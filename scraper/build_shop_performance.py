"""
Build per-employee shop performance averages for the daily brief.

Output: data/shop_performance.json
{
  "as_of": "YYYY-MM-DD",
  "current_month": "YYYY-MM",
  "current_month_label": "May 2026",
  "store_avg_month": 88.3,
  "store_avg_ytd": 86.1,
  "shop_count_month": 4,
  "shop_count_ytd": 18,
  "managers": [
    {"first": "Madison", "name": "Madison Cureton", "month_avg": 92.0, "month_n": 2, "ytd_avg": 88.5, "ytd_n": 9}
  ],
  "crew": [
    {"first": "Lidy", "name": "Lidy Henry", "month_avg": ..., "month_n": ..., "ytd_avg": ..., "ytd_n": ...}
  ],
  "latest_shops": [
    {"date": "2026-05-01", "score": 100.0, "meal_period": "Lunch", "on_shift": ["Bobby Cline", "Lidy Henry", ...]}
  ]
}
"""
import json
import glob
import os
from collections import defaultdict
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
DASH = HERE.parent
DATA = DASH / "data"
MF = DATA / "raw" / "marketforce" / "2065"
OUT = DATA / "shop_performance.json"

MANAGERS = ["Madison", "Vicki", "Kasey", "Nathan"]


def latest_shops_json() -> Path:
    candidates = sorted(MF.glob("*/shops.json"))
    if not candidates:
        raise FileNotFoundError(f"No shops.json under {MF}")
    return candidates[-1]


def load():
    with open(latest_shops_json()) as f:
        shops_doc = json.load(f)
    shops = shops_doc.get("shops", [])
    with open(MF / "participation.json") as f:
        part = json.load(f).get("by_shop", {})
    with open(DATA / "employee_name_map.json") as f:
        name_map = json.load(f)
    return shops, part, name_map


def avg(scores):
    if not scores:
        return None
    return round(sum(scores) / len(scores), 1)


def main():
    shops, part, name_map = load()

    today = date.today()
    current_month = today.strftime("%Y-%m")
    current_month_label = today.strftime("%B %Y")

    ytd_shops = [s for s in shops if str(s.get("date", "")).startswith("2026-")]
    month_shops = [s for s in ytd_shops if str(s.get("date", "")).startswith(current_month)]

    per_emp_ytd = defaultdict(list)
    per_emp_month = defaultdict(list)

    for s in ytd_shops:
        jid = str(s["job_id"])
        score = s.get("score")
        if score is None:
            continue
        names = part.get(jid, [])
        for first in names:
            per_emp_ytd[first].append(score)
            if str(s["date"]).startswith(current_month):
                per_emp_month[first].append(score)

    def emp_record(first):
        return {
            "first": first,
            "name": name_map.get(first, f"NAME_UNRESOLVED ({first})"),
            "month_avg": avg(per_emp_month.get(first, [])),
            "month_n": len(per_emp_month.get(first, [])),
            "ytd_avg": avg(per_emp_ytd.get(first, [])),
            "ytd_n": len(per_emp_ytd.get(first, [])),
        }

    managers = [emp_record(m) for m in MANAGERS]
    crew_firsts = sorted(set(per_emp_ytd.keys()) - set(MANAGERS))
    crew = [emp_record(c) for c in crew_firsts]
    crew = [c for c in crew if c["ytd_n"] > 0]
    crew.sort(key=lambda c: (c["ytd_avg"] is None, -(c["ytd_avg"] or 0)))

    latest_shops = []
    for s in sorted(ytd_shops, key=lambda x: x["date"], reverse=True)[:5]:
        jid = str(s["job_id"])
        names = part.get(jid, [])
        full = [name_map.get(n, n) for n in names]
        latest_shops.append({
            "date": s["date"],
            "score": s.get("score"),
            "meal_period": s.get("meal_period"),
            "on_shift": full,
        })

    doc = {
        "as_of": today.strftime("%Y-%m-%d"),
        "current_month": current_month,
        "current_month_label": current_month_label,
        "store_avg_month": avg([s["score"] for s in month_shops if s.get("score") is not None]),
        "store_avg_ytd": avg([s["score"] for s in ytd_shops if s.get("score") is not None]),
        "shop_count_month": len(month_shops),
        "shop_count_ytd": len(ytd_shops),
        "managers": managers,
        "crew": crew,
        "latest_shops": latest_shops,
    }

    OUT.write_text(json.dumps(doc, indent=2))
    print(f"Wrote {OUT}")
    print(f"  Store: month {doc['store_avg_month']}% ({doc['shop_count_month']} shops) | YTD {doc['store_avg_ytd']}% ({doc['shop_count_ytd']} shops)")
    print(f"  Managers tracked: {len(managers)} | Crew tracked: {len(crew)}")


if __name__ == "__main__":
    main()
