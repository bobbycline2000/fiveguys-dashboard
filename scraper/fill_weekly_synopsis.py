#!/usr/bin/env python3
"""
Fill the FG2065 tab of Bri Davis's "Weekly Synopsis.xlsx" (SharePoint) for one
completed Mon-Sun week — pure API, no browser.

    python scraper/fill_weekly_synopsis.py                 # last completed week, DRY RUN
    python scraper/fill_weekly_synopsis.py 11/15/2026      # week ending that Sunday, DRY RUN
    python scraper/fill_weekly_synopsis.py 11/15/2026 --write
    python scraper/fill_weekly_synopsis.py --q 2026 2      # labor % for a quarter (report only)

Run it MONDAY AFTER BOBBY POSTS INVENTORY COUNTS — P&L COGS and the actual-vs-
theoretical variance are count-based. The script refuses to write if the week's
COGS or variance data is missing (counts not posted yet).

SAFETY (Bobby, 2026-11-21: "FG2065 and the 4 weeks... no other stores"):
  * only the worksheet named exactly FG2065 is ever read/written
  * only columns B-E (Week 1-4); F (TOTAL) and G (GOALS) are never touched
  * only the INPUT rows below; a cell whose current content is a formula is skipped
  * one PATCH per cell (surgical) — the workbook is never downloaded/re-uploaded
  * default is DRY RUN; --write is required to change anything

Every formula below was verified 2026-11-21 against the Week 1 (11/2-11/8) and
Week 2 (11/9-11/15) values already in the sheet — all match to the cent / 4 dp.

  Row  Field                  Source / formula
  8    FORECAST SALES         CT forecast, week sum (data/forecast_history.json)
  9    NET SALES              P&L "TOTAL NET SALES"
  11   COGS                   P&L "TOTAL COST OF GOODS SOLD" ($)
  13   Variances              sum(ATC valueVariance) / net   (negative = over theoretical)
  14   SUPPLIES               P&L "TOTAL SUPPLIES" / net
  16   QTD Labor              (QTD hourly - QTD tips + salary*QTDdays/7) * 1.11 / QTD net
  17   QTD COGS               (QTD COGS + QTD supplies) / QTD net
  18   HOURLY LABOR           P&L "6000 - Payroll - Salaries and Wages - Hourly" ($, INCLUDES tips)
  20   TOTAL LABOR            hourly + weekly GM salary
  21   OT HOURS               Time Detail grand total overtimeHours
  22   Labor all in with tax  (hourly - tips + weekly salary) * 1.11 / net
  24   Tips                   Charged tips (Consolidated Sales Entry Summary)
Formula rows the sheet computes itself (never written): 10, 12, 15, 19, 23 + column F.
Row 19 HOURLY LABOR % = (R18 - R24)/NET — that is where tips come back out.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scraper"))
import api_enter_tips as T          # noqa: E402  CT cookie session
import sales_entry_summary as SES   # noqa: E402  charged tips
import update_excel as UX           # noqa: E402  Graph token + throttled calls

NETCHEF = "https://fiveguysfr77.net-chef.com"
SHEET = "FG2065"                    # the ONLY tab this script may touch
WEEK_COLS = ["B", "C", "D", "E"]    # Week 1..4 — the ONLY columns this script may touch
GM_SALARY = 70000.0                 # Bobby's salary (2026-11-21)
WEEKLY_SALARY = GM_SALARY / 52      # 1346.15 — matches TOTAL LABOR in the sheet
TAX_FACTOR = 1.11                   # "taxes and 1.1" — reproduces sheet rows 16 & 22 to 4 dp
LOCATION_ID = 13969                 # KY-2065-Dixie Highway
HOURLY_GL = "6000 - Payroll - Salaries and Wages - Hourly"
INPUT_ROWS = {8, 9, 11, 13, 14, 16, 17, 18, 20, 21, 22, 24}


# ─── CrunchTime pulls ────────────────────────────────────────────────────────
def f(d: dt.date) -> str:
    return d.strftime("%m/%d/%Y")


def pnl(jar, start: dt.date, end: dt.date) -> dict:
    """P&L summary — POST /resource/nc/inventory/profitandloss/summary.
    start/end must be CT post dates (weeks Mon-Sun; months split at the 1st)."""
    body = {"pagingInfo": {"page": 1, "start": 0, "limit": 99999},
            "extraCriteriaMap": {"startDate": f(start), "endDate": f(end)}}
    r = requests.post(f"{NETCHEF}/resource/nc/inventory/profitandloss/summary",
                      json=body, cookies=jar, headers=T.HDR, timeout=90)
    r.raise_for_status()
    out = {}
    for g in (r.json().get("contentMap") or {}).get("gridList") or []:
        k = g.get("glDescriptionCode") or g.get("plSubstructure") or g.get("plGrouping")
        out[k] = g.get("actualValue")
    return out


def atc_variance(jar, start, end):
    """Actual vs Theoretical — POST /resource/actualvstheoretical/location/details.
    Returns (sum of valueVariance $, row count)."""
    body = {"pagingInfo": {"page": 1, "start": 0, "limit": 1000000},
            "extraCriteriaMap": {"startDate": f(start), "endDate": f(end),
                                 "locationIdFilter": LOCATION_ID,
                                 "hierarchyIdFilter": None, "isConsolidated": False}}
    r = requests.post(f"{NETCHEF}/resource/actualvstheoretical/location/details",
                      json=body, cookies=jar, headers=T.HDR, timeout=120)
    r.raise_for_status()
    rows = (r.json().get("rows") or []) if r.text else []
    return sum(x.get("valueVariance") or 0 for x in rows), len(rows)


def ot_hours(jar, mon):
    body = {"pagingInfo": {"page": 1, "start": 0, "limit": 3000},
            "extraCriteriaMap": {"includeAltLocations": False, "excludeManagers": False,
                                 "summarizeBy": "",
                                 "startDate": f"{f(mon)} 00:00:00",
                                 "weekEndingDate": f"{f(mon + dt.timedelta(6))} 00:00:00"}}
    r = requests.post(f"{NETCHEF}/resource/nc/employee/timedetail/summary",
                      json=body, cookies=jar, headers=T.HDR, timeout=90)
    r.raise_for_status()
    ts = (r.json().get("contentMap") or {}).get("totalSummary") or [{}]
    return ts[0].get("overtimeHours") or 0.0


def tips(jar, start, end):
    return SES.pull_charged_tips_sales_entry(jar, start, end)["charged_tips"]


def forecast(mon):
    fh = json.loads((ROOT / "data" / "forecast_history.json").read_text(encoding="utf-8"))
    tot, missing = 0.0, []
    for i in range(7):
        d = (mon + dt.timedelta(i)).isoformat()
        v = fh.get(d)
        if not isinstance(v, dict) or v.get("forecast") is None:
            missing.append(d)
        else:
            tot += v["forecast"]
    return tot, missing


def quarter_start(d: dt.date) -> dt.date:
    return dt.date(d.year, 3 * ((d.month - 1) // 3) + 1, 1)


def labor_all_in(hourly, tip_amt, days, net):
    return (hourly - tip_amt + WEEKLY_SALARY * days / 7) * TAX_FACTOR / net


# ─── build the column ────────────────────────────────────────────────────────
def build_week(jar, sun: dt.date) -> tuple[dict, list]:
    mon = sun - dt.timedelta(6)
    problems = []
    p = pnl(jar, mon, sun)
    net = p.get("TOTAL NET SALES") or 0
    cogs = p.get("TOTAL COST OF GOODS SOLD") or 0
    hourly = p.get(HOURLY_GL) or p.get("TOTAL PAYROLL") or 0
    sup = p.get("TOTAL SUPPLIES") or 0
    if not net:
        problems.append("P&L net sales is 0 — week not closed in CT")
    if not cogs:
        problems.append("P&L COGS is 0 — inventory counts not posted yet")
    var_amt, var_rows = atc_variance(jar, mon, sun)
    if not var_rows:
        problems.append("Actual-vs-theoretical has no rows — counts not posted yet")
    tip_w = tips(jar, mon, sun)
    fc, fc_missing = forecast(mon)
    if fc_missing:
        problems.append(f"forecast missing for {fc_missing}")

    qs = quarter_start(sun)
    q = pnl(jar, qs, sun)
    q_net = q.get("TOTAL NET SALES") or 0
    q_tips = tips(jar, qs, sun)
    q_days = (sun - qs).days + 1

    v = {
        8: round(fc, 2),
        9: round(net, 2),
        11: round(cogs, 2),
        13: round(var_amt / net, 4) if net else None,
        14: round(sup / net, 4) if net else None,
        16: round(labor_all_in(q.get(HOURLY_GL) or 0, q_tips, q_days, q_net), 4) if q_net else None,
        17: round(((q.get("TOTAL COST OF GOODS SOLD") or 0) + (q.get("TOTAL SUPPLIES") or 0)) / q_net, 4) if q_net else None,
        18: round(hourly, 2),
        20: round(hourly + WEEKLY_SALARY, 2),
        21: round(ot_hours(jar, mon), 2),
        22: round(labor_all_in(hourly, tip_w, 7, net), 4) if net else None,
        24: round(tip_w, 2),
    }
    return v, problems


def week_column(sun: dt.date):
    """Week N of the month = Nth Monday of the Monday's month. Returns col letter or None."""
    mon = sun - dt.timedelta(6)
    n = (mon.day - 1) // 7 + 1
    return WEEK_COLS[n - 1] if n <= len(WEEK_COLS) else None, n


# ─── sheet I/O (FG2065 only) ─────────────────────────────────────────────────
def sheet_base(H):
    r = UX.graph_call("GET", f"{UX.GRAPH}/me/drive/sharedWithMe", H)
    r.raise_for_status()
    for it in r.json().get("value", []):
        if (it.get("name") or "").strip().lower() == "weekly synopsis.xlsx":
            rem = it["remoteItem"]
            return (f"{UX.GRAPH}/drives/{rem['parentReference']['driveId']}/items/{rem['id']}"
                    f"/workbook/worksheets('{SHEET}')")
    raise RuntimeError("Weekly Synopsis.xlsx not found in sharedWithMe")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("week_ending", nargs="?", help="Sunday MM/DD/YYYY (default: last completed)")
    ap.add_argument("--write", action="store_true", help="actually write (default dry run)")
    ap.add_argument("--q", nargs=2, type=int, metavar=("YEAR", "Q"), help="quarter labor report")
    a = ap.parse_args()
    jar = T.ensure_session()

    if a.q:
        y, qn = a.q
        s = dt.date(y, 3 * qn - 2, 1)
        e = dt.date(y + (qn == 4), (3 * qn) % 12 + 1, 1) - dt.timedelta(1)
        p = pnl(jar, s, e); net = p["TOTAL NET SALES"]; hourly = p.get(HOURLY_GL) or 0
        tp = tips(jar, s, e); days = (e - s).days + 1; sal = WEEKLY_SALARY * days / 7
        print(f"Q{qn} {y} ({f(s)}-{f(e)}): net ${net:,.2f}  hourly(incl tips) ${hourly:,.2f}  "
              f"tips ${tp:,.2f}  salary ${sal:,.2f}")
        print(f"  hourly % (no tips)         {(hourly - tp) / net:.2%}")
        print(f"  labor + salary, pre-tax    {(hourly - tp + sal) / net:.2%}")
        print(f"  LABOR ALL IN (x{TAX_FACTOR})     {labor_all_in(hourly, tp, days, net):.2%}")
        print(f"  COGS+Supplies              {(p['TOTAL COST OF GOODS SOLD'] + p.get('TOTAL SUPPLIES', 0)) / net:.2%}")
        return 0

    today = dt.date.today()
    sun = (dt.datetime.strptime(a.week_ending, "%m/%d/%Y").date() if a.week_ending
           else today - dt.timedelta(days=today.weekday() + 1))
    if sun.weekday() != 6:
        sys.exit(f"{sun} is not a Sunday")
    col, n = week_column(sun)
    vals, problems = build_week(jar, sun)

    tok = UX.graph_token()
    H = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
    base = sheet_base(H)
    cur = UX.read_range(H, base, "A1:G40")
    print(f"Week {n} ({f(sun - dt.timedelta(6))}-{f(sun)}) -> FG2065 column {col or 'NONE'}")
    if col is None:
        problems.append(f"Week {n} of the month — the sheet only has Week 1-4 columns")
    ci = (ord(col) - 65) if col else None
    for row in sorted(INPUT_ROWS):
        label = cur["values"][row - 1][0]
        have = cur["values"][row - 1][ci] if ci is not None else ""
        fx = str(cur["formulas"][row - 1][ci]) if ci is not None else ""
        flag = "  (FORMULA — skip)" if fx.startswith("=") else ""
        match = "" if have in ("", None) else ("  ✓ matches" if abs(float(have or 0) - float(vals[row] or 0)) < 0.00051 else f"  ≠ sheet has {have}")
        print(f"  {col}{row:<3} {str(label).strip():<24} {vals[row]!s:<12}{match}{flag}")
    if problems:
        print("\nNOT WRITING —", "; ".join(problems))
        return 2
    if not a.write:
        print("\nDRY RUN — nothing written. Re-run with --write to fill.")
        return 0
    wrote = 0
    for row in sorted(INPUT_ROWS):
        if str(cur["formulas"][row - 1][ci]).startswith("="):
            continue
        r = UX.graph_call("PATCH", f"{base}/range(address='{col}{row}')", H,
                          json={"values": [[vals[row]]]})
        r.raise_for_status()
        wrote += 1
    after = UX.read_range(H, base, f"{col}8:{col}24")
    print(f"\nWROTE {wrote} cells to FG2065!{col}. Re-read:",
          [x[0] for x in after["values"]])
    return 0


if __name__ == "__main__":
    sys.exit(main())
