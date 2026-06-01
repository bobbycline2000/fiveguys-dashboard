"""Pull June 2025 daily net sales for KY-2065 from CT registerSales/summary.

Used to pre-fill column C ("Last Year") on the June 2026 FG Daily Report.xlsx.
"""
import datetime as dt
import json, subprocess, sys
from pathlib import Path
import requests

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
NETCHEF = "https://fiveguysfr77.net-chef.com"
HDR = {
    "Accept": "application/json",
    "Content-Type": "application/json;charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": NETCHEF,
    "Referer": f"{NETCHEF}/ncext/next.ct",
}
PROBE_URL = f"{NETCHEF}/resource/recommended-actions/status"


def load_cookies():
    f = DATA / "ct_cookies.json"
    if not f.exists(): return {}
    return {c["name"]: c["value"] for c in json.loads(f.read_text())}


def session_alive(jar):
    if not jar: return False
    try:
        r = requests.get(PROBE_URL, cookies=jar, headers=HDR, timeout=15, allow_redirects=False)
        return r.status_code == 200 and "json" in r.headers.get("content-type","")
    except Exception:
        return False


def ensure_jar():
    jar = load_cookies()
    if session_alive(jar):
        print("[probe] session alive", flush=True)
        return jar
    print("[mint] cookies stale — running api_discover.py", flush=True)
    res = subprocess.run([sys.executable, str(ROOT/"scraper"/"api_discover.py")],
                         capture_output=True, text=True)
    if res.returncode != 0:
        print(res.stdout); print(res.stderr, file=sys.stderr)
        raise RuntimeError("re-mint failed")
    jar = load_cookies()
    if not session_alive(jar):
        raise RuntimeError("re-mint did not produce a live session")
    return jar


def fmt(d): return d.strftime("%m/%d/%Y")


def pull_range(jar, start, end):
    """Per-day rows from registerSales/summary between start..end inclusive."""
    body = {"page":1,"start":0,"limit":500,"extraFilter":[
        {"type":"date","value":fmt(start - dt.timedelta(days=1)),"field":"salesDate","comparison":"gt"},
        {"type":"date","value":fmt(end   + dt.timedelta(days=1)),"field":"salesDate","comparison":"lt"},
    ]}
    r = requests.post(f"{NETCHEF}/resource/sales/sales/registerSales/summary",
                      json=body, cookies=jar, headers=HDR, timeout=60)
    r.raise_for_status()
    rows = r.json().get("rows") or []
    inc = [x for x in rows if fmt(start) <= x["salesDate"][:10] <= fmt(end)]
    return inc


def main():
    jar = ensure_jar()
    start = dt.date(2025, 6, 1)
    end   = dt.date(2025, 6, 30)
    rows = pull_range(jar, start, end)
    print(f"[ct] {len(rows)} rows returned for {fmt(start)}..{fmt(end)}")

    # Aggregate per business_date (sum across registers if multiple rows/day)
    agg = {}
    for r in rows:
        d = r["salesDate"][:10]  # MM/DD/YYYY
        net = float(r.get("totTotalNetSales") or r.get("totNetSales") or r.get("netSales") or 0)
        agg[d] = agg.get(d, 0.0) + net

    # Build day-of-month → net_sales for June 2025
    out = {}
    cur = start
    while cur <= end:
        key = fmt(cur)
        out[cur.day] = round(agg.get(key, 0.0), 2)
        cur += dt.timedelta(days=1)

    DATA.mkdir(exist_ok=True)
    target = DATA / "ly_june_2025_2065.json"
    target.write_text(json.dumps(out, indent=2))
    print(f"[ok] wrote {target}")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
