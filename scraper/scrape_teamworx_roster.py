#!/usr/bin/env python3
"""
Scrape today's Daily Roster from Teamworx → weekly_schedule.json.

Source: https://fiveguysfr77.ct-teamworx.com/views/manager/tablet/dailyRoster.jsp
Auth:   Same credentials as CrunchTime (CRUNCHTIME_USERNAME / CRUNCHTIME_PASSWORD)

Output: data/raw/parbrink/{store}/{today}/weekly_schedule.json (Teamworx-sourced —
        overrides any Par Brink "weekly schedule" PDF that's stale by a week,
        because wire_dashboard's load_latest sorts by ISO date and today wins).

Why this script exists:
Par Brink's weekly schedule email arrives AFTER the week ends — it's a payroll
report, not a planning document. Bobby actually lives in Teamworx for shift
planning. The dashboard's "Today's Schedule" card needs the day's published
roster, not last week's recap.

Usage:
    python scraper/scrape_teamworx_roster.py --store 2065
    python scraper/scrape_teamworx_roster.py --store 2065 --date 2026-04-30
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, date, timedelta, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
ET = timezone(timedelta(hours=-4))

LOGIN_URL    = "https://fiveguysfr77.ct-teamworx.com/views/auth.jsp"
HOME_URL     = "https://fiveguysfr77.ct-teamworx.com/views/manager/tablet/home.jsp"
ROSTER_URL   = HOME_URL  # kept for JSON meta field — roster is SPA-loaded inside home.jsp
LOCATION_URL = "https://fiveguysfr77.ct-teamworx.com/views/locationSelection.jsp"


def short_name(full: str) -> str:
    """'Cline, Robert' → 'Robert C.'  / 'Llorente Mejias, Francisco' → 'Francisco L.'
       'Hernandez Rodriguez, Maylin' → 'Maylin H.'  /  'Robert Cline' → 'Robert C.'"""
    full = full.strip()
    if "," in full:
        last, first = (p.strip() for p in full.split(",", 1))
        first_word = first.split()[0] if first.split() else ""
        last_first = last.split()[0] if last.split() else ""
        return f"{first_word} {last_first[:1]}." if first_word and last_first else full
    parts = full.split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[-1][:1]}."
    return full


def map_role(position: str) -> str:
    """Position string → dashboard role label."""
    p = position.lower()
    if "general manager" in p:
        return "General Manager"
    if "shift lead" in p:
        return "Shift Lead"
    if "crew" in p:
        return "Crew"
    return position.strip() or "Crew"


def normalize_time(s: str) -> str:
    """'7:30 AM' → '07:30 AM'."""
    m = re.match(r'\s*(\d{1,2}):(\d{2})\s*(AM|PM)\s*', s, re.IGNORECASE)
    if not m:
        return s.strip()
    return f"{int(m.group(1)):02d}:{m.group(2)} {m.group(3).upper()}"


def parse_roster_text(page_text: str) -> list[dict]:
    """
    Parse Teamworx Daily Roster inner_text() into a flat list of shifts.

    Teamworx renders a table whose cells are tab-separated in inner_text:
      'KBKaisha Brewer\t2. Crew\t8:00 AM\t2:00 PM\t6\t0'
    The first cell prepends a 2-char initials block with no separator.
    """
    shifts: list[dict] = []
    time_re = re.compile(r'^\d{1,2}:\d{2}\s*(?:AM|PM)$', re.IGNORECASE)

    for raw in page_text.splitlines():
        parts = raw.split('\t')
        if len(parts) < 5:
            continue
        name_raw, position, in_t, out_t = parts[0], parts[1], parts[2], parts[3]
        hrs_raw = parts[4]

        # Validate times
        if not time_re.match(in_t.strip()) or not time_re.match(out_t.strip()):
            continue
        if not position.strip():
            continue

        # Strip 2-char uppercase initials prefix (e.g. "KBKaisha Brewer" → "Kaisha Brewer")
        name_clean = re.sub(r'^[A-Z]{2}', '', name_raw).strip()
        if not name_clean:
            continue

        try:
            hrs = float(hrs_raw.strip())
        except ValueError:
            hrs = 0.0

        shifts.append({
            "name":  short_name(name_clean),
            "role":  map_role(position.strip()),
            "start": normalize_time(in_t.strip()),
            "end":   normalize_time(out_t.strip()),
            "hrs":   hrs,
        })
    return shifts


def run(store_id: str, target_date: date) -> int:
    from playwright.sync_api import sync_playwright

    user = os.environ.get("CRUNCHTIME_USERNAME") or os.environ.get("TEAMWORX_USERNAME")
    pwd  = os.environ.get("CRUNCHTIME_PASSWORD") or os.environ.get("TEAMWORX_PASSWORD")
    if not user or not pwd:
        print("ERROR: CRUNCHTIME_USERNAME/PASSWORD not set", file=sys.stderr)
        return 2

    today_iso = target_date.isoformat()
    out_dir = ROOT / "data" / "raw" / "parbrink" / store_id / today_iso
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "weekly_schedule.json"

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()

        # 1. Login
        page.goto(LOGIN_URL, wait_until="domcontentloaded")
        page.fill('input[placeholder*="Username"], input[type="text"]', user)
        page.fill('input[type="password"]', pwd)
        page.get_by_role("button", name="Sign In").click()
        page.wait_for_load_state("networkidle", timeout=20000)

        # 2. Pick KY-2065 if Location Selection appears
        if "locationSelection" in page.url:
            page.get_by_role("cell", name=f"KY-{store_id}").first.click()
            page.wait_for_load_state("networkidle", timeout=20000)

        # 2b. Dump cookies for the pure-HTTP API clients (e.g. scrape_teamworx_ideal_vs_actual.py)
        try:
            cookies = ctx.cookies()
            cookie_file = ROOT / "data" / "twx_cookies.json"
            cookie_file.parent.mkdir(parents=True, exist_ok=True)
            cookie_file.write_text(json.dumps(cookies, indent=2), encoding="utf-8")
            print(f"[teamworx-roster] saved {len(cookies)} cookies to {cookie_file}")
        except Exception as e:
            print(f"[teamworx-roster] cookie dump failed (non-fatal): {e}", file=sys.stderr)

        # 3. Click Daily Roster nav item (SPA — stays on home.jsp, loads roster content)
        page.get_by_text("Daily Roster", exact=True).first.click()
        # Wait for the roster table to render (employee rows have 6 cells)
        page.wait_for_selector("table td:nth-child(3)", timeout=15000)
        page.wait_for_timeout(800)

        # 4. Verify the date shown is today
        page_text = page.inner_text("body")
        # Build both padded and non-padded variants (cross-platform)
        _day = str(target_date.day)
        date_str  = f"{target_date.strftime('%A, %B')} {_day}, {target_date.year}"  # "Friday, May 1, 2026"
        date_str2 = target_date.strftime("%A, %b %d, %Y")                            # "Friday, May 01, 2026"
        if date_str not in page_text and date_str2 not in page_text:
            print(f"WARNING: roster page may not be showing {today_iso} — found different date",
                  file=sys.stderr)

        # 5. Save raw page text for debugging
        (ROOT / "data" / "teamworx_roster_text.txt").write_text(page_text, encoding="utf-8")

        # 6. Parse shifts from inner_text (tab-separated table cells)
        shifts = parse_roster_text(page_text)

        ctx.close()
        browser.close()

    if not shifts:
        print("ERROR: parsed 0 shifts from roster page (see data/teamworx_roster_text.txt)",
              file=sys.stderr)
        return 1

    total_hrs = sum(s.get("hrs", 0) for s in shifts)
    # Drop the hrs key — dashboard schema uses name/role/start/end only
    out_shifts = [{k: v for k, v in s.items() if k != "hrs"} for s in shifts]

    monday = target_date - timedelta(days=target_date.weekday())
    sunday = monday + timedelta(days=6)

    out = {
        "meta": {
            "source": "Teamworx Daily Roster (Playwright scrape)",
            "store_id": store_id,
            "report_date": today_iso,
            "week_start": monday.isoformat(),
            "week_end":   sunday.isoformat(),
            "generated":  datetime.now(tz=ET).isoformat(timespec="seconds"),
            "source_url": ROSTER_URL,
        },
        "totals_by_day": {today_iso: round(total_hrs, 2)},
        "schedule": {
            today_iso: {
                "date": today_iso,
                "day_of_week": target_date.strftime("%A"),
                "scheduled_hours": round(total_hrs, 2),
                "shifts": out_shifts,
            }
        },
        "today": {
            "date": today_iso,
            "day_of_week": target_date.strftime("%A"),
            "scheduled_hours": round(total_hrs, 2),
            "shifts": out_shifts,
        },
    }

    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"  {target_date.strftime('%A %b %d')}: {len(shifts)} shifts, {total_hrs:.2f} hrs")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True)
    ap.add_argument("--date", help="YYYY-MM-DD (default: today in ET)")
    args = ap.parse_args()

    if args.date:
        target = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        target = datetime.now(tz=ET).date()

    sys.exit(run(args.store, target))


if __name__ == "__main__":
    main()
