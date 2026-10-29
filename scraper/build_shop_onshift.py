#!/usr/bin/env python3
"""
Secret Shop on-shift roster — straight from CrunchTime Employee Time Detail.

For every 2026 shop in the latest shops.json, pulls the CrunchTime Employee
Time Detail (POST /resource/nc/employee/timedetail/summary, managers INCLUDED)
for that shop's Mon-Sun week, and lists everyone who was on the clock at any
point during the shop's visit window (KnowledgeForce "Time In" bucket, or the
meal-period default when the bucket is missing).

Full names come from CrunchTime ("Last, First" -> "First Last"), so there is no
first-name guessing. Role: Manager = Shift Leader / Manager / GM positions.

Output: data/raw/marketforce/2065/shop_onshift_2026.json
  {job_id: {date, meal_period, score, window, on_shift: [{name, ct_name,
            position, role, intervals}]}}

Usage: python scraper/build_shop_onshift.py
"""
import datetime as dt
import glob
import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
import api_enter_tips as A  # noqa: E402  (session + headers)

ROOT = Path(__file__).resolve().parent.parent
MF = ROOT / "data" / "raw" / "marketforce" / "2065"
OUT = MF / "shop_onshift_2026.json"

# Same defaults as scrape_shop_participation.DEFAULT_WIN
DEFAULT_WIN = {"breakfast": (5.0, 11.0), "lunch": (11.0, 15.0),
               "late dinner": (19.0, 23.0), "dinner": (15.0, 22.0)}  # "late dinner" checked first
MGR_WORDS = ("shift leader", "manager", "gm", "general")


def latest_shops() -> list:
    f = sorted(glob.glob(str(MF / "*" / "shops.json")))[-1]
    return json.load(open(f, encoding="utf-8"))["shops"]


def window(shop: dict) -> tuple:
    vw = shop.get("visit_window")
    if vw and len(vw) == 2:
        return float(vw[0]), float(vw[1])
    meal = (shop.get("meal_period") or "").lower()
    for k, v in DEFAULT_WIN.items():
        if k in meal:
            return v
    return (0.0, 23.99)


def hour(s: str):
    if not s or ":" not in s:
        return None
    h, m = s.split(":")[:2]
    return int(h) + int(m) / 60.0


def display(ct_name: str) -> str:
    if "," not in ct_name:
        return ct_name.strip()
    last, first = [p.strip() for p in ct_name.split(",", 1)]
    return f"{first} {last}"


def pull_week(jar, mon: dt.date) -> list:
    sun = mon + dt.timedelta(days=6)
    body = {"pagingInfo": {"page": 1, "start": 0, "limit": 3000},
            "extraCriteriaMap": {"includeAltLocations": False, "excludeManagers": False,
                                 "summarizeBy": "",
                                 "startDate": f"{A.fmt(mon)} 00:00:00",
                                 "weekEndingDate": f"{A.fmt(sun)} 00:00:00"}}
    r = requests.post(f"{A.NETCHEF}/resource/nc/employee/timedetail/summary",
                      json=body, cookies=jar, headers=A.HDR, timeout=60)
    r.raise_for_status()
    rows = r.json().get("contentMap", {}).get("gridList") or []
    return [x for x in rows if x.get("rowType") == "regular"]


def main() -> int:
    shops = [s for s in latest_shops() if s["date"] >= "2026-01-01"]
    jar = A.ensure_session()
    weeks: dict = {}
    out: dict = {}
    for s in sorted(shops, key=lambda x: x["date"]):
        d = dt.date.fromisoformat(s["date"])
        mon = d - dt.timedelta(days=d.weekday())
        if mon not in weeks:
            weeks[mon] = pull_week(jar, mon)
        ct_day = d.strftime("%m/%d/%Y")
        ws, we = window(s)
        people: dict = {}
        for row in weeks[mon]:
            if row.get("laborDate") != ct_day:
                continue
            t_in, t_out = hour(row.get("timeIn")), hour(row.get("timeOut"))
            if t_in is None or t_out is None:
                continue
            if t_out < t_in:
                t_out += 24
            name = row["employeeName"]
            p = people.setdefault(name, {"intervals": [], "position": row.get("positionName") or ""})
            p["intervals"].append([round(t_in, 2), round(t_out, 2)])
        on = []
        for name, p in people.items():
            if any(min(b, we) > max(a, ws) for a, b in p["intervals"]):
                pos = p["position"]
                role = "Manager" if (any(w in pos.lower() for w in MGR_WORDS)
                                     or name.startswith("Cline, Robert")) else "Crew"
                on.append({"name": display(name), "ct_name": name, "position": pos,
                           "role": role, "intervals": sorted(p["intervals"])})
        on.sort(key=lambda x: (x["role"] != "Manager", x["name"]))
        out[s["job_id"]] = {"date": s["date"], "meal_period": s["meal_period"],
                            "score": s["score"], "window": [ws, we],
                            "window_source": "knowledgeforce" if s.get("visit_window") else "meal-default",
                            "on_shift": on}
        print(f"{s['date']} {s['meal_period']:<7} {s['score']:>5}%  {len(on):>2} on shift  "
              + ", ".join(x["name"] for x in on))
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"\nWrote {OUT} — {len(out)} shops, {len(weeks)} CT week pulls")
    return 0


if __name__ == "__main__":
    sys.exit(main())
