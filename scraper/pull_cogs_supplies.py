#!/usr/bin/env python3
"""
Pull COGS % and Supplies % for KY-2065 by week, for the DM Weekly Synopsis
(Brad Davis's SharePoint Weekly Synopsis.xlsx, FG2065 tab).

Usage:
    python pull_cogs_supplies.py                       # last completed Mon-Sun week
    python pull_cogs_supplies.py 2026-06-29 2026-07-05 [more start end pairs...]
    python pull_cogs_supplies.py --out path.json ...   # also save JSON

API notes (confirmed 2026-07-06, catalogued in CRUNCHTIME_API.md):
- registerSales/summary silently IGNORES gte/lte comparisons — only gt/lt apply.
  So we query day-before..day-after and filter exact dates in Python.
- GL categories "Paper" AND "Supplies" are separate GL codes; both roll into the
  CT P&L "Supplies" line. Janitorial is NOT included on the synopsis basis.

SOURCE CAVEAT:
  This is PURCHASE-COST basis (delivery date), not COGS-sold basis.
  The CT P&L computes COGS = Beg Inv + Purchases - End Inv, so a delivery
  straddling a week boundary shifts +/- 2-4 pts week-to-week. Month totals
  are much closer. Calibrate against the CT P&L / COGS Flash email when possible.
"""
import sys, json, datetime
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scraper"))

import requests
from api_query import load_cookies, session_alive, remint, NETCHEF_BASE, HEADERS

GL_URL    = f"{NETCHEF_BASE}/resource/purchasesbygl/location/details"
SALES_URL = f"{NETCHEF_BASE}/resource/sales/sales/registerSales/summary"
LOCATION_ID = 13969

# GL categories included in FOOD COGS (matches CT P&L "Food" category)
COGS_GL = {"Food", "Bread", "Shakes", "Beverage"}
# GL categories included in SUPPLIES % (CT P&L "Supplies" line)
SUPPLIES_GL = {"Paper", "Supplies"}


def default_week():
    """Last completed Mon-Sun week."""
    today = datetime.date.today()
    last_sun = today - datetime.timedelta(days=today.weekday() + 1)
    last_mon = last_sun - datetime.timedelta(days=6)
    return last_mon.isoformat(), last_sun.isoformat()


def to_ct(iso: str) -> str:
    return datetime.date.fromisoformat(iso).strftime("%m/%d/%Y")


def fetch_gl(jar, start: str, end: str) -> list:
    body = {
        "extraCriteriaMap": {
            "startDate": to_ct(start),
            "endDate":   to_ct(end),
            "locationId": LOCATION_ID,
            "hierarchyId": None,
            "isConsolidated": False,
        },
        "pagingInfo": {"page": 1, "start": 0, "limit": 2000},
    }
    r = requests.post(GL_URL, json=body, cookies=jar, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, list):
        return data
    if "rows" in data:
        return data["rows"]
    if "contentMap" in data and "rows" in data["contentMap"]:
        return data["contentMap"]["rows"]
    return []


def fetch_net_sales(jar, start: str, end: str):
    """Total net sales for start..end inclusive. gt/lt window + Python filter."""
    start_d = datetime.date.fromisoformat(start)
    end_d   = datetime.date.fromisoformat(end)
    day_before = (start_d - datetime.timedelta(days=1)).strftime("%m/%d/%Y")
    day_after  = (end_d   + datetime.timedelta(days=1)).strftime("%m/%d/%Y")

    body = {
        "page": 1, "start": 0, "limit": 500,
        "extraFilter": [
            {"type": "date", "value": day_before, "field": "salesDate", "comparison": "gt"},
            {"type": "date", "value": day_after,  "field": "salesDate", "comparison": "lt"},
        ],
    }
    r = requests.post(SALES_URL, json=body, cookies=jar, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    rows = data if isinstance(data, list) else data.get("rows", data.get("contentMap", {}).get("rows", []))

    total, counted = 0.0, 0
    for row in rows:
        sd_str = row.get("salesDate", "")
        try:
            sd = datetime.datetime.strptime(sd_str.split(" ")[0], "%m/%d/%Y").date()
        except ValueError:
            continue
        if not (start_d <= sd <= end_d):
            continue
        val = row.get("totTotalNetSales")
        if val is not None:
            try:
                total += float(val)
                counted += 1
            except (ValueError, TypeError):
                pass
    return round(total, 2) if counted else None


def main():
    args = sys.argv[1:]
    out_path = None
    if "--out" in args:
        i = args.index("--out")
        out_path = Path(args[i + 1])
        args = args[:i] + args[i + 2:]

    if args:
        if len(args) % 2:
            sys.exit("Usage: pull_cogs_supplies.py [--out file.json] [start end ...]")
        weeks = list(zip(args[::2], args[1::2]))
    else:
        weeks = [default_week()]

    jar = load_cookies()
    if not jar or not session_alive(jar):
        print("[auth] cookies stale — re-minting")
        remint()
        jar = load_cookies()
        if not session_alive(jar):
            print("ERROR: session dead after re-mint. Cookies need manual refresh (Bobby needs Chrome).")
            sys.exit(1)
    else:
        print("[auth] session alive")
    print()

    results = []
    for (wk_start, wk_end) in weeks:
        print(f"  Pulling {wk_start} - {wk_end} ...", end=" ", flush=True)
        gl_rows   = fetch_gl(jar, wk_start, wk_end)
        net_sales = fetch_net_sales(jar, wk_start, wk_end)

        gl_by_desc = defaultdict(float)
        for row in gl_rows:
            desc = (row.get("glDescription") or "").strip()
            gl_by_desc[desc] += float(row.get("amount") or 0)

        cogs_dollars     = sum(v for k, v in gl_by_desc.items() if k in COGS_GL)
        supplies_dollars = sum(v for k, v in gl_by_desc.items() if k in SUPPLIES_GL)
        cogs_pct     = round(100 * cogs_dollars / net_sales, 1) if net_sales else None
        supplies_pct = round(100 * supplies_dollars / net_sales, 1) if net_sales else None
        print(f"{len(gl_rows)} GL rows, net_sales={net_sales}")

        results.append({
            "week": f"{wk_start} - {wk_end}",
            "net_sales": net_sales,
            "cogs_dollars": round(cogs_dollars, 2),
            "cogs_pct": cogs_pct,
            "supplies_dollars": round(supplies_dollars, 2),
            "supplies_pct": supplies_pct,
            "gl_breakdown": dict(sorted(gl_by_desc.items(), key=lambda x: -x[1])),
            "source": "purchasesbygl/location/details (delivery-date) + registerSales/summary",
            "caveat": "Purchase-cost basis (delivery date), NOT COGS-sold basis. ~1 delivery lag vs P&L report.",
        })

    print()
    print(f"{'Week':<25}  {'Net Sales':>12}  {'COGS $':>10}  {'COGS %':>8}  {'Supplies $':>11}  {'Supplies %':>10}")
    print("-" * 100)
    for row in results:
        ns = f"${row['net_sales']:,.2f}" if row['net_sales'] else "N/A"
        cp = f"{row['cogs_pct']:.1f}%" if row['cogs_pct'] is not None else "N/A"
        spct = f"{row['supplies_pct']:.1f}%" if row['supplies_pct'] is not None else "N/A"
        print(f"  {row['week']:<23}  {ns:>12}  ${row['cogs_dollars']:>9,.2f}  {cp:>8}  ${row['supplies_dollars']:>10,.2f}  {spct:>10}")
    print()

    for row in results:
        print(f"GL breakdown {row['week']}:")
        for k, v in row["gl_breakdown"].items():
            flag = " <-- COGS" if k in COGS_GL else (" <-- SUPPLIES" if k in SUPPLIES_GL else "")
            print(f"  {k:<25}  ${v:,.2f}{flag}")
        print()

    if out_path:
        out_path.write_text(json.dumps(results, indent=2))
        print(f"[saved] {out_path}")


if __name__ == "__main__":
    main()
