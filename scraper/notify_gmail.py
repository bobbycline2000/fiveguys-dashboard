#!/usr/bin/env python3
"""
Lightweight CI email notifier via the SCG Gmail account.

Exists because Microsoft Graph sendmail is blocked in CI (MS_TENANT_ID /
MS_CLIENT_ID / MS_CLIENT_SECRET need an Azure app registration Bobby can't
create — not tenant admin; the delegated SPA refresh token hard-expires in
24h). The SCG Gmail OAuth token (secrets/scg_refresh_token.json) already
works in CI daily for Par Brink pickup AND carries gmail.send scope — so
alerts ride that instead.

Usage:
    python scraper/notify_gmail.py --to fg2065@estep-co.com \
        --subject "[FAIL] something" --html "<p>body</p>"
    # or read body from a file:
    python scraper/notify_gmail.py --to ... --subject ... --html-file body.html

Auth: same secrets/ files the daily workflow restores from GitHub Secrets
(SCG_OAUTH_CLIENT_JSON + SCG_GMAIL_REFRESH_TOKEN_JSON).

Exit codes: 0 sent, 1 auth failure, 2 send failure.
"""
from __future__ import annotations

import argparse
import base64
import sys
from email.mime.text import MIMEText
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

ROOT = Path(__file__).resolve().parents[1]
TOKEN_FILE = ROOT / "secrets" / "scg_refresh_token.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def send(to: str, subject: str, html: str) -> None:
    if not TOKEN_FILE.exists():
        print(f"[notify] token file missing: {TOKEN_FILE}", file=sys.stderr)
        raise SystemExit(1)
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    svc = build("gmail", "v1", credentials=creds, cache_discovery=False)
    msg = MIMEText(html, "html")
    msg["to"] = to
    msg["subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    try:
        svc.users().messages().send(userId="me", body={"raw": raw}).execute()
        print(f"[notify] sent to {to}: {subject}")
    except HttpError as e:
        print(f"[notify] send failed: {e}", file=sys.stderr)
        raise SystemExit(2)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--to", required=True)
    p.add_argument("--subject", required=True)
    p.add_argument("--html", default=None)
    p.add_argument("--html-file", default=None)
    a = p.parse_args()
    html = a.html if a.html is not None else Path(a.html_file).read_text(encoding="utf-8")
    send(a.to, a.subject, html)


if __name__ == "__main__":
    main()
