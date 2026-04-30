#!/usr/bin/env python3
"""
COGS Flash Report email reader.

CrunchTime emails a daily "COGS Review Week Ending [date]" report to
fg2065@estep-co.com from noreply@net-chef.com. This script reads the
most recent email via Microsoft Graph API and writes cogs_variance.json.

Reads (from env or GitHub Secrets):
    MS_TENANT_ID, MS_CLIENT_ID, MS_CLIENT_SECRET
    COGS_MAILBOX  (default: fg2065@estep-co.com)
    STORE_ID      (default: 2065)

Writes:
    data/raw/crunchtime/<STORE_ID>/<week_end>/cogs_variance.json
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")

TENANT_ID  = os.environ["MS_TENANT_ID"]
CLIENT_ID  = os.environ["MS_CLIENT_ID"]
CLIENT_SECRET = os.environ["MS_CLIENT_SECRET"]
MAILBOX    = os.environ.get("COGS_MAILBOX", "fg2065@estep-co.com")
STORE_ID   = os.environ.get("STORE_ID", "2065")
COGS_GOAL  = 27.5

ROOT     = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def get_token() -> str:
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    resp = requests.post(url, data={
        "grant_type":    "client_credentials",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope":         "https://graph.microsoft.com/.default",
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()["access_token"]


def search_cogs_emails(token: str) -> list:
    """Return up to 3 most recent COGS Flash Report emails."""
    url = (
        f"https://graph.microsoft.com/v1.0/users/{MAILBOX}/messages"
        f"?$search=\"COGS Review Week Ending\""
        f"&$top=3"
        f"&$select=subject,receivedDateTime,body,from"
    )
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}",
                                      "Prefer": 'outlook.body-content-type="text"'},
                        timeout=30)
    if resp.status_code == 403:
        print("ERROR: Graph API returned 403 — app may need Mail.Read application permission.")
        print("  Ask your Azure AD admin to grant 'Mail.Read' (Application) to the app registration.")
        sys.exit(1)
    resp.raise_for_status()
    return resp.json().get("value", [])


def parse_fp_pct(body: str) -> float | None:
    """
    Parse FP% from the COGS Flash Report table body.

    Table format (pipe-delimited):
      | May 3, 2026      | COGS Flash Report |
      |            | CGS |   CP%   |   FP%   |
      | KY-2065-Di |     |         |    23.4 |
      | Total      |     |         |    23.4 |

    Strategy: find the KY-2065 or Total row, take the last non-empty
    numeric column value.
    """
    for line in body.splitlines():
        if "KY-2065" in line or "Total" in line:
            cols = [c.strip() for c in line.split("|")]
            # Last non-empty column that looks like a number
            for col in reversed(cols):
                try:
                    val = float(col)
                    if 5.0 <= val <= 60.0:
                        return val
                except ValueError:
                    continue
    return None


def parse_week_end(subject: str) -> str | None:
    """Extract 'May 3, 2026' from 'COGS Review Week Ending [May 3, 2026]'."""
    m = re.search(r"\[([^\]]+)\]", subject)
    if not m:
        return None
    try:
        dt = datetime.strptime(m.group(1).strip(), "%B %d, %Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None


def week_start_from_end(week_end_str: str) -> str:
    """CrunchTime weeks run Mon–Sun."""
    end = datetime.strptime(week_end_str, "%Y-%m-%d").date()
    start = end - timedelta(days=6)
    return start.strftime("%Y-%m-%d")


def load_existing_items(store_id: str) -> list:
    """Load top-variance items from the most recent cogs_variance.json (for display)."""
    base = DATA_DIR / "raw" / "crunchtime" / store_id
    if not base.exists():
        return []
    for d in sorted([x for x in base.iterdir() if x.is_dir()], reverse=True):
        cand = d / "cogs_variance.json"
        if cand.exists():
            try:
                data = json.loads(cand.read_text(encoding="utf-8"))
                if data.get("items"):
                    return data["items"]
            except Exception:
                continue
    return []


def main():
    print(f"Reading COGS email for {MAILBOX}...")
    token = get_token()
    emails = search_cogs_emails(token)

    if not emails:
        print("No COGS Review emails found — skipping.")
        sys.exit(0)

    # Use the most recent email
    msg = emails[0]
    subject = msg.get("subject", "")
    body    = msg.get("body", {}).get("content", "") or msg.get("bodyPreview", "")
    received = msg.get("receivedDateTime", "")

    fp_pct = parse_fp_pct(body)
    if fp_pct is None:
        print(f"Could not parse FP% from email: {subject!r}")
        print("Body preview:", body[:200])
        sys.exit(1)

    week_end   = parse_week_end(subject)
    week_start = week_start_from_end(week_end) if week_end else None

    # Use today as the file date (data is current as of today)
    today_str = datetime.now(tz=timezone(timedelta(hours=-4))).strftime("%Y-%m-%d")
    file_date = today_str

    vtg = round(fp_pct - COGS_GOAL, 1)
    existing_items = load_existing_items(STORE_ID)

    out = {
        "meta": {
            "source": f"CrunchTime COGS Flash Report email → {MAILBOX}",
            "category": "Food",
            "store": STORE_ID,
            "week_start": week_start,
            "week_end":   week_end,
            "email_subject":  subject,
            "email_received": received,
            "pulled": datetime.now(tz=timezone(timedelta(hours=-4))).strftime("%Y-%m-%d %H:%M ET"),
            "method": "email_parse",
        },
        "cogs_goal_pct":           COGS_GOAL,
        "cogs_pct_week":           fp_pct,
        "cogs_pct_month":          None,
        "cogs_pct_last_month":     None,
        "variance_to_goal_week":   vtg,
        "variance_to_goal_month":  None,
        "variance_to_goal_last_mo": None,
        "items":   existing_items,
        "ranking": "over_dollars_desc",
    }

    raw_dir = DATA_DIR / "raw" / "crunchtime" / STORE_ID / file_date
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_path = raw_dir / "cogs_variance.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"FP% = {fp_pct}%  (vs goal {COGS_GOAL}% → {vtg:+.1f}%)")
    print(f"Week: {week_start} → {week_end}")


if __name__ == "__main__":
    main()
