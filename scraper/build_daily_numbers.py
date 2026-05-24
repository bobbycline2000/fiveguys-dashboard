#!/usr/bin/env python3
"""
Build the monthly Daily Numbers sheet for the 2065 dashboard from the same
local source data that update_excel.py writes into the SharePoint workbook:
  - Brink sales_summary.json  (net sales, labor %, labor hours, guests)
  - Brink discount_summary.json (total discounts)
  - ct_sales_summary_history.json (cash over/short, deposit)

Writes data/daily_numbers.json -> rendered by daily_numbers.html.
No SharePoint dependency; runs lights-out in CI alongside the daily pull.
"""
import json, calendar, datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
STORE = "2065"

def load(p):
    try: return json.loads(Path(p).read_text())
    except Exception: return None

def main():
    today = datetime.date.today()
    year, month = today.year, today.month
    month_name = today.strftime("%B %Y")
    pb_dir = DATA / "raw" / "parbrink" / STORE

    # cash over/short + deposit keyed by date
    ct_hist = load(DATA / "ct_sales_summary_history.json") or []
    ct_by_date = {r["business_date"]: r for r in ct_hist if isinstance(r, dict)}

    rows = []
    ndays = calendar.monthrange(year, month)[1]
    for d in range(1, ndays + 1):
        iso = datetime.date(year, month, d).isoformat()
        ss = load(pb_dir / iso / "sales_summary.json")
        ds = load(pb_dir / iso / "discount_summary.json")
        ct = ct_by_date.get(iso)
        if not (ss or ct):
            rows.append({"day": d, "date": iso, "empty": True})
            continue
        rows.append({
            "day": d, "date": iso, "empty": False,
            "net_sales":   (ss or {}).get("net_sales"),
            "labor_pct":   (ss or {}).get("labor_percent"),
            "labor_hours": (ss or {}).get("labor_hours"),
            "guests":      (ss or {}).get("guest_count"),
            "sales_guest": (round((ss["net_sales"]/ss["guest_count"]),2)
                            if ss and ss.get("guest_count") else None),
            "discounts":   (ds or {}).get("total_amount"),
            "cash_os":     (ct or {}).get("over_short"),
        })

    filled = [r for r in rows if not r["empty"] and r.get("net_sales") is not None]
    totals = {
        "net_sales":  round(sum(r["net_sales"] for r in filled), 2) if filled else None,
        "discounts":  round(sum(r["discounts"] for r in filled if r.get("discounts")), 2) if filled else None,
        "labor_hours":round(sum(r["labor_hours"] for r in filled if r.get("labor_hours")), 2) if filled else None,
        "cash_os":    round(sum(r["cash_os"] for r in filled if r.get("cash_os") is not None), 2) if filled else None,
        "avg_labor_pct": round(sum(r["labor_pct"] for r in filled if r.get("labor_pct"))/len([r for r in filled if r.get("labor_pct")]), 2) if filled else None,
        "days_with_data": len(filled),
    }
    out = {"store_id": STORE, "month": month_name,
           "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M ET"),
           "rows": rows, "totals": totals}
    (DATA / "daily_numbers.json").write_text(json.dumps(out, indent=2))
    print(f"daily_numbers.json: {month_name}, {len(filled)} days with data, MTD net=${totals['net_sales']:,.0f}" if totals["net_sales"] else "no data")

if __name__ == "__main__":
    main()
