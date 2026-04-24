"""
Backup safety-net for the dashboard pipeline.

Runs AFTER wire_dashboard.py. Cross-checks that dashboard.html actually contains
the fresh values from data/latest.json. If the dashboard is stale (e.g., wire
silently failed, or a class name changed, or the scrape landed data but the HTML
didn't update), this script:

  1. Writes a human-readable diagnosis to data/debug-log.txt
     (Bobby's SESSION START PROTOCOL reads this and auto-fixes at next session).
  2. Creates a GitHub issue if `gh` is available (for CI visibility).
  3. Exits with non-zero status so the GitHub Action step fails loudly.

Usage:
    python scraper/verify_dashboard.py
Exit codes:
    0 — dashboard reflects latest.json
    1 — dashboard is stale / checks failed
"""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "dashboard.html"
LATEST = ROOT / "data" / "latest.json"
DEBUG_LOG = ROOT / "data" / "debug-log.txt"

def write_debug(messages):
    DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with DEBUG_LOG.open("a", encoding="utf-8") as f:
        f.write(f"\n[{stamp}] Dashboard freshness check FAILED\n")
        for m in messages:
            f.write(f"  - {m}\n")
        f.write("  Fix: run `python scraper/wire_dashboard.py` locally and inspect MISS list.\n")
        f.write("  If fields are missing, a class name or label may have changed in dashboard.html.\n")

def try_open_github_issue(title, body):
    """Create a GH issue via gh CLI if available. No-op if gh isn't installed."""
    if not os.environ.get("GITHUB_ACTIONS"):
        return
    try:
        subprocess.run(
            ["gh", "issue", "create", "--title", title, "--body", body, "--label", "dashboard-stale"],
            check=False, capture_output=True, text=True, timeout=20,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

def main():
    if not DASH.exists():
        print("FAIL: dashboard.html missing")
        return 1
    if not LATEST.exists():
        print("FAIL: data/latest.json missing — scrape never ran")
        return 1

    data = json.loads(LATEST.read_text(encoding="utf-8"))
    html = DASH.read_text(encoding="utf-8")

    failures = []

    # Check 1: the scraped sales.net value appears in the dashboard
    sales_net = data.get("sales", {}).get("net")
    if sales_net is not None:
        needle = f"${sales_net:,.0f}"
        if needle not in html:
            failures.append(
                f"sales.net={needle} from latest.json NOT found in dashboard.html — "
                f"the Daily Sales KPI is stale or wire_dashboard.py failed to update it."
            )

    # Check 2: the scraped sales.per_guest appears
    per_guest = data.get("sales", {}).get("per_guest")
    if per_guest is not None:
        needle = f"${per_guest:.2f}"
        if needle not in html:
            failures.append(
                f"sales.per_guest={needle} from latest.json NOT found in dashboard.html."
            )

    # Check 3: the report_date's day name is in the date-chip
    report_date = data.get("meta", {}).get("report_date")
    if report_date:
        try:
            rpt_dt = datetime.strptime(report_date, "%Y-%m-%d")
            day_name = rpt_dt.strftime("%A")
            month_day = rpt_dt.strftime("%B %d").replace(" 0", " ")
            chip_start = html.find('class="date-chip"')
            if chip_start >= 0:
                chip_end = html.find('</div>', chip_start)
                chip_html = html[chip_start:chip_end]
                if day_name not in chip_html or month_day.split()[-1] not in chip_html:
                    failures.append(
                        f"date-chip header does not match report_date={report_date} "
                        f"(expected '{day_name}, {month_day}'). chip snippet: {chip_html!r}"
                    )
            else:
                failures.append("date-chip element not found in dashboard.html")
        except ValueError:
            failures.append(f"meta.report_date malformed: {report_date!r}")

    # Check 4: dashboard.html was modified today (local timezone)
    mtime = datetime.fromtimestamp(DASH.stat().st_mtime)
    now = datetime.now()
    if mtime.date() != now.date():
        failures.append(
            f"dashboard.html mtime is {mtime.isoformat()} — not today. "
            f"The HTML was not regenerated on this run."
        )

    if failures:
        print("DASHBOARD STALE — " + str(len(failures)) + " check(s) failed:\n")
        for f in failures:
            print("  ✗ " + f)

        write_debug(failures)

        title = f"Dashboard stale — {now.strftime('%Y-%m-%d')}"
        body = (
            "Automated freshness check failed. Detail:\n\n"
            + "\n".join(f"- {f}" for f in failures)
            + "\n\nDiagnosis written to `data/debug-log.txt`. "
            + "Next Claude Code session will auto-pick-up via SESSION START PROTOCOL."
        )
        try_open_github_issue(title, body)

        return 1

    print(f"OK — dashboard reflects latest.json (sales.net=${sales_net:,.0f}, report_date={report_date})")
    return 0

if __name__ == "__main__":
    sys.exit(main())
