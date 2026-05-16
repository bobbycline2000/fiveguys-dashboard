#!/usr/bin/env python3
"""
Auto-bump the VERSION constant in sw.js based on a content hash of the
HTML shell files. When any shell file changes, VERSION changes, the service
worker installs as a new version, the old cache is evicted, and every
device pulls fresh on next visit.

Exit code:
  0 — sw.js up-to-date (or successfully rewritten)
  Non-zero only on hard error (missing files, etc.)

Prints a single line to stdout indicating action taken so CI can decide
whether to commit.
"""
import hashlib
import re
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SW = REPO / "sw.js"

# Files that, when changed, should bust the cache. Keep aligned with
# the SHELL array inside sw.js.
SHELL_FILES = [
    "dashboard.html",
    "safe_drawer.html",
    "bread.html",
    "synopsis.html",
    "portfolio.html",
    "manifest.json",
]


def shell_hash() -> str:
    h = hashlib.sha256()
    for name in SHELL_FILES:
        p = REPO / name
        if not p.exists():
            continue
        h.update(name.encode())
        h.update(b"\0")
        h.update(p.read_bytes())
        h.update(b"\0")
    return h.hexdigest()[:10]


def main() -> int:
    if not SW.exists():
        print(f"FAIL sw.js not found at {SW}")
        return 1

    sw_text = SW.read_text(encoding="utf-8")
    m = re.search(r"const VERSION = '([^']+)';", sw_text)
    if not m:
        print("FAIL could not find VERSION constant in sw.js")
        return 1

    current = m.group(1)
    today = date.today().isoformat()
    new_version = f"fg-2065-ops-{shell_hash()}-{today}"

    if current == new_version:
        print(f"NOOP sw.js VERSION already {current}")
        return 0

    new_text = sw_text.replace(
        f"const VERSION = '{current}';",
        f"const VERSION = '{new_version}';",
        1,
    )
    SW.write_text(new_text, encoding="utf-8")
    print(f"BUMP {current} -> {new_version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
