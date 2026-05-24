#!/usr/bin/env python3
"""
District discovery: enumerate every CrunchTime location Bobby's login can see.

GET /resource/ceslogin/locations returns {locationName, locationId, locationCode}
for all stores in scope. locationId is the INTERNAL id (KY-2065 = 13969), NOT the
store number — that's the value the per-store config files need.

Tries saved cookies first (data/ct_cookies.json). If the session is dead, prints
a clear re-mint instruction. Writes the result to data/ct_locations.json.
"""

import json, sys
from pathlib import Path
import requests

ROOT     = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
NETCHEF_BASE = "https://fiveguysfr77.net-chef.com"
LOCATIONS_URL = f"{NETCHEF_BASE}/resource/ceslogin/locations?page=1&start=0&limit=100"
PROBE_URL     = f"{NETCHEF_BASE}/resource/recommended-actions/status"

cookies_file = DATA_DIR / "ct_cookies.json"
if not cookies_file.exists():
    print("FATAL: ct_cookies.json not found", file=sys.stderr)
    sys.exit(2)

jar = {c["name"]: c["value"] for c in json.loads(cookies_file.read_text())}
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json;charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": NETCHEF_BASE,
    "Referer": f"{NETCHEF_BASE}/ncext/modern.ct",
}

# session-alive probe
probe = requests.get(PROBE_URL, cookies=jar, headers=headers, timeout=20, allow_redirects=False)
print(f"probe {PROBE_URL} -> {probe.status_code}")
if probe.status_code != 200:
    print("\nSESSION DEAD (saved cookies expired). Re-mint required:")
    print("  Bobby logs into https://fiveguysfr77.net-chef.com in Chrome, then")
    print("  we capture fresh cookies and re-run this script.")
    sys.exit(3)

resp = requests.get(LOCATIONS_URL, cookies=jar, headers=headers, timeout=30)
print(f"GET {LOCATIONS_URL} -> {resp.status_code} ({len(resp.text)} bytes)")
if resp.status_code != 200:
    print(resp.text[:600]); sys.exit(1)

data = resp.json()
locs = (data.get("contentMap") or {}).get("locations") or data.get("locations") or []
print(f"\n=== {len(locs)} locations visible to this login ===")
for L in locs:
    print(f"  code={L.get('locationCode'):<8} id={L.get('locationId'):<8} {L.get('locationName')}")

out = DATA_DIR / "ct_locations.json"
out.write_text(json.dumps(locs, indent=2))
print(f"\nwrote {out}")
