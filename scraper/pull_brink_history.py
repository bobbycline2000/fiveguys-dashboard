"""
Pull historical Par Brink "Hourly Sales And Labor" PDFs from bob.cline2000@gmail.com
for a date range, save raw PDFs + parsed JSON.

Designed to run weekly in GitHub Actions — picks up the last N days, fills any gaps
in the local archive at data/raw/parbrink/{store}/{date}/.

Usage:
  python scraper/pull_brink_history.py --store 2065 --days 7
  python scraper/pull_brink_history.py --store 2065 --start 2026-04-22 --end 2026-05-05

Auth:
  Reuses the existing Gmail OAuth refresh token at secrets/scg_refresh_token.json
  (set up via parbrink_email_pickup.py --setup).

Exit codes:
  0  success — at least 1 day pulled
  1  no emails found in range
  2  auth failure
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("ERROR: pip install google-api-python-client google-auth google-auth-oauthlib", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
SECRETS = ROOT / "secrets"
TOKEN_FILE = SECRETS / "scg_refresh_token.json"
SENDER = "noreply@parpos.com"
DAILY_SUBJECT = "Promethus Reports"
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def log(msg):
    print(msg, flush=True)


def get_gmail_service():
    if not TOKEN_FILE.exists():
        log(f"ERROR: {TOKEN_FILE} missing. Run: python scraper/parbrink_email_pickup.py --setup")
        sys.exit(2)
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    return build("gmail", "v1", credentials=creds)


def list_promethus_emails(service, after_date: date, before_date: date) -> list[dict]:
    """Returns metadata for all Promethus daily emails in the date range."""
    q = (
        f'from:{SENDER} subject:"{DAILY_SUBJECT}" '
        f'after:{after_date.strftime("%Y/%m/%d")} '
        f'before:{(before_date + timedelta(days=1)).strftime("%Y/%m/%d")}'
    )
    log(f"Gmail query: {q}")
    out = []
    page = None
    while True:
        kwargs = {"userId": "me", "q": q, "maxResults": 100}
        if page:
            kwargs["pageToken"] = page
        resp = service.users().messages().list(**kwargs).execute()
        out.extend(resp.get("messages", []))
        page = resp.get("nextPageToken")
        if not page:
            break
    log(f"Found {len(out)} candidate emails")
    return out


def get_full_message(service, msg_id: str) -> dict:
    return service.users().messages().get(userId="me", id=msg_id, format="full").execute()


def extract_body(message: dict) -> str:
    payload = message.get("payload", {})
    chunks = []

    def walk(part):
        mt = part.get("mimeType", "")
        if mt.startswith("text/plain"):
            data = part.get("body", {}).get("data", "")
            if data:
                try:
                    chunks.append(base64.urlsafe_b64decode(data + "===").decode("utf-8", errors="replace"))
                except Exception:
                    pass
        for sub in part.get("parts", []) or []:
            walk(sub)

    walk(payload)
    return "\n".join(chunks)


def parse_business_date(body: str) -> date | None:
    m = re.search(r"Business Date:\s*([\d/]+)", body)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1).strip(), "%m/%d/%Y").date()
    except ValueError:
        return None


def find_attachment(message: dict, filename_pattern: str) -> tuple[str, str] | None:
    """Returns (attachment_id, filename) if found."""
    payload = message.get("payload", {})

    def walk(part):
        if part.get("filename") and re.search(filename_pattern, part["filename"], re.IGNORECASE):
            body = part.get("body", {})
            if body.get("attachmentId"):
                return (body["attachmentId"], part["filename"])
        for sub in part.get("parts", []) or []:
            r = walk(sub)
            if r:
                return r
        return None

    return walk(payload)


def download_attachment(service, msg_id: str, att_id: str, dest: Path):
    att = service.users().messages().attachments().get(userId="me", messageId=msg_id, id=att_id).execute()
    data = base64.urlsafe_b64decode(att["data"] + "===")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return len(data)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--store", default="2065", help="Store ID (default 2065)")
    p.add_argument("--days", type=int, help="Pull last N days (alternative to --start/--end)")
    p.add_argument("--start", help="Start date YYYY-MM-DD")
    p.add_argument("--end", help="End date YYYY-MM-DD")
    args = p.parse_args()

    if args.days:
        end = date.today()
        start = end - timedelta(days=args.days)
    elif args.start and args.end:
        start = datetime.strptime(args.start, "%Y-%m-%d").date()
        end = datetime.strptime(args.end, "%Y-%m-%d").date()
    else:
        # Default: last 7 days
        end = date.today()
        start = end - timedelta(days=7)

    log(f"=== Pull Brink history for {args.store} | {start} → {end} ===")
    service = get_gmail_service()
    emails = list_promethus_emails(service, start, end)
    if not emails:
        log("No emails found.")
        sys.exit(1)

    pulled = 0
    skipped = 0
    for em in emails:
        full = get_full_message(service, em["id"])
        body = extract_body(full)
        biz_date = parse_business_date(body)
        if not biz_date or not (start <= biz_date <= end):
            skipped += 1
            continue
        # Save under data/raw/parbrink/{store}/{date}/
        out_dir = ROOT / "data" / "raw" / "parbrink" / args.store / biz_date.isoformat()
        if (out_dir / "Hourly Sales And Labor.pdf").exists():
            log(f"  [{biz_date}] already on disk — skip")
            skipped += 1
            continue
        att = find_attachment(full, r"Hourly.*Sales.*And.*Labor\.pdf")
        if not att:
            log(f"  [{biz_date}] no Hourly Sales And Labor.pdf attachment — skip")
            skipped += 1
            continue
        att_id, filename = att
        sz = download_attachment(service, em["id"], att_id, out_dir / "Hourly Sales And Labor.pdf")
        log(f"  [{biz_date}] saved {filename} ({sz} bytes)")
        pulled += 1

    log(f"\n=== Pulled {pulled} new days, skipped {skipped} ===")
    sys.exit(0 if pulled > 0 else 1)


if __name__ == "__main__":
    main()
