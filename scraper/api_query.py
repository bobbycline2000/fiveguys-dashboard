#!/usr/bin/env python3
"""
Live query: yesterday's Net Sales + Labor % at Store 2065 via the cookie-replay
path. If cached cookies are stale, re-mint by running api_discover.py.

calcId mapping (verified 2026-05-03):
  Sun=1, Mon=2, Tue=3, Wed=4, Thu=5, Fri=6, Sat=7
  i.e. calcId = isoweekday() % 7 + 1
"""

import datetime, json, subprocess, sys
from pathlib import Path

import requests

ROOT     = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"

NETCHEF_BASE = "https://fiveguysfr77.net-chef.com"
METRICS_URL  = f"{NETCHEF_BASE}/resource/dashboard/performance/metrics"
PROBE_URL    = f"{NETCHEF_BASE}/resource/recommended-actions/status"
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json;charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": NETCHEF_BASE,
    "Referer": f"{NETCHEF_BASE}/ncext/modern.ct",
}


def load_cookies():
    f = DATA_DIR / "ct_cookies.json"
    if not f.exists():
        return {}
    return {c["name"]: c["value"] for c in json.loads(f.read_text())}


def session_alive(jar):
    try:
        r = requests.get(PROBE_URL, cookies=jar, headers=HEADERS, timeout=15, allow_redirects=False)
        return r.status_code == 200 and "json" in (r.headers.get("content-type") or "").lower()
    except Exception:
        return False


def remint():
    print("[mint] cookies stale — running api_discover.py to refresh", flush=True)
    result = subprocess.run(
        [sys.executable, str(ROOT / "scraper" / "api_discover.py")],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise RuntimeError("api_discover.py failed")
    print("[mint] re-minted", flush=True)


def fetch_metrics(jar):
    body = {"allLocations": False, "pagingInfo": {"infinite": False}}
    r = requests.post(METRICS_URL, json=body, cookies=jar, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def calcid_for_date(d: datetime.date) -> int:
    # iso: Mon=1..Sun=7  ->  CT calcId: Sun=1, Mon=2..Sat=7
    return d.isoweekday() % 7 + 1


def find_metric(metrics, name):
    for row in metrics:
        if row.get("name") == name:
            return row
    return None


def value_for_calcid(row, calcid):
    if not row:
        return None
    for m in row.get("metrics", []):
        if str(m.get("calcId")) == str(calcid):
            return m.get("value")
    return None


def main():
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    cid_y = calcid_for_date(yesterday)
    cid_t = calcid_for_date(today)
    print(f"today={today.isoformat()} ({today.strftime('%A')}) calcId={cid_t}")
    print(f"yesterday={yesterday.isoformat()} ({yesterday.strftime('%A')}) calcId={cid_y}")

    jar = load_cookies()
    if not jar or not session_alive(jar):
        remint()
        jar = load_cookies()
        if not session_alive(jar):
            raise RuntimeError("re-mint did not produce a live session")
    else:
        print("[probe] cached session alive — skipping Playwright mint")

    print(f"[fetch] POST {METRICS_URL}")
    metrics = fetch_metrics(jar)
    print(f"[fetch] got {len(metrics)} metric rows")

    sales_row = find_metric(metrics, "Actual Net Sales")
    labor_row = find_metric(metrics, "Labor % of Net Sales")

    sales_y = value_for_calcid(sales_row, cid_y)
    labor_y = value_for_calcid(labor_row, cid_y)
    sales_wtd = value_for_calcid(sales_row, "WTD")
    labor_wtd = value_for_calcid(labor_row, "WTD")

    pretty_date = yesterday.strftime("%A %B %d, %Y").replace(" 0", " ")
    print()
    print("=" * 60)
    print(f"  STORE 2065 - {pretty_date}")
    print("=" * 60)
    if sales_y is not None:
        print(f"  Net Sales:        ${float(sales_y):,.2f}")
    else:
        print("  Net Sales:        n/a")
    if labor_y is not None:
        print(f"  Labor % of Sales: {float(labor_y):.2f}%")
    else:
        print("  Labor % of Sales: n/a")
    print()
    if sales_wtd is not None:
        print(f"  Week-to-date Sales:  ${float(sales_wtd):,.2f}")
    if labor_wtd is not None:
        print(f"  Week-to-date Labor%: {float(labor_wtd):.2f}%")
    print("=" * 60)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
