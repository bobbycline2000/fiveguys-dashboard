"""Pull CrunchTime Recent Sales Transactions -> write per-day deposits + over/short.

Endpoint:  POST /resource/sales/sales/registerSales/summary
            (documented in scraper/CRUNCHTIME_API.md)
Returns:   per-register-per-day rows. We aggregate by date.

Output:
  data/ct_sales_summary_history.json — list of {business_date, deposit,
  over_short, gross_sales, net_sales, captured_at}

Pairs with safe_drawer.html — which reads this file to auto-prefill
the "Deposit (from CrunchTime)" and "CT Over/Short" fields.

Run:  python scripts/track_ct_sales_summary.py
"""
from __future__ import annotations

import datetime as _dt
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
NETCHEF = "https://fiveguysfr77.net-chef.com"
PROBE = f"{NETCHEF}/resource/recommended-actions/status"
SUMMARY = f"{NETCHEF}/resource/sales/sales/registerSales/summary"
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json;charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": NETCHEF,
    "Referer": f"{NETCHEF}/ncext/modern.ct",
}
OUTPUT = DATA / "ct_sales_summary_history.json"
DAYS_BACK = 21  # rolling 3-week window


def load_cookies() -> dict:
    f = DATA / "ct_cookies.json"
    if not f.exists():
        return {}
    return {c["name"]: c["value"] for c in json.loads(f.read_text())}


def session_alive(jar: dict) -> bool:
    if not jar:
        return False
    try:
        r = requests.get(PROBE, cookies=jar, headers=HEADERS, timeout=15, allow_redirects=False)
        return r.status_code == 200 and "json" in (r.headers.get("content-type") or "").lower()
    except Exception:
        return False


def remint() -> None:
    """Re-mint cookies via the existing Playwright login flow."""
    print("[ct-sales] cookies stale — re-minting via scraper/api_discover.py", flush=True)
    r = subprocess.run(
        [sys.executable, str(ROOT / "scraper" / "api_discover.py")],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        print(r.stdout); print(r.stderr, file=sys.stderr)
        raise RuntimeError("api_discover.py re-mint failed")


def fetch_summary(jar: dict, start: _dt.date, end: _dt.date) -> list[dict]:
    body = {
        "page": 1, "start": 0, "limit": 200,
        "extraFilter": [
            {"type": "date", "value": start.strftime("%m/%d/%Y"),
             "field": "salesDate", "comparison": "gt"},
            {"type": "date", "value": end.strftime("%m/%d/%Y"),
             "field": "salesDate", "comparison": "lt"},
        ],
    }
    r = requests.post(SUMMARY, json=body, cookies=jar, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    # The response is typically {"rows":[...], "total":N} or {"data":[...]} or
    # a bare list. Handle all three.
    if isinstance(data, list):
        return data
    return data.get("rows") or data.get("data") or []


def _num(v) -> float:
    if v is None or v == "":
        return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _date_only(s: str | None) -> str | None:
    """Normalize CT date strings -> ISO YYYY-MM-DD."""
    if not s:
        return None
    s = s.split(" ")[0]
    if "/" in s:  # mm/dd/yyyy
        m, d, y = s.split("/")
        return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
    if "-" in s:  # already iso-ish
        return s[:10]
    return None


def aggregate(rows: list[dict]) -> dict[str, dict]:
    """Sum across registers per business date.

    CT field names we look for (the API doc says these exist; in case the
    response uses camelCase or differently-named keys, we look for several
    candidates so this works on first call):
      - salesDate / businessDate / date
      - totBankDeposit / bankDeposit / totalBankDeposit / depositAmount
      - totOverShort / overShort / cashOverShort / totalOverShort
      - totGrossSales / grossSales / netSales / totNetSales
    """
    by_date: dict[str, dict] = defaultdict(lambda: {
        "deposit": 0.0, "over_short": 0.0,
        "gross_sales": 0.0, "net_sales": 0.0,
        "book_cash": 0.0,
        "register_count": 0,
    })
    for r in rows:
        d = (_date_only(r.get("salesDate"))
             or _date_only(r.get("businessDate"))
             or _date_only(r.get("date")))
        if not d:
            continue
        bucket = by_date[d]
        bucket["deposit"]     += _num(r.get("totBankDeposits"))
        bucket["over_short"]  += _num(r.get("totOverShort"))
        bucket["gross_sales"] += _num(r.get("totGrossSales"))
        bucket["net_sales"]   += _num(r.get("totTotalNetSales"))
        bucket["book_cash"]   = bucket.get("book_cash", 0.0) + _num(r.get("totBookCash"))
        bucket["register_count"] += 1
    return by_date


def main() -> int:
    jar = load_cookies()
    if not session_alive(jar):
        remint()
        jar = load_cookies()
        if not session_alive(jar):
            print("[ct-sales] re-mint did not produce a live session", file=sys.stderr)
            return 1

    today = _dt.date.today()
    start = today - _dt.timedelta(days=DAYS_BACK)
    print(f"[ct-sales] window {start} -> {today}", flush=True)

    rows = fetch_summary(jar, start, today)
    print(f"[ct-sales] fetched {len(rows)} register-day rows", flush=True)

    # On first call, dump a raw sample so we can verify field names if
    # aggregation comes out empty.
    sample_path = DATA / "ct_sales_summary_sample.json"
    sample_path.write_text(json.dumps(rows[:3], indent=2), encoding="utf-8")

    agg = aggregate(rows)

    out_rows = []
    for d in sorted(agg.keys()):
        v = agg[d]
        out_rows.append({
            "business_date": d,
            "deposit":     round(v["deposit"], 2),
            "over_short":  round(v["over_short"], 2),
            "book_cash":   round(v["book_cash"], 2),
            "gross_sales": round(v["gross_sales"], 2),
            "net_sales":   round(v["net_sales"], 2),
            "register_count": v["register_count"],
            "captured_at": _dt.datetime.now().isoformat(timespec="seconds"),
        })

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(out_rows, indent=2), encoding="utf-8")
    print(f"[ct-sales] wrote {OUTPUT.name} — {len(out_rows)} days", flush=True)

    if out_rows:
        latest = out_rows[-1]
        print(f"[ct-sales] latest {latest['business_date']}: "
              f"deposit ${latest['deposit']:,.2f}  "
              f"O/S ${latest['over_short']:,.2f}", flush=True)
    else:
        print("[ct-sales] WARNING: 0 aggregated rows. "
              "Check data/ct_sales_summary_sample.json for field names.", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
