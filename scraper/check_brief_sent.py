#!/usr/bin/env python3
"""Answer one question: did today's Daily Brief actually reach the fg2065 inbox?

Added 2026-09-03. The dashboard-watchdog's brief-rescue trigger used to check for a
local marker file (`BobbyWorkspace/_drafts/outlook-pull-<today>.md`). That check is a
permanent false positive: the brief now runs in GitHub Actions, so the marker is written
on the CI runner and `data/daily-brief/` is untracked, meaning nothing ever syncs back to
Bobby's laptop. Every watchdog run therefore read "brief not sent" and would fire a
redundant send on top of the two the workflows already produce.

The only authoritative answer is the mailbox itself. `_graph_send` posts with
`saveToSentItems: False`, so Sent Items is empty by design -- the brief is addressed TO
fg2065, so the INBOX is where it lands and where we must look.

Exit codes:  0 = brief present (do not re-send)   1 = not found (rescue is warranted)
             2 = could not determine (auth/network) -- treat as "do not re-send"

Usage:  python scraper/check_brief_sent.py [--date YYYY-MM-DD] [--quiet]
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"
MAILBOX = "fg2065@estep-co.com"
# Must match the subject built in read_outlook_via_gmail.py:main()
SUBJECT_TEMPLATE = "Daily Brief \u2014 {d}"
SCOPE = ("https://outlook.office.com/Mail.ReadWrite "
         "https://outlook.office.com/Mail.Send offline_access")


def _load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    # Real environment wins, so CI can inject without a .env file.
    for k in ("GRAPH_TENANT_ID", "GRAPH_CLIENT_ID", "GRAPH_REFRESH_TOKEN"):
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


def _save_refresh_token(new_rt: str) -> None:
    """The refresh token rotates on every exchange -- persist it or the next run fails."""
    if not ENV_PATH.exists():
        return
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    out, found = [], False
    for line in lines:
        if line.startswith("GRAPH_REFRESH_TOKEN="):
            out.append(f"GRAPH_REFRESH_TOKEN={new_rt}")
            found = True
        else:
            out.append(line)
    if not found:
        out.append(f"GRAPH_REFRESH_TOKEN={new_rt}")
    ENV_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")


def brief_sent(target: date, quiet: bool = False) -> int:
    env = _load_env()
    missing = [k for k in ("GRAPH_TENANT_ID", "GRAPH_CLIENT_ID", "GRAPH_REFRESH_TOKEN")
               if not env.get(k)]
    if missing:
        if not quiet:
            print(f"INDETERMINATE: missing {', '.join(missing)}")
        return 2

    try:
        resp = requests.post(
            f"https://login.microsoftonline.com/{env['GRAPH_TENANT_ID']}/oauth2/v2.0/token",
            data={
                "grant_type": "refresh_token",
                "client_id": env["GRAPH_CLIENT_ID"],
                "refresh_token": env["GRAPH_REFRESH_TOKEN"],
                "scope": SCOPE,
            }, timeout=30)
    except Exception as exc:
        if not quiet:
            print(f"INDETERMINATE: token request failed: {exc}")
        return 2

    if not resp.ok:
        if not quiet:
            print(f"INDETERMINATE: token exchange {resp.status_code} {resp.text[:200]}")
        return 2

    body = resp.json()
    new_rt = body.get("refresh_token")
    if new_rt and new_rt != env["GRAPH_REFRESH_TOKEN"]:
        _save_refresh_token(new_rt)

    # Window back to the start of the target day (UTC) with a day of slack, so a brief
    # sent just after local midnight is still found.
    since = (datetime.combine(target, datetime.min.time(), tzinfo=timezone.utc)
             - timedelta(hours=12)).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = ("https://outlook.office.com/api/v2.0/me/messages"
           f"?$top=100&$select=Subject,ReceivedDateTime"
           f"&$filter=ReceivedDateTime ge {since}&$orderby=ReceivedDateTime desc")
    try:
        r = requests.get(url, headers={"Authorization": "Bearer " + body["access_token"]},
                         timeout=30)
    except Exception as exc:
        if not quiet:
            print(f"INDETERMINATE: inbox query failed: {exc}")
        return 2

    if not r.ok:
        if not quiet:
            print(f"INDETERMINATE: inbox query {r.status_code} {r.text[:200]}")
        return 2

    wanted = SUBJECT_TEMPLATE.format(d=target.strftime("%Y-%m-%d"))
    hits = [m for m in r.json().get("value", [])
            if (m.get("Subject") or "").strip() == wanted]
    if hits:
        if not quiet:
            times = ", ".join(h["ReceivedDateTime"] for h in hits)
            print(f"SENT: '{wanted}' found in {MAILBOX} inbox "
                  f"({len(hits)} copy/copies at {times})")
        return 0
    if not quiet:
        print(f"NOT SENT: no '{wanted}' in {MAILBOX} inbox -- rescue warranted")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", help="YYYY-MM-DD (default: today, local)")
    ap.add_argument("--quiet", action="store_true", help="Exit code only, no output")
    a = ap.parse_args()
    target = date.fromisoformat(a.date) if a.date else date.today()
    return brief_sent(target, quiet=a.quiet)


if __name__ == "__main__":
    sys.exit(main())
