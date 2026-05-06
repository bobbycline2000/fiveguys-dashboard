#!/usr/bin/env python3
"""
Pull this week + next week per-day Forecasted Sales from CrunchTime
and write data/forecast_by_day.json for the bread tool.

Two endpoints, two different week conventions — important:

1. /resource/sales/sales/forecast (Manage Sales Forecast)
   - Returns top-level "type=forecast" items with `weekEnding` (Sunday, MM/DD/YYYY)
     and day1..day7 = MONDAY..SUNDAY $ forecast.
   - Each item has children with type=guests / type=checks (day1..day7 are counts,
     NOT $ — the previous walker incorrectly grabbed those).
   - Source for THIS WEEK and NEXT WEEK forecasts.

2. /resource/dashboard/performance/metrics (Performance Metrics box)
   - calcId 1=Sun..7=Sat (Sun-Sat week starting from PAST Sunday).
   - Source for THIS WEEK actuals only.

Bread tool aligns to Mon-Sun weeks (matches Five Guys ops convention).
Output: 14 days, Mon..Sun (this week) + Mon..Sun (next week).
"""

import datetime, json, sys
from pathlib import Path

import requests

from api_query import (
    DATA_DIR, NETCHEF_BASE, HEADERS,
    load_cookies, session_alive, remint,
    fetch_metrics, find_metric, value_for_calcid,
)

FORECAST_URL = f"{NETCHEF_BASE}/resource/sales/sales/forecast"
DAY_NAMES = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']  # forecast endpoint order


def this_week_monday(d: datetime.date) -> datetime.date:
    return d - datetime.timedelta(days=d.weekday())  # Python weekday(): Mon=0..Sun=6


def fetch_sales_forecast(jar):
    body = {"node": "root", "extraFilter": []}
    r = requests.post(FORECAST_URL, json=body, cookies=jar, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def collect_forecast_weeks(payload):
    """Return list of (weekEnding_date, day_values_dict) for type='forecast' items only."""
    out = []

    def walk(n):
        if isinstance(n, dict):
            if n.get("type") == "forecast" and n.get("weekEnding"):
                we_raw = str(n["weekEnding"]).split(" ")[0]  # "05/10/2026"
                try:
                    we = datetime.datetime.strptime(we_raw, "%m/%d/%Y").date()
                except ValueError:
                    we = None
                if we:
                    out.append((we, {f"day{i}": n.get(f"day{i}") for i in range(1, 8)}))
            # IMPORTANT: do NOT recurse into 'children' — those are guests/checks counts
            # but DO recurse into other container fields
            for k, v in n.items():
                if k != "children":
                    walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)

    walk(payload)
    return out


def coerce_float(v):
    if v in (None, "", "—"):
        return None
    try:
        return float(str(v).replace("$", "").replace(",", ""))
    except (TypeError, ValueError):
        return None


def calcid_for_date(d: datetime.date) -> int:
    # performance/metrics: Sun=1..Sat=7
    return d.isoweekday() % 7 + 1


def main():
    today = datetime.date.today()
    this_mon = this_week_monday(today)
    next_mon = this_mon + datetime.timedelta(days=7)
    this_week_ending = this_mon + datetime.timedelta(days=6)  # Sunday
    next_week_ending = next_mon + datetime.timedelta(days=6)

    jar = load_cookies()
    if not jar or not session_alive(jar):
        remint()
        jar = load_cookies()
        if not session_alive(jar):
            raise RuntimeError("re-mint did not produce a live session")

    # ── FORECASTS (this week + next week) from /sales/sales/forecast ────
    debug_dir = DATA_DIR / "_debug"
    debug_dir.mkdir(exist_ok=True)
    payload = fetch_sales_forecast(jar)
    (debug_dir / "sales_forecast_raw.json").write_text(json.dumps(payload, indent=2, default=str))

    weeks = collect_forecast_weeks(payload)
    by_ending = {we: vals for we, vals in weeks}
    print(f"[forecast] {len(weeks)} forecast week objects (filtered out guests/checks children)")

    this_vals = by_ending.get(this_week_ending)
    next_vals = by_ending.get(next_week_ending)
    if not this_vals:
        print(f"[warn] no forecast for week ending {this_week_ending}")
    if not next_vals:
        print(f"[warn] no forecast for week ending {next_week_ending}")

    days = []
    for offset in range(14):
        d = this_mon + datetime.timedelta(days=offset)
        in_next_week = offset >= 7
        vals = next_vals if in_next_week else this_vals
        # offset 0..6 -> day1..day7 (Mon..Sun)
        idx = (offset % 7) + 1
        f = coerce_float(vals.get(f"day{idx}")) if vals else None
        days.append({
            "date": d.isoformat(),
            "name": DAY_NAMES[offset % 7],
            "forecast": f,
            "actual": None,
            "is_next_week": in_next_week,
        })

    # ── ACTUALS (this week, Mon..today) from performance/metrics ────────
    try:
        metrics = fetch_metrics(jar)
        actual_row = find_metric(metrics, "Actual Net Sales")
        if actual_row:
            for d in days:
                if d["is_next_week"]:
                    continue
                date = datetime.date.fromisoformat(d["date"])
                if date > today:
                    continue
                cid = calcid_for_date(date)
                a = value_for_calcid(actual_row, cid)
                d["actual"] = coerce_float(a)
    except Exception as e:
        print(f"[warn] couldn't pull actuals: {e}", file=sys.stderr)

    out = {
        "meta": {
            "generated": datetime.datetime.now().isoformat(timespec='seconds'),
            "today": today.isoformat(),
            "this_week_mon": this_mon.isoformat(),
            "next_week_mon": next_mon.isoformat(),
            "week_convention": "Mon-Sun",
        },
        "days": days,
    }
    out_path = DATA_DIR / "forecast_by_day.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"[ok] wrote {out_path}")
    for d in days:
        f = f"${d['forecast']:,.0f}" if d['forecast'] is not None else "—"
        a = f"${d['actual']:,.0f}" if d['actual'] is not None else "—"
        tag = " (next wk)" if d['is_next_week'] else ""
        print(f"  {d['name']} {d['date']}{tag}  forecast={f}  actual={a}")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
