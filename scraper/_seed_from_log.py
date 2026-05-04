#!/usr/bin/env python3
"""
Seed ct_endpoints_by_screen.json from the killed first-run log so
api_discover_one.py can build incrementally without re-discovering.
Only fills in screen names; the captured/payloads dict is empty here
(those payloads were never persisted from the killed run, but we'll
re-fetch on the next pass through any screen).
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
LOG  = ROOT / "data" / "_deep_discovery_log.txt"
EPS  = ROOT / "data" / "ct_api_endpoints_deep.json"
SCRN = ROOT / "data" / "ct_endpoints_by_screen.json"

if not LOG.exists():
    print(f"missing log: {LOG}", file=sys.stderr); sys.exit(2)

text = LOG.read_text(encoding="utf-8", errors="replace")
sections = re.split(r"=== (\w+) ===", text)
# pattern: ['intro', 'screen1', 'body1', 'screen2', 'body2', ...]
by_screen = {}
for i in range(1, len(sections), 2):
    screen = sections[i]
    body = sections[i+1]
    paths = re.findall(r"\[(GET|POST)\]\s+\d+\s+\(\s*\d+b\)\s+--\s+(\S+)", body)
    urls = []
    for method, path in paths:
        url = "https://fiveguysfr77.net-chef.com" + path
        if url not in urls:
            urls.append(url)
    if urls:
        by_screen[screen] = urls

SCRN.write_text(json.dumps(by_screen, indent=2))
print(f"seeded {sum(len(v) for v in by_screen.values())} endpoint references across {len(by_screen)} screens")
for s, u in by_screen.items():
    print(f"  {s}: {len(u)}")
