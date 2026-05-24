#!/usr/bin/env python3
"""
Daily dashboard inspector + auto-fix.

Inspects EVERY dashboard data source each run. For any section that is missing
or stale, it runs that section's fix command, then re-checks. Always rebuilds
the derived views (daily numbers, food cost plan, status light). Writes
data/inspect-log.txt, appends anything still broken to data/debug-log.txt, and
regenerates data/status.json.

Designed to run in CI (daily_dashboard.yml) AFTER all scrapers, BEFORE commit —
so a section that failed earlier in the run gets one auto-retry in the same run.

Freshness: green <=1 day, yellow <=3 days, red >3 / missing.
"""
from __future__ import annotations
import json, subprocess, sys, datetime, os
from pathlib import Path

try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PY = sys.executable
STORE = os.environ.get("STORE_ID", "2065")
TODAY = datetime.date.today()

def newest_age_days(paths, prefer_report_date=True):
    """Return (age_in_days, detail) for the freshest of the given files/globs, or (None,'missing')."""
    best = None; detail = "missing"
    for spec in paths:
        for p in (DATA.glob(spec) if any(c in spec for c in "*?[") else [DATA / spec]):
            if not p.exists():
                continue
            d = None
            if prefer_report_date and p.suffix == ".json":
                try:
                    j = json.loads(p.read_text(encoding="utf-8"))
                    rd = (j.get("meta", {}) or {}).get("report_date") or j.get("report_date") or j.get("week_end")
                    if rd:
                        d = datetime.date.fromisoformat(str(rd)[:10])
                except Exception:
                    pass
            if d is None:
                d = datetime.date.fromtimestamp(p.stat().st_mtime)
            age = (TODAY - d).days
            if best is None or age < best:
                best = age; detail = f"{p.name} {d.isoformat()}"
    return best, detail

def newest_dir_age(base_glob):
    """Age of the most recent dated subfolder matching base_glob (e.g. raw/parbrink/2065/2026-*)."""
    dirs = sorted(DATA.glob(base_glob))
    dated = [d for d in dirs if d.is_dir() and d.name[:4].isdigit()]
    if not dated:
        return None, "no dated folder"
    try:
        d = datetime.date.fromisoformat(sorted(d.name for d in dated)[-1])
        return (TODAY - d).days, f"latest {d.isoformat()}"
    except ValueError:
        return None, "unparseable folder"

def run(cmd):
    try:
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=600)
        return r.returncode == 0, (r.stdout or "")[-300:] + (r.stderr or "")[-300:]
    except Exception as e:
        return False, str(e)

# section -> (check fn, fix commands). max_age: green threshold (days).
SECTIONS = [
    {"key":"sales_labor","label":"Sales / Labor (Par Brink)","max":2,
     "check": lambda: newest_dir_age(f"raw/parbrink/{STORE}/2026-*"),
     "fix": [[PY,"scraper/parbrink_email_pickup.py","--store",STORE,"--mode","daily"],
             [PY,"scraper/parbrink_parse_sales_summary.py","--store",STORE],
             [PY,"scraper/parbrink_parse_hourly_sales_labor.py","--store",STORE]]},
    {"key":"crunchtime","label":"CrunchTime metrics","max":2,
     "check": lambda: newest_age_days(["latest.json"]),
     "fix": [[PY,"scraper/scrape_labor_ct.py","--store",STORE]]},
    {"key":"foodcost","label":"Food Cost variance","max":8,
     "check": lambda: newest_dir_age(f"raw/crunchtime/{STORE}/2026-*"),
     "fix": [[PY,"scraper/scrape_cogs.py"]]},
    {"key":"shops","label":"Secret Shops","max":35,
     "check": lambda: newest_dir_age(f"raw/marketforce/{STORE}/2026-*"),
     "fix": [[PY,"scraper/scrape_knowledgeforce_api.py","--store",STORE]]},
    {"key":"compliance","label":"ComplianceMate","max":2,
     "check": lambda: newest_age_days(["compliancemate.json"], prefer_report_date=False),
     "fix": [[PY,"scraper/scrape_compliancemate.py"]]},
]

# Derived views — always rebuilt (cheap, no external creds).
DERIVED = [
    [PY,"scraper/build_daily_numbers.py"],
    [PY,"scraper/build_food_cost_plan.py"],
]

def status_of(age, mx):
    if age is None: return "red"
    if age <= mx: return "green"
    if age <= mx + 2: return "yellow"
    return "red"

def main():
    log = [f"=== Daily inspect {datetime.datetime.now():%Y-%m-%d %H:%M} ==="]
    still_broken = []
    for s in SECTIONS:
        age, detail = s["check"]()
        st = status_of(age, s["max"])
        if st == "green":
            log.append(f"  ✅ {s['label']}: OK ({detail})")
            continue
        log.append(f"  ⚠️ {s['label']}: {st.upper()} ({detail}) — auto-fixing")
        for cmd in s["fix"]:
            ok, out = run(cmd)
            log.append(f"      fix {Path(cmd[1]).name}: {'ok' if ok else 'FAILED'}")
        age2, detail2 = s["check"]()
        st2 = status_of(age2, s["max"])
        if st2 == "green":
            log.append(f"      ✅ FIXED → {detail2}")
        else:
            log.append(f"      ❌ still {st2.upper()} ({detail2})")
            still_broken.append(f"{s['label']}: {st2} ({detail2})")

    for cmd in DERIVED:
        ok, _ = run(cmd)
        log.append(f"  derived {Path(cmd[1]).name}: {'ok' if ok else 'FAILED'}")
        if not ok: still_broken.append(f"{Path(cmd[1]).name} build failed")

    # always refresh the status light last
    run([PY,"scraper/build_status.py"])
    log.append("  status.json refreshed")

    (DATA/"inspect-log.txt").write_text("\n".join(log)+"\n", encoding="utf-8")
    print("\n".join(log))

    if still_broken:
        with (DATA/"debug-log.txt").open("a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] daily_inspect — auto-fix could not resolve:\n")
            for b in still_broken:
                f.write(f"  - {b}\n")
        print(f"\n{len(still_broken)} section(s) still broken after auto-fix — logged to debug-log.txt")
        return 1
    print("\nAll sections green after inspect/auto-fix.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
