"""
Roll up daily Par Brink sales_summary.json files into Week / Month / Quarter
period totals so the dashboard's Week, Month, and Quarter tabs show real data
instead of the "—" placeholders.

Reads:   data/raw/parbrink/{store}/<YYYY-MM-DD>/sales_summary.json  (all dates)
Writes:  data/period_rollups.json

Anchor date is the most recent report_date found in the daily JSONs (NOT the
system clock — Par Brink emails arrive overnight for the prior business day,
so the latest JSON is the freshest "today").

Periods (inclusive of the anchor):
  - week    : last 7 days  (anchor − 6 ... anchor)
  - month   : last 30 days
  - quarter : last 90 days

Output schema:
{
  "meta": {"store_id": "2065", "anchor_date": "2026-04-25", "generated": "...",
           "days_seen_total": 2, "days_in_week": 1, "days_in_month": 2, "days_in_quarter": 2},
  "week":    {"net_sales": 5541.0, "gross_sales": 5644.84, "order_count": 207,
              "guest_count": 1014, "labor_cost": 1073.11, "labor_hours": 102.58,
              "labor_percent": 19.37, "sales_per_guest": 5.46, "avg_ticket": 26.77,
              "days": 1},
  "month":   { ... same shape ... },
  "quarter": { ... same shape ... }
}
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_daily(store_id: str) -> list[dict]:
    base = ROOT / "data" / "raw" / "parbrink" / store_id
    if not base.exists():
        return []
    rows = []
    for d in sorted(base.iterdir()):
        if not d.is_dir():
            continue
        jp = d / "sales_summary.json"
        if not jp.exists():
            continue
        try:
            data = json.loads(jp.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"WARN: could not read {jp}: {e}", file=sys.stderr)
            continue
        report_date = data.get("meta", {}).get("report_date") or d.name
        try:
            dt = datetime.strptime(report_date, "%Y-%m-%d").date()
        except ValueError:
            continue
        data["_date"] = dt
        rows.append(data)
    return rows


def rollup(rows: list[dict], anchor: date, window_days: int) -> dict:
    cutoff = anchor - timedelta(days=window_days - 1)
    in_window = [r for r in rows if cutoff <= r["_date"] <= anchor]

    net_sales = sum(r.get("net_sales", 0.0) or 0.0 for r in in_window)
    gross_sales = sum(r.get("gross_sales", 0.0) or 0.0 for r in in_window)
    order_count = sum(r.get("order_count", 0) or 0 for r in in_window)
    guest_count = sum(r.get("guest_count", 0) or 0 for r in in_window)
    labor_cost = sum(r.get("labor_cost", 0.0) or 0.0 for r in in_window)
    labor_hours = sum(r.get("labor_hours", 0.0) or 0.0 for r in in_window)

    labor_percent = round((labor_cost / net_sales) * 100, 2) if net_sales else 0.0
    sales_per_guest = round(net_sales / guest_count, 2) if guest_count else 0.0
    avg_ticket = round(net_sales / order_count, 2) if order_count else 0.0

    return {
        "net_sales": round(net_sales, 2),
        "gross_sales": round(gross_sales, 2),
        "order_count": order_count,
        "guest_count": guest_count,
        "labor_cost": round(labor_cost, 2),
        "labor_hours": round(labor_hours, 2),
        "labor_percent": labor_percent,
        "sales_per_guest": sales_per_guest,
        "avg_ticket": avg_ticket,
        "days": len(in_window),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True)
    args = ap.parse_args()

    rows = load_daily(args.store)
    if not rows:
        print(f"No daily sales_summary.json files found for store {args.store}", file=sys.stderr)
        return 1

    anchor = max(r["_date"] for r in rows)

    week = rollup(rows, anchor, 7)
    month = rollup(rows, anchor, 30)
    quarter = rollup(rows, anchor, 90)

    out = {
        "meta": {
            "store_id": args.store,
            "anchor_date": anchor.isoformat(),
            "generated": datetime.now().isoformat(timespec="seconds"),
            "days_seen_total": len(rows),
            "days_in_week": week["days"],
            "days_in_month": month["days"],
            "days_in_quarter": quarter["days"],
        },
        "week": week,
        "month": month,
        "quarter": quarter,
    }

    out_path = ROOT / "data" / "period_rollups.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"  Anchor: {anchor.isoformat()}  | days seen: {len(rows)}")
    print(f"  Week  ({week['days']}d): ${week['net_sales']:,.2f} net, {week['order_count']} orders, {week['guest_count']} guests")
    print(f"  Month ({month['days']}d): ${month['net_sales']:,.2f} net, {month['order_count']} orders, {month['guest_count']} guests")
    print(f"  Qtr   ({quarter['days']}d): ${quarter['net_sales']:,.2f} net, {quarter['order_count']} orders, {quarter['guest_count']} guests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
