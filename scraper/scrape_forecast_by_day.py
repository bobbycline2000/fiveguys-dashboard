#!/usr/bin/env python3
"""
Pull this week + next week per-day Forecasted Sales from CrunchTime.

THIS WEEK comes from /resource/dashboard/performance/metrics
  - "Forecasted Sales" + "Actual Net Sales" rows, per calcId 1..7 (Sun..Sat)

NEXT WEEK comes from /resource/sales/sales/forecast (the Manage Sales Forecast page)
  - Body: {"node":"root","extraFilter":[]}
  - Returns week objects with day1..day7. Day1 = Sunday. (CT week starts Sun.)
  - We dump the raw response to data/_debug/sales_forecast.json for inspection
    on first run, then extract next week's day1..day7 from it.

Output: data/forecast_by_day.json
{
  "meta": { "generated": "...", "today": "...", "week_start": "...", "week_end_plus_7": "..." },
  "days": [ { "date": "...", "name": "SUN", "forecast": 3500.0, "actual": 3200.0, "is_next_week": false }, ... ]
}
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
DAY_NAMES = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']  # CT order: day1=Sun


def week_start_sunday(d: datetime.date) -> datetime.date:
    # Python: Mon=0..Sun=6. CT week starts Sunday.
    # If today is Sunday (weekday()==6), week_start = today.
    return d - datetime.timedelta(days=(d.weekday() + 1) % 7)


def fetch_sales_forecast(jar):
    body = {"node": "root", "extraFilter": []}
    r = requests.post(FORECAST_URL, json=body, cookies=jar, headers=HEADERS, timeout=30)
    r.raise_for_status()
    try:
        return r.json()
    except Exception:
        return r.text


def find_week_objects(payload):
    """Walk payload recursively, return any dict that has day1..day7 keys."""
    out = []

    def walk(node):
        if isinstance(node, dict):
            keys = set(node.keys())
            if all(f"day{i}" in keys for i in range(1, 8)):
                out.append(node)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(payload)
    return out


def parse_date(s):
    if not s:
        return None
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d-%b-%y", "%d-%b-%Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.datetime.strptime(s.split("T")[0], fmt.split("T")[0]).date()
        except ValueError:
            continue
    return None


def coerce_float(v):
    if v in (None, "", "—"):
        return None
    try:
        return float(str(v).replace("$", "").replace(",", ""))
    except (TypeError, ValueError):
        return None


def main():
    today = datetime.date.today()
    this_week_start = week_start_sunday(today)
    next_week_start = this_week_start + datetime.timedelta(days=7)

    jar = load_cookies()
    if not jar or not session_alive(jar):
        remint()
        jar = load_cookies()
        if not session_alive(jar):
            raise RuntimeError("re-mint did not produce a live session")

    # ── THIS WEEK from performance metrics ─────────────────────────────
    metrics = fetch_metrics(jar)
    fcst_row = find_metric(metrics, "Forecasted Sales")
    actual_row = find_metric(metrics, "Actual Net Sales")
    if not fcst_row:
        raise RuntimeError("Forecasted Sales row not found in performance metrics")

    this_week = []
    for i in range(7):
        d = this_week_start + datetime.timedelta(days=i)
        calcid = d.isoweekday() % 7 + 1  # Sun=1..Sat=7
        f = value_for_calcid(fcst_row, calcid)
        a = value_for_calcid(actual_row, calcid)
        this_week.append({
            "date": d.isoformat(),
            "name": DAY_NAMES[i],
            "forecast": coerce_float(f),
            "actual": coerce_float(a),
            "is_next_week": False,
        })

    # ── NEXT WEEK from /resource/sales/sales/forecast ──────────────────
    next_week = [
        {"date": (next_week_start + datetime.timedelta(days=i)).isoformat(),
         "name": DAY_NAMES[i],
         "forecast": None, "actual": None, "is_next_week": True}
        for i in range(7)
    ]

    debug_dir = DATA_DIR / "_debug"
    debug_dir.mkdir(exist_ok=True)
    try:
        payload = fetch_sales_forecast(jar)
        (debug_dir / "sales_forecast_raw.json").write_text(
            json.dumps(payload, indent=2, default=str)
        )
        weeks = find_week_objects(payload)
        print(f"[forecast] /sales/sales/forecast returned {len(weeks)} week-shaped objects")

        # Match each week object to a week-start date if possible
        for w in weeks:
            ws = None
            for k in ("weekStartDate", "weekStart", "startDate", "weekBeginning",
                      "fiscalWeekStart", "weekBeginDate", "beginDate"):
                if k in w:
                    ws = parse_date(w[k])
                    if ws:
                        break
            if ws == next_week_start:
                for i in range(7):
                    val = coerce_float(w.get(f"day{i+1}"))
                    if val is not None:
                        next_week[i]["forecast"] = val
                print(f"[forecast] matched next week ({next_week_start}) — filled day1..day7")
                break
        else:
            # Fallback: if there are exactly 2 weeks and we can't match by date, assume order = [this, next]
            if len(weeks) >= 2:
                w = weeks[1]
                for i in range(7):
                    next_week[i]["forecast"] = coerce_float(w.get(f"day{i+1}"))
                print(f"[forecast] no date match — used 2nd week object as next week (positional fallback)")
            else:
                print(f"[forecast] could not extract next week — see data/_debug/sales_forecast_raw.json")
    except Exception as e:
        print(f"[forecast] FAILED to pull next week: {e}", file=sys.stderr)

    days = this_week + next_week
    out = {
        "meta": {
            "generated": datetime.datetime.now().isoformat(timespec='seconds'),
            "today": today.isoformat(),
            "week_start": this_week_start.isoformat(),
            "week_end_plus_7": (this_week_start + datetime.timedelta(days=13)).isoformat(),
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
