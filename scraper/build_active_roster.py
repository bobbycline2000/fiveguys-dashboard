#!/usr/bin/env python3
"""
Who actually works for Store 2065 — straight from CrunchTime punches.

Pulls CrunchTime Employee Time Detail (managers INCLUDED) for the last N weeks
and lists everyone who clocked in, with last day worked, hours, and role.
Anyone with no punch in the window is NOT on the team, whatever older lists say.

Built 2026-11-21 after Bobby found the directory / FGU list / manager scoreboard
still showing people (Nathan, Kasey) who left 5-7+ months ago.

Output: data/active_roster.json
  {generated, window_start, window_end, employees: [{name, ct_name, role,
   positions, last_worked, hours_window, first_seen_in_window}]}

Usage: python scraper/build_active_roster.py [--weeks 5]
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import api_enter_tips as A  # noqa: E402
from build_shop_onshift import pull_week, display, MGR_WORDS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "active_roster.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weeks", type=int, default=5)
    a = ap.parse_args()
    today = dt.date.today()
    this_mon = today - dt.timedelta(days=today.weekday())
    jar = A.ensure_session()
    people: dict = {}
    yday = (today - dt.timedelta(days=1)).isoformat()
    yesterday: dict = {}
    for w in range(a.weeks):
        mon = this_mon - dt.timedelta(weeks=w)
        for row in pull_week(jar, mon):
            ct = (row.get("employeeName") or row.get("name") or "").strip()
            if not ct:
                continue
            ld = row.get("laborDate") or ""  # MM/DD/YYYY
            day = f"{ld[6:10]}-{ld[0:2]}-{ld[3:5]}" if len(ld) == 10 else ""
            pos = (row.get("positionName") or "").strip()
            hrs = float(row.get("totalTime") or 0)
            p = people.setdefault(ct, {"name": display(ct), "ct_name": ct, "positions": set(),
                                       "last_worked": "", "first_seen_in_window": "9999",
                                       "hours_window": 0.0})
            if pos:
                p["positions"].add(pos)
            p["hours_window"] += hrs
            if day == yday:
                y = yesterday.setdefault(ct, {"name": display(ct), "position": pos, "shifts": [], "hours": 0.0})
                y["shifts"].append(f"{row.get('timeIn') or '?'}-{row.get('timeOut') or 'on'}")
                y["hours"] = round(y["hours"] + hrs, 2)
            if day:
                p["last_worked"] = max(p["last_worked"], day)
                p["first_seen_in_window"] = min(p["first_seen_in_window"], day)
    emps = []
    for p in people.values():
        pos = sorted(p["positions"])
        p["positions"] = pos
        p["role"] = "Manager" if any(w in x.lower() for x in pos for w in MGR_WORDS) else "Crew"
        p["hours_window"] = round(p["hours_window"], 1)
        emps.append(p)
    emps.sort(key=lambda x: (x["role"] != "Manager", x["name"]))
    OUT.write_text(json.dumps({
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "window_start": (this_mon - dt.timedelta(weeks=a.weeks - 1)).isoformat(),
        "window_end": today.isoformat(),
        "employees": emps,
        "yesterday_date": yday,
        "yesterday": sorted(yesterday.values(), key=lambda x: x["shifts"][0])}, indent=2), encoding="utf-8")
    print(f"{len(emps)} active ({sum(e['role'] == 'Manager' for e in emps)} managers) -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
