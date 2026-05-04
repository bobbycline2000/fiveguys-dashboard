#!/usr/bin/env python3
"""
Probe what Application permissions are consented on the Azure app
registration that the dashboard uses (MS_CLIENT_ID).

Decodes the JWT access token from the client-credentials flow and
prints the `roles` claim — that is the authoritative list of granted
Application permissions on this tenant.

Usage (locally or in GitHub Actions):
    MS_TENANT_ID=... MS_CLIENT_ID=... MS_CLIENT_SECRET=... \
        python scripts/probe_graph_scopes.py
"""

import base64
import json
import os
import sys

import requests

TENANT_ID     = os.environ["MS_TENANT_ID"]
CLIENT_ID     = os.environ["MS_CLIENT_ID"]
CLIENT_SECRET = os.environ["MS_CLIENT_SECRET"]

# Roles we care about for the email automation roadmap.
WANT = [
    "Mail.Read",
    "Mail.ReadWrite",
    "Mail.Send",
    "Calendars.Read",
    "Calendars.ReadWrite",
    "Files.Read.All",
    "Files.ReadWrite.All",
    "Sites.Read.All",
    "Sites.ReadWrite.All",
    "User.Read.All",
]


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


def decode_jwt_payload(token: str) -> dict:
    # JWT = header.payload.signature, all base64url
    payload = token.split(".")[1]
    # pad to multiple of 4
    payload += "=" * ((4 - len(payload) % 4) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))


def main() -> int:
    tok = get_token()
    claims = decode_jwt_payload(tok)
    roles = sorted(claims.get("roles", []))

    print(f"Tenant : {claims.get('tid')}")
    print(f"App ID : {claims.get('appid')}")
    print(f"App    : {claims.get('app_displayname', '?')}")
    print()
    print(f"Granted Application roles ({len(roles)}):")
    for r in roles:
        print(f"  - {r}")

    print()
    print("Roadmap check:")
    for w in WANT:
        mark = "GRANTED" if w in roles else "MISSING"
        print(f"  {mark:8}  {w}")

    print()
    missing_critical = [w for w in ("Mail.ReadWrite", "Mail.Send") if w not in roles]
    if missing_critical:
        print(f"Next step: ask Azure admin to add + grant admin consent for:")
        for w in missing_critical:
            print(f"  - {w} (Application)")
        consent_url = (
            f"https://login.microsoftonline.com/{TENANT_ID}/adminconsent"
            f"?client_id={CLIENT_ID}"
        )
        print(f"\nAdmin-consent URL: {consent_url}")
        return 2
    print("All critical roles for drafts + send are present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
