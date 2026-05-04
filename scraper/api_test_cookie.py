#!/usr/bin/env python3
"""
Cookie-replay sanity check: hit /resource/dashboard/performance/metrics
using ONLY the session cookies captured by api_discover.py.

If this returns 200 + JSON matching the same shape as the live capture,
the cookie-only auth pattern is confirmed and we can build api_*.py
modules to replace Playwright.
"""

import json, sys
from pathlib import Path

import requests

ROOT     = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"

NETCHEF_BASE = "https://fiveguysfr77.net-chef.com"
TARGET_URL   = f"{NETCHEF_BASE}/resource/dashboard/performance/metrics"
TARGET_BODY  = {"allLocations": False, "pagingInfo": {"infinite": False}}

cookies_file = DATA_DIR / "ct_cookies.json"
if not cookies_file.exists():
    print("FATAL: ct_cookies.json not found — run api_discover.py first", file=sys.stderr)
    sys.exit(2)

cookies = json.loads(cookies_file.read_text())
jar = {c["name"]: c["value"] for c in cookies}

print(f"Loaded {len(jar)} cookies — including: {[k for k in jar if 'session' in k.lower() or 'JSESSION' in k]}")
print(f"POST -> {TARGET_URL}")
print(f"Body: {TARGET_BODY}")

# Headers that an XHR fetch typically sends. Keep minimal — see if cookie-only works.
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json;charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": NETCHEF_BASE,
    "Referer": f"{NETCHEF_BASE}/ncext/modern.ct",
}

resp = requests.post(TARGET_URL, json=TARGET_BODY, cookies=jar, headers=headers, timeout=30)
print(f"\n=== STATUS: {resp.status_code} ===")
print(f"=== RESPONSE LENGTH: {len(resp.text)} bytes ===")
print(f"=== RESPONSE CONTENT-TYPE: {resp.headers.get('content-type')} ===")
print(f"\n=== FIRST 800 chars of body ===")
print(resp.text[:800])

if resp.status_code == 200 and "json" in (resp.headers.get("content-type") or "").lower():
    try:
        data = resp.json()
        if isinstance(data, list) and data:
            kpis = [row.get("name") for row in data if row.get("name")]
            print(f"\n=== KPIs returned ({len(kpis)}) ===")
            for k in kpis[:25]:
                print(f"  - {k}")
            print("\nVERDICT: COOKIE-ONLY AUTH WORKS. Pivot is viable.")
            sys.exit(0)
    except Exception as exc:
        print(f"JSON parse failed: {exc}")

print("\nVERDICT: Did NOT return clean JSON. Inspect response.")
sys.exit(1)
