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
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
DASH = HERE.parent
DATA = DASH / "data"
MF = DATA / "raw" / "marketforce" / "2065"
OUT = DATA / "shop_performance.json"

# Who was on shift for each shop = CrunchTime Employee Time Detail
# (shop_onshift_2026.json, built by build_shop_onshift.py). Bobby's rule
# 2026-11-07: CT time detail is the only source for shop names.
ONSHIFT = MF / "shop_onshift_2026.json"
BRINK = DATA / "raw" / "parbrink" / "2065"
LEAD_ROLES = ("shift lead", "shift manager", "manager")  # GM (Bobby) excluded
ROSTER_LOOKBACK_DAYS = 7


def latest_shops_json() -> Path:
    candidates = sorted(MF.glob("*/shops.json"))
    if not candidates:
        raise FileNotFoundError(f"No shops.json under {MF}")
    return candidates[-1]


def load():
    with open(latest_shops_json()) as f:
        shops_doc = json.load(f)
    shops = shops_doc.get("shops", [])
    onshift = json.loads(ONSHIFT.read_text(encoding="utf-8")) if ONSHIFT.exists() else {}
    part = {jid: [p["name"] for p in rec.get("on_shift", [])] for jid, rec in onshift.items()}
    return shops, part


SEPARATED = DATA / "separated_employees.json"


def _key(name: str) -> str:
    """'Rusul K.' / 'Rusul Kadhim' -> 'rusul k' (first name + last initial)."""
    p = name.replace(".", "").split()
    return f"{p[0].lower()} {p[-1][:1].lower()}" if len(p) > 1 else p[0].lower()


def separated_keys() -> set:
    if not SEPARATED.exists():
        return set()
    doc = json.loads(SEPARATED.read_text(encoding="utf-8"))
    return {_key(e["name"]) for e in doc.get("separated", [])}


def current_managers(known_full_names: set) -> list:
    """Shift Leads on the Teamworx roster in the last 7 days who are still active.

    Teamworx gives "First L." — resolve to a full name from CT names we've seen.
    """
    today = date.today()
    gone = separated_keys()
    seen = []
    for i in range(ROSTER_LOOKBACK_DAYS + 1):
        day = (today - timedelta(days=i)).isoformat()
        f = BRINK / day / "weekly_schedule.json"
        if not f.exists():
            continue
        doc = json.loads(f.read_text(encoding="utf-8"))
        for d in doc.get("schedule", {}).values():
            for sh in d.get("shifts", []):
                role = (sh.get("role") or "").lower()
                if any(r in role for r in LEAD_ROLES) and "general" not in role and sh.get("name") not in seen:
                    seen.append(sh["name"])
    out = []
    for short in seen:
        parts = short.replace(".", "").split()
        first, init = parts[0], (parts[-1][:1] if len(parts) > 1 else "")
        if _key(short) in gone:
            continue
        full = next((n for n in sorted(known_full_names)
                     if n.split()[0].lower() == first.lower()
                     and (not init or n.split()[-1][:1].upper() == init.upper())), None)
        out.append(full or short)
    return sorted(out)


def avg(scores):
    if not scores:
        return None
    return round(sum(scores) / len(scores), 1)


def main():
    shops, part = load()

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

    def emp_record(full):
        return {
            "first": full.split()[0],
            "name": full,
            "month_avg": avg(per_emp_month.get(full, [])),
            "month_n": len(per_emp_month.get(full, [])),
            "ytd_avg": avg(per_emp_ytd.get(full, [])),
            "ytd_n": len(per_emp_ytd.get(full, [])),
        }

    mgr_names = current_managers(set(per_emp_ytd.keys()))
    managers = [emp_record(m) for m in mgr_names]
    gone = separated_keys()
    crew_names = sorted(n for n in set(per_emp_ytd.keys()) - set(mgr_names)
                        if _key(n) not in gone)
    crew = [emp_record(c) for c in crew_names]
    crew = [c for c in crew if c["ytd_n"] > 0]
    crew.sort(key=lambda c: (c["ytd_avg"] is None, -(c["ytd_avg"] or 0)))

    latest_shops = []
    for s in sorted(ytd_shops, key=lambda x: x["date"], reverse=True)[:5]:
        jid = str(s["job_id"])
        names = part.get(jid, [])
        full = list(names)
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
