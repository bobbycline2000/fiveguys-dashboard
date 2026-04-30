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

LOGIN_URL = "https://fiveguysfr77.ct-teamworx.com/views/auth.jsp"
ROSTER_URL = "https://fiveguysfr77.ct-teamworx.com/views/manager/tablet/dailyRoster.jsp"
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
    Parse Teamworx Daily Roster page text into a flat list of shifts.
    Roster groups employees under section headers like:
      'General Manager-Salary'
      'Shift Leader-Hourly'
      '2. Crew'  (or just 'Crew')
    Each shift row: <name> <position> <in_time> <out_time> <hrs> <ot_hrs>
    """
    shifts: list[dict] = []
    current_section = None
    section_re = re.compile(
        r'^(General Manager[-\s]?Salary|Shift Leader[-\s]?Hourly|\d?\.?\s*Crew|Crew)\b',
        re.IGNORECASE,
    )
    # Row pattern: name (multi-word) ... time time hrs ot
    row_re = re.compile(
        r'^(?P<name>[A-Z][A-Za-z\-\'\.]+(?:\s+[A-Z][A-Za-z\-\'\.]+)+)\s+'
        r'(?P<position>(?:General Manager[-\s]?Salary|Shift Leader[-\s]?Hourly|\d?\.?\s*Crew|Crew))\s+'
        r'(?P<in>\d{1,2}:\d{2}\s*(?:AM|PM))\s+'
        r'(?P<out>\d{1,2}:\d{2}\s*(?:AM|PM))\s+'
        r'(?P<hrs>\d+(?:\.\d+)?)\s+'
        r'(?P<ot>\d+(?:\.\d+)?)\s*$',
        re.IGNORECASE,
    )

    for raw in page_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        sm = section_re.match(line)
        if sm and "total" not in line.lower():
            current_section = sm.group(1)
            continue
        m = row_re.match(line)
        if m:
            shifts.append({
                "name": short_name(m.group("name")),
                "role": map_role(m.group("position")),
                "start": normalize_time(m.group("in")),
                "end":   normalize_time(m.group("out")),
                "hrs":   float(m.group("hrs")),
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
        page.fill('input[name="username"], input[type="text"]', user)
        page.fill('input[name="password"], input[type="password"]', pwd)
        # Click Sign In button (orange button)
        page.click('button:has-text("Sign In"), input[type="submit"]')
        page.wait_for_load_state("networkidle", timeout=20000)

        # 2. Pick KY-2065 if Location Selection appears
        if "locationSelection" in page.url:
            page.fill('input[placeholder*="Select Location"], input[type="search"]', store_id)
            page.wait_for_timeout(800)
            # Click the matching row
            page.click(f'text=KY-{store_id}')
            page.wait_for_load_state("networkidle", timeout=20000)

        # 3. Navigate to Daily Roster
        page.goto(ROSTER_URL, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle", timeout=20000)
        page.wait_for_timeout(1500)  # allow data to render

        # 4. Verify date matches; if not, navigate via the date arrows
        page_text = page.inner_text("body")
        if target_date.strftime("%a, %b %d, %Y") not in page_text \
           and target_date.strftime("%A, %b %d, %Y") not in page_text:
            print(f"WARNING: roster page may not be on {today_iso}", file=sys.stderr)

        # 5. Save raw page text for debugging
        (ROOT / "data" / "teamworx_roster_text.txt").write_text(page_text, encoding="utf-8")

        # 6. Parse shifts
        shifts = parse_roster_text(page_text)

        ctx.close()
        browser.close()

    if not shifts:
        print("ERROR: parsed 0 shifts from roster page (see data/teamworx_roster_text.txt)",
              file=sys.stderr)
        return 1

    total_hrs = sum(s.get("hrs", 0) for s in shifts)
    # Strip the hrs key before writing (dashboard schema doesn't use it directly)
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
