"""
ct_daily_payroll.py — date-parameterized CrunchTime sales/forecast backfill.

WHY THIS EXISTS
---------------
The Performance Metrics *widget* (and its `/resource/dashboard/performance/metrics`
endpoint) always render whatever week CrunchTime defaults to. On a MONDAY run that is
the upcoming Mon–Sun week, so yesterday (Sunday) is not in the grid at all and every
per-day cell is blank. `main.py::_extract_from_page_text` correctly refuses to read a
Week/Period-to-Date total as a daily value (guard added 2026-08-24) — but that left
Monday runs with no CrunchTime data whatsoever, falling back to the previous day's
cached latest.json and freezing the dashboard a day behind every week.

Probed 2026-09-07: `/resource/dashboard/performance/metrics` ignores `startDate`,
`endDate`, `businessDate` and `weekEndingDate` entirely — it is not date-parameterizable.
`/resource/dailypayrollcontrol/summary` IS, and returns per-day rows under
`contentMap.gridList` (not `data`/`rows`).

RECONCILIATION (2026-09-07, against the known-good 2026-09-05 record in latest.json
and the Par Brink Sales Summary PDF for the same day):
    actualSales      09/05 = 5521.06  == Par Brink net_sales 5521.06   == latest.json 5521
    actualSales      09/06 = 4818.82  == Par Brink net_sales 4818.82
    forecastedSales  09/05 = 5398     == latest.json forecast 5398
    WTD sum 08/31–09/05  = 25921.22   == latest.json net_week 25921
    forecast sum         = 27838      == latest.json forecast_week 27838

PAYROLL IS DELIBERATELY NOT USED. The 2026-07-13 warning in CRUNCHTIME_API.md holds:
this endpoint's payroll figures do not reconcile. Observed 09/06 actualPayroll 1636.68
(33.96%) against Par Brink labor_cost 977.35 (20.28%) — the last day of the week
carries what looks like a weekly salaried allocation. Labor stays on its existing
source chain in wire_dashboard.py (CT API → Par Brink hourly PDF).

Emits only the sales family, in the raw label→{day,week} shape parse_metrics() expects.
"""

import datetime
import json
import subprocess
import sys
from pathlib import Path

import requests

ROOT     = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"

NETCHEF_BASE = "https://fiveguysfr77.net-chef.com"
SUMMARY_URL  = f"{NETCHEF_BASE}/resource/dailypayrollcontrol/summary"
PROBE_URL    = f"{NETCHEF_BASE}/resource/recommended-actions/status"
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json;charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": NETCHEF_BASE,
    "Referer": f"{NETCHEF_BASE}/ncext/modern.ct",
}


def _load_cookies() -> dict:
    f = DATA_DIR / "ct_cookies.json"
    if not f.exists():
        return {}
    return {c["name"]: c["value"] for c in json.loads(f.read_text())}


def _session_alive(jar: dict) -> bool:
    if not jar:
        return False
    try:
        r = requests.get(PROBE_URL, cookies=jar, headers=HEADERS,
                         timeout=15, allow_redirects=False)
        return r.status_code == 200 and "json" in (r.headers.get("content-type") or "").lower()
    except Exception:
        return False


def _remint() -> dict:
    """Re-mint cookies via the Playwright discovery script (same path api_query.py uses)."""
    subprocess.run([sys.executable, str(ROOT / "scraper" / "api_discover.py")],
                   capture_output=True, text=True, timeout=600)
    return _load_cookies()


def _week_bounds(day: datetime.date) -> tuple[datetime.date, datetime.date]:
    """CrunchTime weeks run Monday→Sunday. Return (monday, sunday) containing `day`."""
    monday = day - datetime.timedelta(days=day.weekday())
    return monday, monday + datetime.timedelta(days=6)


def _fmt_money(v) -> str:
    return "" if v is None else f"${v:,.2f}"


def fetch_day(day: datetime.date, jar: dict | None = None) -> dict:
    """
    Return raw metrics (label → {"day","week"}) for `day`, or {} if unavailable.

    "week" is the Monday→`day` running total, matching how the Performance Metrics
    grid reports Week-to-Date.
    """
    jar = jar or _load_cookies()
    if not _session_alive(jar):
        jar = _remint()
        if not _session_alive(jar):
            print("[ct_daily_payroll] no live CrunchTime session — skipping", flush=True)
            return {}

    monday, sunday = _week_bounds(day)
    body = {
        "pagingInfo": {"page": 1, "start": 0, "limit": 75},
        "extraCriteriaMap": {
            "startDate": monday.strftime("%m/%d/%Y 00:00:00"),
            "endDate":   sunday.strftime("%m/%d/%Y 00:00:00"),
        },
    }
    try:
        r = requests.post(SUMMARY_URL, json=body, cookies=jar, headers=HEADERS, timeout=30)
        r.raise_for_status()
        grid = (r.json().get("contentMap") or {}).get("gridList") or []
    except Exception as exc:
        print(f"[ct_daily_payroll] request failed: {exc}", flush=True)
        return {}

    target = day.strftime("%m/%d/%Y")
    rows_upto, day_row = [], None
    for row in grid:
        d = (row.get("date") or "")[:10]
        if not d:
            continue
        try:
            rd = datetime.datetime.strptime(d, "%m/%d/%Y").date()
        except ValueError:
            continue
        if rd <= day:
            rows_upto.append(row)
        if d == target:
            day_row = row

    if day_row is None:
        print(f"[ct_daily_payroll] {target} not present in gridList "
              f"({monday:%m/%d}–{sunday:%m/%d})", flush=True)
        return {}

    net_d = day_row.get("actualSales")
    fc_d  = day_row.get("forecastedSales")
    if net_d is None:
        print(f"[ct_daily_payroll] {target} has no actualSales yet — skipping", flush=True)
        return {}

    def _total(field):
        vals = [x.get(field) for x in rows_upto if x.get(field) is not None]
        return sum(vals) if vals else None

    raw = {
        "Actual Net Sales":  {"day": _fmt_money(net_d), "week": _fmt_money(_total("actualSales"))},
        "Forecasted Sales":  {"day": _fmt_money(fc_d),  "week": _fmt_money(_total("forecastedSales"))},
    }
    print(f"[ct_daily_payroll] {target}: net={_fmt_money(net_d)} "
          f"forecast={_fmt_money(fc_d)} wtd={_fmt_money(_total('actualSales'))}", flush=True)
    return raw


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    d = (datetime.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1
         else datetime.date.today() - datetime.timedelta(days=1))
    print(json.dumps(fetch_day(d), indent=2))
