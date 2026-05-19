#!/usr/bin/env python3
"""
Scrape the BOSS bread calendar at bread2.fiveguys.com.

Output: data/boss_calendar.json with the next ~6 weeks of bread orders,
plus holiday-week detection so the bread tool / brief can warn ahead.

Auth: form POST to index.php with BOSS_USERNAME / BOSS_PASSWORD (env or GH
secrets). Session cookie (PHPSESSID) lives for the duration of the run.

Discovery: scraper/BOSS_API.md.
"""

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://bread2.fiveguys.com"
LOGIN = f"{BASE}/login.php"
ORDERS = f"{BASE}/orders.php"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
}

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
OUT_PATH = DATA_DIR / "boss_calendar.json"

DAY_NAMES = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


def login(username: str, password: str) -> requests.Session:
    """POST credentials to orders.php (the login form action), return an authenticated session.
    Real BOSS login form (discovered 2026-05-19): action=orders.php, fields = User / Password / Remember / Submit."""
    s = requests.Session()
    s.headers.update(HEADERS)

    # GET the login page first to establish a session cookie
    s.get(LOGIN, timeout=30)

    payload = {
        "User": username,
        "Password": password,
        "Submit": "Log In",
    }
    r = s.post(LOGIN, data=payload, timeout=30, allow_redirects=True,
               headers={"Referer": LOGIN})
    r.raise_for_status()
    if "Log Out" not in r.text:
        # Surface the actual error returned by BOSS so we can debug.
        snippet = BeautifulSoup(r.text, "html.parser").get_text(" ", strip=True)
        snippet = re.sub(r"\s+", " ", snippet)[:600]
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        (DATA_DIR / "boss_login_debug.html").write_text(r.text, encoding="utf-8")
        raise RuntimeError(
            f"BOSS login failed. Landing URL: {r.url}\n"
            f"Page snippet: {snippet}\n"
            "Saved full response to data/boss_login_debug.html"
        )
    return s


def fetch_calendar_html(s: requests.Session) -> str:
    r = s.get(ORDERS, timeout=30)
    r.raise_for_status()
    return r.text


def parse_month_range(soup: BeautifulSoup) -> str:
    txt = soup.get_text(" ", strip=True)
    m = re.search(r"([A-Z][a-z]+)\s*/\s*([A-Z][a-z]+)", txt)
    return m.group(0) if m else ""


def infer_year_for_day(day_num: int, today: dt.date, prev_day: int | None) -> int:
    """Calendar headers like 'May / June' span months; cells just show day numbers.
    We infer year+month from the today anchor and the day sequence (resets on new month)."""
    return today.year  # year rarely matters here; month inferred separately


def parse_cells(html: str, today: dt.date) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", id="calendar")
    if not table:
        return []

    month_range = parse_month_range(soup)
    # Calendar shows two months when the range spans (e.g. "May / June")
    months = [m.lower() for m in re.findall(r"[A-Z][a-z]+", month_range)]
    month_nums = []
    for name in months:
        try:
            month_nums.append(dt.datetime.strptime(name[:3], "%b").month)
        except ValueError:
            pass
    if not month_nums:
        month_nums = [today.month, (today.month % 12) + 1]

    cells = []
    prev_day = 0
    cur_month_idx = 0

    for td in table.find_all("td"):
        date_num_el = td.find(class_="date_number")
        day_str = date_num_el.get_text(strip=True) if date_num_el else ""
        if not day_str.isdigit():
            # Empty leading/trailing cells
            cells.append({"empty": True})
            continue
        day = int(day_str)
        # Detect month roll-over: when day numbers reset (e.g. 31 → 01)
        if day < prev_day - 5:  # heuristic: any drop > 5 = new month
            cur_month_idx = min(cur_month_idx + 1, len(month_nums) - 1)
        prev_day = day
        month = month_nums[cur_month_idx]
        # Year: roll back/forward if the rendered cell month is before/after today's month
        year = today.year
        if month < today.month - 6:
            year += 1
        elif month > today.month + 6:
            year -= 1
        try:
            date = dt.date(year, month, day)
        except ValueError:
            cells.append({"empty": True})
            continue

        cls = td.get("class") or []
        cell_text = td.get_text(" ", strip=True)
        cell_html = str(td)

        hb_match = re.search(r"(\d+)\s*HB", cell_text)
        hd_match = re.search(r"(\d+)\s*HD", cell_text)
        sub_match = re.search(r"(\d{2}/\d{2}/\d{4})", cell_text)

        has_modify = 'modify.gif' in cell_html
        has_transit = 'transit' in cell_html.lower()
        has_place = 'order.gif' in cell_html
        has_issue = 'Bread_Issue' in cell_html or 'Issue_Button' in cell_html
        is_holiday = 'holiday' in ' '.join(cls).lower()

        weekday = date.weekday()  # Mon=0..Sun=6
        cells.append({
            "date": date.isoformat(),
            "weekday": DAY_NAMES[weekday],
            "td_class": ' '.join(cls),
            "hb_trays": int(hb_match.group(1)) if hb_match else None,
            "hd_trays": int(hd_match.group(1)) if hd_match else None,
            "submitted_on": sub_match.group(1) if sub_match else None,
            "is_holiday_cell": is_holiday,
            "is_transit": has_transit,
            "is_adjustable": has_modify,
            "is_place_slot": has_place,
            "has_issue": has_issue,
            "is_past": 'past_date' in cls,
            "is_future": 'future_date' in cls,
            "is_delivery_day": (hb_match is not None) or (hd_match is not None) or has_place or has_modify or has_transit,
        })

    return [c for c in cells if not c.get("empty")]


def detect_holiday_weeks(cells: list[dict]) -> list[dict]:
    """Group cells by ISO week, flag weeks that contain any holiday-class cell.
    For each holiday week, identify the skipped delivery day (blank Mon adjacent to holiday cells)."""
    by_week = {}
    for c in cells:
        d = dt.date.fromisoformat(c["date"])
        mon = d - dt.timedelta(days=d.weekday())
        wk_key = mon.isoformat()
        by_week.setdefault(wk_key, []).append(c)

    flagged = []
    for wk_key, days in sorted(by_week.items()):
        has_holiday = any(d.get("is_holiday_cell") for d in days)
        if not has_holiday:
            continue
        # Find the skipped delivery slot in this week:
        # a future_date cell that's a typical delivery weekday (Mon/Wed/Fri/Sat for 2065)
        # but has no HB/HD/place/modify/transit signal.
        delivery_weekdays = {"MON", "WED", "FRI", "SAT"}
        skipped = [
            d for d in days
            if d["weekday"] in delivery_weekdays
            and not d.get("is_delivery_day")
            and d.get("is_future")
        ]
        flagged.append({
            "week_start_mon": wk_key,
            "days": days,
            "skipped_delivery_days": [s["date"] for s in skipped],
        })
    return flagged


def main():
    username = os.environ.get("BOSS_USERNAME")
    password = os.environ.get("BOSS_PASSWORD")
    if not username or not password:
        print("ERROR: BOSS_USERNAME and BOSS_PASSWORD must be set.", file=sys.stderr)
        sys.exit(2)

    today = dt.date.today()
    print(f"[boss] login as {username} ...")
    s = login(username, password)
    print(f"[boss] login OK; fetching calendar")
    html = fetch_calendar_html(s)

    # Save raw HTML for debug
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "boss_calendar.raw.html").write_text(html, encoding="utf-8")

    cells = parse_cells(html, today)
    holiday_weeks = detect_holiday_weeks(cells)

    out = {
        "meta": {
            "generated": dt.datetime.now().isoformat(timespec="seconds"),
            "today": today.isoformat(),
            "source": ORDERS,
            "store": "2065",
            "delivery_days": ["MON", "WED", "FRI", "SAT"],
        },
        "cells": cells,
        "holiday_weeks": holiday_weeks,
    }
    OUT_PATH.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[boss] wrote {OUT_PATH}  cells={len(cells)}  holiday_weeks={len(holiday_weeks)}")
    for hw in holiday_weeks:
        print(f"  HOLIDAY WEEK starting {hw['week_start_mon']} — skipped: {hw['skipped_delivery_days']}")


if __name__ == "__main__":
    main()
