"""
Refresh the secret shop tracker end-to-end.

Pulls fresh shops from KnowledgeForce, recomputes per-employee performance,
rebuilds the tracker xlsx, re-wires the dashboard, and stages the changes.
The caller (daily brief skill or weekly cron) handles git commit + push.

Usage:
    python scripts/refresh_shop_tracker.py
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

STEPS = [
    ("Pull shops from KnowledgeForce", ["python", "scraper/scrape_knowledgeforce_api.py"]),
    ("Build shop performance averages", ["python", "scraper/build_shop_performance.py"]),
    ("Rebuild shop tracker xlsx",       ["python", "scraper/build_shop_tracker.py"]),
    ("Wire dashboard",                   ["python", "scraper/wire_dashboard.py"]),
]


def main():
    print(f"=== Shop tracker refresh — {REPO} ===\n")
    for label, cmd in STEPS:
        print(f"--- {label} ---")
        result = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout.strip())
        if result.returncode != 0:
            print(f"FAILED: {label}", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            sys.exit(1)
        print()
    print("=== All steps OK. Caller should git add/commit/push. ===")


if __name__ == "__main__":
    main()
