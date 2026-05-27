#!/usr/bin/env python3
"""
Send the April + May 2026 secret shop printable xlsx to fg2065@estep-co.com.
Uses the delegated refresh-token path (GRAPH_REFRESH_TOKEN in .env).
"""
from __future__ import annotations
import base64
import json
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent

# Auto-load .env
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

TENANT_ID     = os.environ.get("GRAPH_TENANT_ID", "")
CLIENT_ID     = os.environ.get("GRAPH_CLIENT_ID", "")
REFRESH_TOKEN = os.environ.get("GRAPH_REFRESH_TOKEN", "")
FROM_ADDR     = os.environ.get("GRAPH_ACCOUNT_USERNAME", "fg2065@estep-co.com")
TO_ADDR       = "fg2065@estep-co.com"

ATTACH_PATH = ROOT / "data" / "Shop_AprMay_2026_Printable.xlsx"


def get_access_token() -> str:
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        "grant_type":    "refresh_token",
        "client_id":     CLIENT_ID,
        "refresh_token": REFRESH_TOKEN,
        "scope":         "https://graph.microsoft.com/Mail.Send offline_access",
    }
    resp = requests.post(url, data=data, timeout=30)
    if not resp.ok:
        print(f"Token exchange failed: {resp.status_code} {resp.text[:300]}")
        sys.exit(1)
    body = resp.json()
    if "access_token" not in body:
        print(f"No access_token in response: {body}")
        sys.exit(1)
    # Persist updated refresh token if returned
    new_rt = body.get("refresh_token")
    if new_rt and new_rt != REFRESH_TOKEN:
        _update_env_var(env_path, "GRAPH_REFRESH_TOKEN", new_rt)
        print("[send] Refresh token rotated and saved to .env")
    return body["access_token"]


def _update_env_var(env_file: Path, key: str, value: str) -> None:
    lines = env_file.read_text(encoding="utf-8").splitlines()
    updated = []
    found = False
    for line in lines:
        if line.startswith(f"{key}="):
            updated.append(f"{key}={value}")
            found = True
        else:
            updated.append(line)
    if not found:
        updated.append(f"{key}={value}")
    env_file.write_text("\n".join(updated) + "\n", encoding="utf-8")


def send_email(token: str) -> None:
    # Read + base64-encode attachment
    attach_bytes = ATTACH_PATH.read_bytes()
    attach_b64   = base64.b64encode(attach_bytes).decode("ascii")

    payload = {
        "message": {
            "subject": "Secret Shop Tracker — April & May 2026 (Printable)",
            "body": {
                "contentType": "Text",
                "content": "Attached is the April + May 2026 secret shop printable summary for Store 2065 — shop dates, scores, and employee names on shift for each shop."
            },
            "toRecipients": [{"emailAddress": {"address": TO_ADDR}}],
            "attachments": [
                {
                    "@odata.type":  "#microsoft.graph.fileAttachment",
                    "name":         "Shop_AprMay_2026_Printable.xlsx",
                    "contentType":  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "contentBytes": attach_b64,
                }
            ],
        },
        "saveToSentItems": True,
    }

    url = f"https://graph.microsoft.com/v1.0/users/{FROM_ADDR}/sendMail"
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    if resp.status_code == 202:
        print(f"[send] Email sent to {TO_ADDR} — 202 Accepted")
    elif resp.status_code == 401:
        print(f"[send] 401 Unauthorized — token may lack Mail.Send scope. {resp.text[:300]}")
        sys.exit(1)
    else:
        print(f"[send] Unexpected status {resp.status_code}: {resp.text[:400]}")
        sys.exit(1)


def main() -> None:
    if not (TENANT_ID and CLIENT_ID and REFRESH_TOKEN):
        print("GRAPH_TENANT_ID / GRAPH_CLIENT_ID / GRAPH_REFRESH_TOKEN not set")
        sys.exit(1)
    if not ATTACH_PATH.exists():
        print(f"Attachment not found: {ATTACH_PATH}")
        sys.exit(1)
    print(f"[send] Getting access token for {FROM_ADDR}...")
    token = get_access_token()
    print(f"[send] Sending email to {TO_ADDR} with attachment {ATTACH_PATH.name} ({ATTACH_PATH.stat().st_size} bytes)...")
    send_email(token)


if __name__ == "__main__":
    main()
