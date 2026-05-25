#!/usr/bin/env python3
"""
District Schedule Analysis — analyzes the UPCOMING week's schedule each GM builds,
for every store in the district, and flags where it's over labor target, running OT,
or thin on coverage. Read-only. No templates required.

Per store (one Teamworx session, switching console location between stores):
  1. switch_location(twx_id)
  2. list_schedules(year) -> pick the upcoming week (next week's weekEndingDate)
  3. get_week_forecast(week_ending) -> per-day forecast sales
  4. get_shift_metrics(week_ending) -> scheduled labor by position/day
  5. compute weekly + per-day labor %, OT, position coverage -> flags
  6. write data/district/<store_id>/schedule_analysis.json

Output is rendered by the "Schedule Analysis" panel on district.html.

Usage:
    python scraper/district_schedule_analysis.py            # all district stores, upcoming week
    python scraper/district_schedule_analysis.py --week-ending 2026-05-31
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, date as date_cls
from pathlib import Path

import teamworx_api as twx

sys.stdout.reconfigure(encoding="utf-8")

ROOT      = Path(__file__).resolve().parents[1]
CONFIG    = ROOT / "config" / "stores.json"
OUT_BASE  = ROOT / "data" / "district"

DEFAULT_TARGET_PCT = 20.0   # flag threshold; per-store override via stores.json "labor_target_pct"
THIN_CREW_HRS      = 10.0   # a day with <this much crew is flagged thin
OVER_TARGET_FLAG   = 2.0    # only flag a day if it's this many pts over target

WD_LABEL = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}


def load_stores() -> list[dict]:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    return cfg.get("stores", [])


def upcoming_week_ending(s, year: int, today: date_cls) -> str | None:
    """Find the weekEndingDate of the next week (the one starting after today).
    Falls back to the latest schedule on file if nothing is strictly in the future."""
    scheds = twx.list_schedules(s, year)
    fut = []
    for sc in scheds:
        we = sc.get("weekEndingDate")
        if not we:
            continue
        try:
            m, d, y = (int(x) for x in we.split("/"))
            we_date = date_cls(y, m, d)
        except Exception:
            continue
        fut.append((we_date, we_date.strftime("%Y-%m-%d")))
    if not fut:
        return None
    fut.sort()
    # next week = smallest week-ending strictly after today
    for we_date, iso in fut:
        if we_date > today:
            return iso
    # nothing in the future -> latest available
    return fut[-1][1]


def analyze_store(s, store: dict, week_ending: str, today_iso: str) -> dict:
    target = float(store.get("labor_target_pct", DEFAULT_TARGET_PCT))
    twx_id = int(store["teamworx_location_id"])
    twx.switch_location(s, twx_id)

    wf = twx.get_week_forecast(s, week_ending)
    sales_by_date = {d["date"]: (d.get("totalSales") or 0)
                     for d in wf.get("salesForecastDays", [])}
    week_start = wf.get("weekStartDate") or ""

    # only count metric rows whose laborDate is one of the 7 days in this week
    valid_dates = set(sales_by_date.keys())
    rows = [r for r in twx.get_shift_metrics(s, week_ending)
            if r.get("laborDate") in valid_dates]

    day: dict[str, dict] = {}
    for r in rows:
        k = r["laborDate"]
        d = day.setdefault(k, {"hrs": 0.0, "val": 0.0, "ot": 0.0, "otv": 0.0, "pos": {}})
        d["hrs"] += r.get("totalHours") or 0
        d["val"] += r.get("totalValue") or 0
        d["ot"]  += r.get("totalOTHours") or 0
        d["otv"] += r.get("overtimeValue") or 0
        pos = r.get("positionName") or "?"
        d["pos"][pos] = round((d["pos"].get(pos, 0) + (r.get("totalHours") or 0)), 1)

    per_day, issues = [], []
    wk_s = wk_v = wk_h = wk_ot = wk_otv = 0.0
    for k in sorted(day):
        wd = WD_LABEL[datetime.strptime(k, "%Y-%m-%d").weekday()]
        sl = sales_by_date.get(k, 0)
        dd = day[k]
        pct = (dd["val"] / sl * 100) if sl else 0
        wk_s += sl; wk_v += dd["val"]; wk_h += dd["hrs"]; wk_ot += dd["ot"]; wk_otv += dd["otv"]
        per_day.append({
            "date": k, "wd": wd, "sales": round(sl), "hrs": round(dd["hrs"], 1),
            "cost": round(dd["val"]), "pct": round(pct, 1), "byPosition": dd["pos"],
        })
        if pct > target + OVER_TARGET_FLAG:
            over = round(dd["val"] - sl * target / 100)
            issues.append({"sev": "high", "day": wd,
                           "msg": f"{wd} labor {pct:.1f}% — ~${over} over {target:.0f}% target"})
        if dd["ot"] > 0:
            issues.append({"sev": "med", "day": wd,
                           "msg": f"{wd} overtime {dd['ot']:.1f}h (${round(dd['otv'])})"})
        crew = dd["pos"].get("2. Crew", 0)
        if 0 < crew < THIN_CREW_HRS:
            issues.append({"sev": "med", "day": wd,
                           "msg": f"{wd} only {crew:.0f}h crew scheduled — thin coverage"})

    wk_pct = (wk_v / wk_s * 100) if wk_s else 0
    return {
        "store_id":    store["store_id"],
        "store_name":  store.get("store_name", store["store_id"]),
        "week_ending": week_ending,
        "week_start":  week_start,
        "target_pct":  target,
        "generated_at": today_iso,
        "week": {
            "fcst_sales": round(wk_s), "sched_cost": round(wk_v),
            "sched_hours": round(wk_h, 1), "labor_pct": round(wk_pct, 1),
            "over_target_dollars": round(wk_v - wk_s * target / 100),
            "ot_hours": round(wk_ot, 1), "ot_value": round(wk_otv),
        },
        "issue_count": len(issues),
        "issues": issues,
        "per_day": per_day,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--week-ending", default=None, help="YYYY-MM-DD; default = upcoming week")
    ap.add_argument("--year", type=int, default=None)
    args = ap.parse_args()

    today = datetime.now(tz=twx.ET).date()
    year = args.year or today.year
    now_iso = datetime.now(tz=twx.ET).isoformat()

    s = twx.load_session()
    stores = load_stores()
    if not stores:
        print("No stores in config/stores.json", file=sys.stderr)
        return 1

    ok = 0
    for store in stores:
        sid = store.get("store_id", "?")
        if "teamworx_location_id" not in store:
            print(f"SKIP {sid}: no teamworx_location_id in config")
            continue
        try:
            twx.switch_location(s, int(store["teamworx_location_id"]))
            we = args.week_ending or upcoming_week_ending(s, year, today)
            if not we:
                print(f"SKIP {sid}: no upcoming schedule found")
                continue
            result = analyze_store(s, store, we, now_iso)
            out_dir = OUT_BASE / sid
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "schedule_analysis.json").write_text(
                json.dumps(result, indent=2), encoding="utf-8")
            wk = result["week"]
            print(f"OK  {sid:5} wk {we}  {wk['labor_pct']}%  "
                  f"${wk['over_target_dollars']} over  {result['issue_count']} issues")
            ok += 1
        except twx.TeamworxAuthError as e:
            print(f"AUTH {sid}: {e}", file=sys.stderr)
            return 2
        except Exception as e:
            print(f"FAIL {sid}: {e}", file=sys.stderr)

    print(f"Done: {ok}/{len(stores)} stores analyzed")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
