#!/usr/bin/env python3
"""
Five Guys University (Schoox) refresh-token exchange — the lights-out
alternative to a live Chrome capture (Schoox login is Google-SSO/MFA gated,
so a scripted login is not possible; see scraper/FGU_API.md).

POST /api/v2/auth/token/refresh with {"token": "<refresh_token>"} returns a
fresh accessToken AND a ROTATED refreshToken (the old one is consumed —
single use). This script:
  1. Reads the refresh token from FGU_REFRESH_TOKEN env (GitHub Secret).
  2. Exchanges it for a fresh access token.
  3. Writes data/fgu_session.json = {"token": "<accessToken>"} for
     scrape_fgu.py to consume immediately.
  4. Writes secrets/fgu_refresh_token.txt = "<rotated refreshToken>" (raw,
     no trailing newline) — the workflow's self-heal step pushes this file's
     contents back to the FGU_REFRESH_TOKEN GitHub Secret so tomorrow's run
     has a valid token. secrets/ is gitignored — never committed.

If the refresh token is dead (expired/already rotated elsewhere), this exits
non-zero with a clear message. That is NOT a bug to patch around — it means
a human must re-capture a fresh token+refresh_token pair from a logged-in
Schoox Chrome tab and re-seed the FGU_REFRESH_TOKEN secret
(`gh secret set FGU_REFRESH_TOKEN`). Per patch-spiral-prevention: two dead
refresh-token exchanges in a row means stop and get a human to re-auth, not
keep retrying.

Usage: FGU_REFRESH_TOKEN=<refresh jwt> python scraper/fgu_refresh_token.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
SESSION_FILE = ROOT / "data" / "fgu_session.json"
ROTATED_FILE = ROOT / "secrets" / "fgu_refresh_token.txt"
REFRESH_URL = "https://app.schoox.com/api/v2/auth/token/refresh"


def main() -> None:
    rt = os.environ.get("FGU_REFRESH_TOKEN", "").strip()
    if not rt:
        print("[fgu-refresh] FGU_REFRESH_TOKEN not set", file=sys.stderr)
        sys.exit(1)

    resp = requests.post(
        REFRESH_URL,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        json={"token": rt},
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"[fgu-refresh] refresh FAILED — status {resp.status_code}. "
              f"Token is dead (expired or already rotated elsewhere). "
              f"A human must re-capture from a logged-in Schoox Chrome tab "
              f"and `gh secret set FGU_REFRESH_TOKEN`.", file=sys.stderr)
        sys.exit(2)

    body = resp.json()
    access_token = body.get("accessToken")
    rotated_refresh = body.get("refreshToken")
    if not access_token or not rotated_refresh:
        print("[fgu-refresh] refresh response missing accessToken/refreshToken", file=sys.stderr)
        sys.exit(3)

    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_text(json.dumps({"token": access_token}), encoding="utf-8")

    ROTATED_FILE.parent.mkdir(parents=True, exist_ok=True)
    ROTATED_FILE.write_text(rotated_refresh, encoding="utf-8")

    expires_in = body.get("expiresIn")
    print(f"[fgu-refresh] OK — fresh access token written to {SESSION_FILE} "
          f"(expires_in={expires_in}s). Rotated refresh token staged at {ROTATED_FILE}.")


if __name__ == "__main__":
    main()
