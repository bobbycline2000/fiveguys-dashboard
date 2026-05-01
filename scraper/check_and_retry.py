"""
9 AM Dashboard Retry Agent.

Runs after the 4 AM pipeline. Checks whether Par Brink data for today (or
yesterday's business date) is wired into the live dashboard. If stale, it
re-runs the full pipeline and checks again. Retries up to MAX_RETRIES times
with RETRY_WAIT_SECONDS between each attempt.

On final failure, writes a clear entry to data/debug-log.txt.

Windows Task: FiveGuys-DashboardCheck — runs daily at 9:00 AM.

Usage:
  python scraper/check_and_retry.py [--store 2065] [--max-retries 3]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRAPER = ROOT / "scraper"
DBG = ROOT / "data" / "debug-log.txt"

MAX_RETRIES = 3
RETRY_WAIT_SECONDS = 300  # 5 minutes between retries


def log_debug(store: str, msg: str) -> None:
    """Append a timestamped entry to debug-log.txt."""
    from datetime import datetime
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n[{ts}] check_and_retry store={store}\n  - {msg}\n"
    DBG.parent.mkdir(parents=True, exist_ok=True)
    with open(DBG, "a", encoding="utf-8") as f:
        f.write(entry)
    print(f"[check-and-retry] {msg}")


def latest_parbrink_date(store: str) -> date | None:
    """Return the report_date from the most recent Par Brink sales_summary.json."""
    base = ROOT / "data" / "raw" / "parbrink" / store
    if not base.exists():
        return None
    for folder in sorted(base.iterdir(), reverse=True):
        if not folder.is_dir():
            continue
        jp = folder / "sales_summary.json"
        if not jp.exists():
            continue
        try:
            data = json.loads(jp.read_text(encoding="utf-8"))
            rd = data.get("meta", {}).get("report_date")
            if rd:
                return date.fromisoformat(rd)
        except Exception:
            continue
    return None


def dashboard_is_fresh(store: str) -> tuple[bool, str]:
    """
    Return (is_fresh, reason).
    Fresh = Par Brink sales_summary report_date is today or yesterday,
    AND that net_sales value appears in dashboard.html.
    """
    pb_date = latest_parbrink_date(store)
    today = date.today()
    yesterday = today - timedelta(days=1)

    if pb_date is None:
        return False, "No Par Brink sales_summary.json found at all"

    if pb_date < yesterday:
        return False, f"Par Brink data is from {pb_date} — expected {yesterday} or {today}"

    # Check net_sales value appears in the HTML
    jp = ROOT / "data" / "raw" / "parbrink" / store
    # Find the matching folder
    net_sales = None
    for folder in sorted(jp.iterdir(), reverse=True):
        if not folder.is_dir():
            continue
        cand = folder / "sales_summary.json"
        if not cand.exists():
            continue
        try:
            data = json.loads(cand.read_text(encoding="utf-8"))
            if data.get("meta", {}).get("report_date") == pb_date.isoformat():
                net_sales = data.get("net_sales")
                break
        except Exception:
            continue

    if net_sales is None:
        return False, f"Could not read net_sales from {pb_date} sales_summary.json"

    dash = ROOT / "dashboard.html"
    if not dash.exists():
        return False, "dashboard.html does not exist"

    # Format as the wire script would: $X,XXX
    formatted = f"${net_sales:,.0f}"
    if formatted not in dash.read_text(encoding="utf-8"):
        return False, f"Net sales {formatted} (Par Brink {pb_date}) not found in dashboard.html"

    return True, f"Fresh — Par Brink {pb_date}, {formatted} wired into dashboard"


def run_pipeline(store: str) -> int:
    print("[check-and-retry] Running full pipeline...")
    result = subprocess.run(
        [sys.executable, str(SCRAPER / "run_daily_pipeline.py"), "--store", store],
        cwd=ROOT,
    )
    return result.returncode


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="2065")
    ap.add_argument("--max-retries", type=int, default=MAX_RETRIES)
    args = ap.parse_args()

    store = args.store
    max_retries = args.max_retries

    print(f"[check-and-retry] Starting freshness check for store {store}")

    fresh, reason = dashboard_is_fresh(store)
    if fresh:
        print(f"[check-and-retry] Dashboard is fresh. {reason}")
        return 0

    print(f"[check-and-retry] Dashboard is STALE: {reason}")

    for attempt in range(1, max_retries + 1):
        print(f"\n[check-and-retry] Attempt {attempt}/{max_retries} — running pipeline...")
        rc = run_pipeline(store)

        fresh, reason = dashboard_is_fresh(store)
        if fresh:
            print(f"[check-and-retry] SUCCESS on attempt {attempt}. {reason}")
            return 0

        print(f"[check-and-retry] Still stale after attempt {attempt}: {reason}")

        if attempt < max_retries:
            wait_min = RETRY_WAIT_SECONDS // 60
            print(f"[check-and-retry] Waiting {wait_min} minutes before retry...")
            time.sleep(RETRY_WAIT_SECONDS)

    # All retries exhausted
    msg = f"FAILED after {max_retries} attempts. Last check: {reason}"
    log_debug(store, msg)
    print(f"\n[check-and-retry] {msg}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
