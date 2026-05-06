"""
Bulk pull historical 'Hourly Sales And Labor' reports from admin5.parpos.com
using Playwright with shared Chrome cookies.

For each (store, date) pair: set DateRangeModel.Date, click View Report,
wait for iframe to render, extract hourly text, save parsed JSON to
data/raw/parbrink/{store}/{date}/hourly_sales_labor.json.

Usage:
  # Pull last 8 weeks of Tue-Sun (default for the rolling-curve product):
  python scraper/bulk_pull_brink_history.py --store 2065 --weeks 8 --tue-sun

  # Pull every day in a date range:
  python scraper/bulk_pull_brink_history.py --store 2065 --start 2026-03-11 --end 2026-05-05

  # Mondays only (when Bobby already downloaded these manually):
  python scraper/bulk_pull_brink_history.py --store 2065 --weeks 8 --mondays-only

The script uses Playwright's persistent context pointed at your default
Chrome user data dir, so it inherits your existing logged-in session.
You must close Chrome before running this script (Chrome locks the profile).

Alternative if Chrome lock causes issues: use --fresh to start a clean
Playwright profile, then log in once interactively. Cookies persist for
future runs in scraper/.brink_profile/.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Use LOCALAPPDATA (Windows) so OneDrive doesn't try to sync browser cache files
import os as _os
_localappdata = _os.environ.get("LOCALAPPDATA") or str(Path.home() / ".cache")
PROFILE_DIR = Path(_localappdata) / "scg-brink-profile"

REPORT_URL = "https://admin5.parpos.com/Reports/Report/HourlySalesAndLabor/"

ROW_RE = re.compile(
    r"(\d{1,2}:\d{2}\s*[AP]M)\s+\$?([\d,]+\.\d{2})\s+(\d+)\s+\$?[\d,]+\.\d{2}\s+(\d+)\s+\$?[\d,]+\.\d{2}\s+([\d,]+\.\d{2})\s+\$?([\d,]+\.\d{2})\s+([\d,]+\.\d{2})%"
)


def parse_iframe_text(text: str) -> list[dict]:
    rows = []
    for m in ROW_RE.finditer(text):
        hour = m.group(1).strip()
        rows.append({
            "hour": hour,
            "netSales": float(m.group(2).replace(",", "")),
            "guests": int(m.group(3)),
            "orders": int(m.group(4)),
            "laborHrs": float(m.group(5).replace(",", "")),
            "laborDollars": float(m.group(6).replace(",", "")),
            "laborPct": float(m.group(7).replace(",", "")),
        })
    return rows


def daterange(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--store", default="2065")
    p.add_argument("--weeks", type=int, default=8)
    p.add_argument("--start", help="YYYY-MM-DD")
    p.add_argument("--end", help="YYYY-MM-DD")
    p.add_argument("--tue-sun", action="store_true", help="Pull only Tue-Sun (Bobby already has Mondays)")
    p.add_argument("--mondays-only", action="store_true")
    p.add_argument("--fresh", action="store_true", help="Use fresh profile; you'll log in once")
    args = p.parse_args()

    if args.start and args.end:
        from datetime import datetime as _dt
        start_d = _dt.strptime(args.start, "%Y-%m-%d").date()
        end_d = _dt.strptime(args.end, "%Y-%m-%d").date()
    else:
        end_d = date.today() - timedelta(days=1)
        start_d = end_d - timedelta(weeks=args.weeks)

    targets = []
    for d in daterange(start_d, end_d):
        wd = d.weekday()  # 0=Mon ... 6=Sun
        if args.mondays_only and wd != 0:
            continue
        if args.tue_sun and wd == 0:
            continue
        targets.append(d)

    print(f"Targets: {len(targets)} dates from {start_d} to {end_d}")
    if not targets:
        print("Nothing to pull.")
        return

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("pip install playwright && playwright install chromium", file=sys.stderr)
        sys.exit(1)

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Profile: {PROFILE_DIR}")

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,  # let user see + log in if needed
            viewport={"width": 1400, "height": 900},
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        # Initial nav — auto-login if needed
        page.goto(REPORT_URL, wait_until="domcontentloaded", timeout=60000)
        time.sleep(3)
        if "/Public/Login" in page.url:
            print("Not logged in — auto-logging in with stored creds...", flush=True)
            print(f"  page url: {page.url}", flush=True)
            try:
                page.wait_for_selector("input#Username, input#username", timeout=15000, state="visible")
            except Exception as e:
                print(f"  username field not found: {e}", flush=True)
                Path("scraper/_brink_login_debug.html").write_text(page.content(), encoding="utf-8")
                ctx.close()
                sys.exit(1)
            page.locator("input#Username, input#username").first.fill("fg2065@estep-co.com")
            page.locator("input#Password, input#password").first.fill("Muscle426$$")
            page.locator("button:has-text('Continue'), input[type=submit], #submitLogin").first.click()
            page.wait_for_load_state("networkidle", timeout=30000)
            if "/Public/Login" in page.url:
                print("ERROR: auto-login failed. Aborting.", flush=True)
                ctx.close()
                sys.exit(1)
            print("Logged in.", flush=True)
            page.goto(REPORT_URL, wait_until="networkidle", timeout=60000)

        # Select KY-2065 by directly injecting the form's hidden fields
        # GUIDs captured 2026-05-05 from a real selection
        KY2065_GUID = "cb10d857-83f6-4861-8ca7-25952377068f"
        GROUP_VALUES = "449,503,502,518,581"
        page.evaluate("""(args) => {
            const setOrCreate = (name, value) => {
                let inp = document.querySelector(`input[name='${name}']`);
                if (!inp) {
                    inp = document.createElement('input');
                    inp.type = 'hidden';
                    inp.name = name;
                    document.querySelector('form').appendChild(inp);
                }
                inp.value = value;
            };
            // Replicate 9× as Brink's UI does it
            setOrCreate('LocationsModel.HierarchyControl.LocationValues', Array(9).fill(args.guid).join(','));
            setOrCreate('LocationsModel.HierarchyControl.LocationGroupValues', args.groups);
            setOrCreate('LocationsModel.Type', 'SelectLocations');
        }""", {"guid": KY2065_GUID, "groups": GROUP_VALUES})
        print("Injected KY-2065 location into form.", flush=True)

        # Helper to ensure location is set every iteration (form rerenders after submit)
        def ensure_location():
            page.evaluate("""(args) => {
                const setOrCreate = (name, value) => {
                    let inp = document.querySelector(`input[name='${name}']`);
                    if (!inp) {
                        inp = document.createElement('input');
                        inp.type = 'hidden';
                        inp.name = name;
                        document.querySelector('form').appendChild(inp);
                    }
                    inp.value = value;
                };
                setOrCreate('LocationsModel.HierarchyControl.LocationValues', Array(9).fill(args.guid).join(','));
                setOrCreate('LocationsModel.HierarchyControl.LocationGroupValues', args.groups);
                setOrCreate('LocationsModel.Type', 'SelectLocations');
            }""", {"guid": KY2065_GUID, "groups": GROUP_VALUES})

        results = {}
        skipped = []
        for i, d in enumerate(targets, 1):
            ds = d.strftime("%-m/%-d/%Y") if sys.platform != "win32" else d.strftime("%#m/%#d/%Y")
            iso = d.isoformat()
            print(f"  [{i}/{len(targets)}] {iso} ({d.strftime('%a')}) ...", end=" ", flush=True)
            out_dir = ROOT / "data" / "raw" / "parbrink" / args.store / iso
            dest_pdf = out_dir / "Hourly Sales And Labor.pdf"
            if dest_pdf.exists():
                print("SKIP (already on disk)")
                continue
            try:
                ensure_location()
                # Set date
                page.locator("#DateRangeModel_Date").fill(ds)
                # Click View Report
                page.locator("#run-report").click()
                # Wait for the report viewer to render — look for the export/save button to be enabled
                time.sleep(8)
                # Trigger PDF download via the DXR.axd export endpoint directly
                # The DevExpress viewer exposes export via document.querySelector
                # Easier: use the existing keyboard shortcut OR click the export icon
                # Strategy: click the Save/Export icon (floppy disk) and accept PDF download
                with page.expect_download(timeout=30000) as dl_info:
                    # The export button has a specific DevExpress class
                    page.evaluate("""() => {
                        // DevExpress report viewer exposes an export API via the toolbar
                        // Find the save/export button
                        const btns = document.querySelectorAll('img[title*="Save"], img[alt*="Save"], button[title*="Save"], img[title*="Export"], [class*="dxrd-save"], [class*="dxrd-export"]');
                        for (const b of btns) {
                            const r = b.getBoundingClientRect();
                            if (r.width > 0) { b.click(); return 'clicked: ' + (b.title||b.alt||b.className); }
                        }
                        return 'no save btn';
                    }""")
                    download = dl_info.value
                out_dir.mkdir(parents=True, exist_ok=True)
                download.save_as(str(dest_pdf))
                print(f"OK (saved {dest_pdf.stat().st_size} bytes)")
            except Exception as e:
                print(f"ERR: {str(e)[:150]}")
                skipped.append(iso)

        print(f"\n=== Pulled {len(results)} | skipped {len(skipped)} ===")
        if skipped:
            print(f"Skipped: {skipped}")
        ctx.close()


if __name__ == "__main__":
    main()
