#!/usr/bin/env python3
"""
Pull weekly ideal-vs-scheduled hours from Teamworx (lights-out, pure HTTP).

Endpoint: POST /json/mn/laborSchedule/getWbForecastData
Auth:     cookies from data/twx_cookies.json (shared with teamworx_api.py)

Output:   data/raw/teamworx/<store>/week-ending-<YYYY-MM-DD>/ideal_vs_actual.json

Usage:
    python scraper/scrape_teamworx_ideal_vs_actual.py --store 2065
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date as date_cls, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from teamworx_api import load_session, _post_json, BASE  # noqa: E402

ROOT     = Path(__file__).resolve().parents[1]
RAW      = ROOT / "data" / "raw" / "teamworx"

DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def week_ending_sunday(today: date_cls) -> date_cls:
    # Mon=0 ... Sun=6; week ends on Sunday.
    return today + timedelta(days=(6 - today.weekday()) % 7)


def fetch_forecast(store: str) -> dict:
    s = load_session()
    today = date_cls.today()
    week_end = week_ending_sunday(today)
    body = {"laborDate": None, "weekEndingDate": week_end.isoformat()}
    data = _post_json(s, "/json/mn/laborSchedule/getWbForecastData", body)
    # Diagnostic — print full response inline (truncated).
    try:
        print(f"[debug] top-level keys: {list(data.keys())}")
        for k in list(data.keys())[:6]:
            v = data[k]
            if isinstance(v, dict):
                print(f"[debug] {k} = dict keys: {list(v.keys())}")
            elif isinstance(v, list):
                print(f"[debug] {k} = list len={len(v)}")
                if v and isinstance(v[0], dict):
                    print(f"[debug] {k}[0] keys: {list(v[0].keys())}")
            else:
                print(f"[debug] {k} = {type(v).__name__}: {str(v)[:120]}")
        print("[debug] full response (3000 chars):")
        print(json.dumps(data, indent=2)[:3000])
    except Exception as e:
        print(f"[debug] dump failed: {e}")
    return data, week_end, today


def normalize(data: dict, week_end: date_cls, today: date_cls, store: str) -> dict:
    days_in = data.get("salesForecastDays") or data.get("forecastDays") or []
    week_start = week_end - timedelta(days=6)

    out_days = []
    for i, d in enumerate(days_in[:7]):
        day_date = (week_start + timedelta(days=i)).isoformat()
        ideal = float(d.get("idealHours") or d.get("idealLaborHours") or 0)
        sched = float(d.get("scheduledHours") or d.get("scheduledLaborHours") or 0)
        sales = float(d.get("totalSales") or d.get("netSales") or d.get("forecastSales") or 0)
        out_days.append({
            "date": day_date,
            "day_label": DAY_LABELS[i],
            "ideal_hours": round(ideal, 2),
            "scheduled_hours": round(sched, 2),
            "variance_hours": round(sched - ideal, 2),
            "sales": round(sales, 2),
            "ideal_labor_pct": None,
            "sched_labor_pct": None,
        })

    return {
        "meta": {
            "store": store,
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "scraped_at": datetime.now().isoformat(timespec="seconds"),
            "today": today.isoformat(),
            "source": "teamworx getWbForecastData",
        },
        "days": out_days,
        "totals": {
            "ideal_hours": round(sum(d["ideal_hours"] for d in out_days), 2),
            "scheduled_hours": round(sum(d["scheduled_hours"] for d in out_days), 2),
            "variance_hours": round(sum(d["variance_hours"] for d in out_days), 2),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="2065")
    args = ap.parse_args()

    data, week_end, today = fetch_forecast(args.store)
    payload = normalize(data, week_end, today, args.store)

    out_dir = RAW / args.store / f"week-ending-{week_end.isoformat()}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "ideal_vs_actual.json"
    out_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"[teamworx ideal-vs-actual] wrote {out_file}")
    print(f"  week {payload['meta']['week_start']} → {payload['meta']['week_end']}")
    print(f"  ideal {payload['totals']['ideal_hours']} hrs / "
          f"scheduled {payload['totals']['scheduled_hours']} hrs / "
          f"variance {payload['totals']['variance_hours']} hrs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
