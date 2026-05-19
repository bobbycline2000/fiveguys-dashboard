#!/usr/bin/env python3
"""
Read data/boss_calendar.json + data/forecast_by_day.json and produce
data/boss_holiday_alerts.json — manager-facing recommendations for any
holiday-shifted bread week in the next ~6 weeks.

Bread math (matches bread.html):
  Build_To_HB = ceil(window_sales / $986 per tray)
  Build_To_HD = ceil(window_sales / $19,974 per tray)

For a holiday week we shift the missed delivery day's forecast onto adjacent
delivery days (most common BOSS pattern: skipped Mon → bumped Tue substitution).
"""

import datetime as dt
import json
import math
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA = REPO_ROOT / "data"
CAL_PATH = DATA / "boss_calendar.json"
FCAST_PATH = DATA / "forecast_by_day.json"
OUT_PATH = DATA / "boss_holiday_alerts.json"

# Constants from 2065 Q1 PMIX (8-wk, $236K total sales).
HB_DOLLARS_PER_TRAY = 986.0
HD_DOLLARS_PER_TRAY = 19974.0
HB_BAGS_PER_TRAY = 5
HD_BAGS_PER_TRAY = 6

# Sales buffer — matches bread.html ($3K cushion on every delivery window).
# Holiday weeks lift the buffer because CT's forecast averages prior weeks
# and doesn't bump for Memorial Day / July 4 / Labor Day cookout traffic.
SALES_BUFFER_BASE = 3000.0
SALES_BUFFER_HOLIDAY = 5000.0

DELIVERY_WEEKDAYS = {"MON", "WED", "FRI", "SAT"}


def load_json(p: Path):
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def by_date(forecast):
    if not forecast:
        return {}
    return {d["date"]: d for d in forecast.get("days", [])}


def build_to(window_sales: float) -> dict:
    hb = math.ceil(window_sales / HB_DOLLARS_PER_TRAY)
    hd = math.ceil(window_sales / HD_DOLLARS_PER_TRAY)
    return {"hb_trays": hb, "hd_trays": hd}


def main():
    cal = load_json(CAL_PATH)
    fcast = load_json(FCAST_PATH)
    if not cal:
        print("[holiday] no boss_calendar.json — skipping")
        return
    fcast_by_date = by_date(fcast)
    cells_by_date = {c["date"]: c for c in cal.get("cells", []) if c.get("date")}

    alerts = []
    for hw in cal.get("holiday_weeks", []):
        wk_start = hw["week_start_mon"]
        week_days = sorted(hw["days"], key=lambda d: d["date"])
        skipped = hw.get("skipped_delivery_days", [])
        # Find sales forecast sum for skipped days (volume that must redistribute)
        skipped_sales = sum(
            float(fcast_by_date.get(d, {}).get("forecast") or 0.0) for d in skipped
        )

        # For each delivery day in this week, compute current order vs recommended.
        day_recs = []
        delivery_days_in_week = [d for d in week_days if d["weekday"] in DELIVERY_WEEKDAYS and d.get("is_delivery_day")]

        # Spread the skipped volume across delivery days in the week (weighted by their own forecast).
        delivery_forecasts = []
        for d in delivery_days_in_week:
            f = float(fcast_by_date.get(d["date"], {}).get("forecast") or 0.0)
            delivery_forecasts.append((d, f))
        total_delivery_forecast = sum(f for _, f in delivery_forecasts) or 1.0

        for d, own_fcast in delivery_forecasts:
            share = (own_fcast / total_delivery_forecast) * skipped_sales
            raw_window = own_fcast + share
            # Apply the $3K base buffer (matches bread.html), bumped to $5K
            # on holiday-flagged delivery days.
            buffer = SALES_BUFFER_HOLIDAY if d.get("is_holiday_cell") else SALES_BUFFER_BASE
            window_sales = raw_window + buffer
            rec = build_to(window_sales)
            day_recs.append({
                "date": d["date"],
                "weekday": d["weekday"],
                "current_hb": d.get("hb_trays"),
                "current_hd": d.get("hd_trays"),
                "forecast_own": round(own_fcast),
                "redistributed_from_skip": round(share),
                "raw_window_sales": round(raw_window),
                "buffer_applied": int(buffer),
                "window_sales": round(window_sales),
                "recommended_hb": rec["hb_trays"],
                "recommended_hd": rec["hd_trays"],
                "delta_hb": (rec["hb_trays"] - (d.get("hb_trays") or 0)),
                "delta_hd": (rec["hd_trays"] - (d.get("hd_trays") or 0)),
                "is_holiday_cell": d.get("is_holiday_cell", False),
                "is_locked": d.get("is_transit", False) or not d.get("is_adjustable", False),
            })

        # Friendly holiday name guess from date
        holiday_name = guess_holiday_name(skipped, week_days)

        alerts.append({
            "week_start_mon": wk_start,
            "holiday_name": holiday_name,
            "skipped_delivery_days": skipped,
            "skipped_forecast_sales": round(skipped_sales),
            "delivery_day_recommendations": day_recs,
            "headline": _headline(holiday_name, wk_start, skipped, day_recs),
        })

    OUT_PATH.write_text(json.dumps({
        "meta": {
            "generated": dt.datetime.now().isoformat(timespec="seconds"),
            "alerts_count": len(alerts),
        },
        "alerts": alerts,
    }, indent=2), encoding="utf-8")
    print(f"[holiday] wrote {OUT_PATH}  alerts={len(alerts)}")
    for a in alerts:
        print(f"  {a['headline']}")


def guess_holiday_name(skipped_dates, week_days) -> str:
    candidates = []
    for s in skipped_dates:
        d = dt.date.fromisoformat(s)
        candidates.append(d)
    # also try the holiday-flagged days themselves
    for d in week_days:
        if d.get("is_holiday_cell"):
            candidates.append(dt.date.fromisoformat(d["date"]))
    if not candidates:
        return "Holiday"

    for d in candidates:
        # Federal holiday guess
        if d.month == 5 and d.weekday() == 0 and d.day >= 25:
            return "Memorial Day"
        if d.month == 7 and d.day == 4:
            return "Independence Day"
        if d.month == 9 and d.weekday() == 0 and d.day <= 7:
            return "Labor Day"
        if d.month == 11 and d.weekday() == 3 and 22 <= d.day <= 28:
            return "Thanksgiving"
        if d.month == 12 and d.day == 25:
            return "Christmas"
        if d.month == 1 and d.day == 1:
            return "New Year's Day"
    return "Holiday"


def _headline(holiday, wk_start, skipped, day_recs) -> str:
    bumps = [r for r in day_recs if r["delta_hb"] > 0 or r["delta_hd"] > 0]
    parts = [f"{holiday} week ({wk_start})"]
    if skipped:
        parts.append(f"skipped: {', '.join(skipped)}")
    if bumps:
        bp = "; ".join(
            f"{r['weekday']} {r['date']} → {r['recommended_hb']} HB"
            + (f" / {r['recommended_hd']} HD" if r['recommended_hd'] else "")
            + (f"  (Δ +{r['delta_hb']} HB)" if r['delta_hb'] > 0 else "")
            for r in bumps
        )
        parts.append(f"bumps: {bp}")
    return " — ".join(parts)


if __name__ == "__main__":
    main()
