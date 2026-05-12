#!/usr/bin/env python3
"""
CrunchTime Labor Pull — Store 2065
=====================================
Pulls labor data for yesterday from the CrunchTime NetChef cookie-replay
API and writes data/labor_today.json.

Endpoints used:
  POST /resource/dashboard/performance/metrics
       → "Labor % of Net Sales", "Actual Labor", "Actual Hours", "Scheduled Hours"
  POST /resource/labor/todays/operatingMetrics
       → 15-min interval breakdown for the hourly bar chart (11A-10P)

Output schema (data/labor_today.json):
  {
    "date":               "YYYY-MM-DD",          # yesterday's business date
    "labor_percent":      19.4,                  # Labor % of Net Sales (yesterday)
    "labor_dollars":      873.0,                 # Actual Labor $ (yesterday)
    "actual_hours":       87.9,                  # Actual Hours (yesterday)
    "scheduled_hours":    82.5,                  # Scheduled Hours (yesterday)
    "avg_hourly_wage":    9.93,                  # derived: labor_dollars / actual_hours
    "labor_percent_wtd":  21.1,                  # WTD Labor %
    "labor_dollars_wtd":  4500.0,                # WTD Actual Labor $
    "actual_hours_wtd":   350.0,                 # WTD Actual Hours
    "hourly_breakdown": [                        # 11A-10P, one row per hour
      {"label": "11A", "hour_24": 11, "labor_percent": 18.2},
      ...
    ],
    "meta": {
      "source": "crunchtime_api",
      "pulled_at": "YYYY-MM-DDTHH:MM:SS",
      "calc_id_yesterday": 3
    }
  }

Auth: reuses cached ct_cookies.json; re-mints via api_discover.py on stale session.
Known failure modes:
  - 401/403/redirect from /resource calls  → cookies stale, api_discover.py re-mints
  - operatingMetrics returns empty list     → store not yet open today; hourly_breakdown empty
  - "Labor % of Net Sales" value is None   → CT hasn't EOD-posted yet; labor_percent = null

Usage:
  python scraper/scrape_labor_ct.py [--store 2065]
"""

import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

import requests

ROOT     = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

NETCHEF_BASE      = "https://fiveguysfr77.net-chef.com"
METRICS_URL       = f"{NETCHEF_BASE}/resource/dashboard/performance/metrics"
OP_METRICS_URL    = f"{NETCHEF_BASE}/resource/labor/todays/operatingMetrics"
PROBE_URL         = f"{NETCHEF_BASE}/resource/recommended-actions/status"

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json;charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": NETCHEF_BASE,
    "Referer": f"{NETCHEF_BASE}/ncext/modern.ct",
}

# calcId mapping: Sun=1, Mon=2, Tue=3, Wed=4, Thu=5, Fri=6, Sat=7
def calcid_for_date(d: datetime.date) -> int:
    return d.isoweekday() % 7 + 1


def load_cookies() -> dict:
    f = DATA_DIR / "ct_cookies.json"
    if not f.exists():
        return {}
    raw = json.loads(f.read_text(encoding="utf-8"))
    # Support both list-of-dicts (Playwright export) and plain dict forms
    if isinstance(raw, list):
        return {c["name"]: c["value"] for c in raw}
    return raw


def session_alive(jar: dict) -> bool:
    try:
        r = requests.get(
            PROBE_URL, cookies=jar, headers=HEADERS, timeout=15, allow_redirects=False
        )
        return r.status_code == 200 and "json" in (r.headers.get("content-type") or "").lower()
    except Exception:
        return False


def remint() -> None:
    print("[mint] cookies stale — running api_discover.py to refresh", flush=True)
    result = subprocess.run(
        [sys.executable, str(ROOT / "scraper" / "api_discover.py")],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise RuntimeError("api_discover.py failed — cannot refresh CT session")
    print("[mint] re-minted", flush=True)


def fetch_metrics(jar: dict) -> list:
    body = {"allLocations": False, "pagingInfo": {"infinite": False}}
    r = requests.post(METRICS_URL, json=body, cookies=jar, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    # Response is either a bare list or {"success":true,"contentMap":{"data":[...]}}
    if isinstance(data, list):
        return data
    return data.get("contentMap", {}).get("data", data) or []


def fetch_operating_metrics(jar: dict) -> list:
    body = {
        "simpleFilterMap": {
            "onlyCurrentTime": {"filterValue": True, "value": True, "filterType": "boolean"}
        },
        "extraCriteriaMap": {"widgetConfig": {"period": 15}},
        "sortInfo": {"sortList": [{"property": "time", "direction": "ASC"}]},
    }
    r = requests.post(OP_METRICS_URL, json=body, cookies=jar, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, list):
        return data
    return data.get("contentMap", {}).get("data", data) or []


def find_metric(rows: list, name: str) -> dict | None:
    for row in rows:
        if row.get("name") == name:
            return row
    return None


def value_for_calcid(row: dict | None, calcid) -> float | None:
    if not row:
        return None
    for m in row.get("metrics", []):
        if str(m.get("calcId")) == str(calcid):
            v = m.get("value")
            return float(v) if v is not None else None
    return None


def build_hourly_breakdown(op_rows: list) -> list:
    """
    Collapse 15-min intervals into hourly buckets (11A-10P) suitable for
    the dashboard's laborData JS array.
    Each returned dict: {label, hour_24, labor_percent}
    """
    if not op_rows:
        return []

    # Group by hour using startTime "HH:MM"
    by_hour: dict[int, list] = {}
    for row in op_rows:
        start = row.get("startTime", "")
        try:
            h = int(start.split(":")[0])
        except (ValueError, IndexError):
            continue
        by_hour.setdefault(h, []).append(row)

    result = []
    for h in sorted(by_hour.keys()):
        if not (11 <= h <= 22):
            continue
        intervals = by_hour[h]
        total_sales = sum(r.get("sales", 0) or 0 for r in intervals)
        total_lab   = sum(r.get("actLab", 0) or 0 for r in intervals)
        if total_sales and total_sales > 0:
            pct = round(total_lab / total_sales * 100, 1)
        else:
            pct = 0.0
        # Hour label: 11A, 12P, 1P, 2P ... 10P
        if h == 12:
            label = "12P"
        elif h < 12:
            label = f"{h}A"
        else:
            label = f"{h - 12}P"
        result.append({"label": label, "hour_24": h, "labor_percent": pct})

    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="Pull labor data from CrunchTime API")
    ap.add_argument("--store", default="2065")
    args = ap.parse_args()

    today     = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    cid_y     = calcid_for_date(yesterday)

    print(f"[labor_ct] business date: {yesterday.isoformat()} "
          f"({yesterday.strftime('%A')}) calcId={cid_y}", flush=True)

    # ── Auth ─────────────────────────────────────────────────────────────────
    jar = load_cookies()
    if not jar or not session_alive(jar):
        remint()
        jar = load_cookies()
        if not session_alive(jar):
            raise RuntimeError("[labor_ct] re-mint did not produce a live session")
    else:
        print("[labor_ct] cached session alive", flush=True)

    # ── Pull performance metrics ──────────────────────────────────────────────
    print(f"[labor_ct] POST {METRICS_URL}", flush=True)
    metrics = fetch_metrics(jar)
    print(f"[labor_ct] got {len(metrics)} metric rows", flush=True)

    labor_pct_row   = find_metric(metrics, "Labor % of Net Sales")
    labor_dol_row   = find_metric(metrics, "Actual Labor")
    actual_hrs_row  = find_metric(metrics, "Actual Hours")
    sched_hrs_row   = find_metric(metrics, "Scheduled Hours")

    labor_pct      = value_for_calcid(labor_pct_row,  cid_y)
    labor_dollars  = value_for_calcid(labor_dol_row,  cid_y)
    actual_hours   = value_for_calcid(actual_hrs_row, cid_y)
    sched_hours    = value_for_calcid(sched_hrs_row,  cid_y)
    # WTD
    labor_pct_wtd  = value_for_calcid(labor_pct_row,  "WTD")
    labor_dol_wtd  = value_for_calcid(labor_dol_row,  "WTD")
    actual_hrs_wtd = value_for_calcid(actual_hrs_row, "WTD")

    avg_wage = None
    if labor_dollars is not None and actual_hours:
        avg_wage = round(labor_dollars / actual_hours, 2)

    print(f"[labor_ct] Labor %: {labor_pct}  Labor $: {labor_dollars}  "
          f"Actual Hrs: {actual_hours}  Sched Hrs: {sched_hours}", flush=True)

    # ── Pull hourly operating metrics ─────────────────────────────────────────
    print(f"[labor_ct] POST {OP_METRICS_URL}", flush=True)
    op_rows = fetch_operating_metrics(jar)
    print(f"[labor_ct] got {len(op_rows)} interval rows", flush=True)
    hourly = build_hourly_breakdown(op_rows)
    print(f"[labor_ct] built {len(hourly)} hourly buckets (11A-10P)", flush=True)

    # ── Write output ──────────────────────────────────────────────────────────
    out = {
        "date":               yesterday.isoformat(),
        "labor_percent":      labor_pct,
        "labor_dollars":      labor_dollars,
        "actual_hours":       actual_hours,
        "scheduled_hours":    sched_hours,
        "avg_hourly_wage":    avg_wage,
        "labor_percent_wtd":  labor_pct_wtd,
        "labor_dollars_wtd":  labor_dol_wtd,
        "actual_hours_wtd":   actual_hrs_wtd,
        "hourly_breakdown":   hourly,
        "meta": {
            "source":              "crunchtime_api",
            "pulled_at":           datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
            "calc_id_yesterday":   cid_y,
        },
    }

    out_path = DATA_DIR / "labor_today.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[labor_ct] wrote {out_path}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main())
