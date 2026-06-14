#!/usr/bin/env python3
"""
Builds data/status.json — a red/yellow/green health snapshot of every dashboard
data source, plus an overall light. Rendered as a status bar on dashboard.html /
district.html and printed at session start.

Freshness rule (daily reports normally land yesterday's data):
  green  = data within 1 day of today (today or yesterday)
  yellow = 2-3 days stale
  red    = 4+ days stale, or the source file is missing
"""
import json, datetime, sys
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TODAY = datetime.date.today()

def as_of_from(path, prefer_report_date=True):
    """Return (date, note) for a source file, or (None, 'missing')."""
    p = DATA / path
    if not p.exists():
        return None, "file missing"
    if prefer_report_date:
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            rd = (d.get("meta", {}) or {}).get("report_date") or d.get("report_date")
            if rd:
                return datetime.date.fromisoformat(rd[:10]), f"report {rd[:10]}"
        except Exception:
            pass
    return datetime.date.fromtimestamp(p.stat().st_mtime), "file updated"

def newest_parbrink(report):
    base = DATA / "raw" / "parbrink" / "2065"
    if not base.exists(): return None, "no brink folder"
    for d in sorted([x for x in base.iterdir() if x.is_dir() and x.name.startswith("2026")], reverse=True):
        f = d / report
        if f.exists():
            try:
                rd = json.loads(f.read_text())["meta"]["report_date"]
                return datetime.date.fromisoformat(rd), f"report {rd}"
            except Exception:
                return datetime.date.fromtimestamp(f.stat().st_mtime), "file updated"
    return None, "no report"

def newest_shops():
    base = DATA / "raw" / "marketforce" / "2065"
    if not base.exists(): return None, "no shop data"
    dates = sorted([x.name for x in base.iterdir() if x.is_dir() and x.name.startswith("2026")], reverse=True)
    if dates:
        return datetime.date.fromisoformat(dates[0]), f"pull {dates[0]}"
    return None, "no shop pull"

def light(as_of):
    if as_of is None: return "red"
    age = (TODAY - as_of).days
    if age <= 1: return "green"
    if age <= 3: return "yellow"
    return "red"

def src(key, label, as_of, note, creds_pending=False):
    if creds_pending:
        return {"key":key,"label":label,"status":"yellow","as_of":None,"detail":"creds pending — stale data"}
    st = light(as_of)
    return {"key":key,"label":label,"status":st,
            "as_of":as_of.isoformat() if as_of else None,
            "detail":(f"{note} ({(TODAY-as_of).days}d ago)" if as_of else note)}

def newest_cogs():
    """Return (date, note) for food cost data. Uses food_cost_plan.json (generated daily
    by build_food_cost_plan.py) as the freshness signal; falls back to scanning
    data/raw/crunchtime/2065/ for the most recent cogs_variance.json with a valid pct.
    cogs_avt_live.json is gitignored and never exists in CI — do not check it."""
    fp = DATA / "food_cost_plan.json"
    if fp.exists():
        try:
            d = json.loads(fp.read_text(encoding="utf-8"))
            # food_cost_plan.json is regenerated daily; use its mtime as the as-of date.
            # The underlying pct may be older (see cogs_pct_week_label) but the pipeline ran.
            return datetime.date.fromtimestamp(fp.stat().st_mtime), "food cost plan updated"
        except Exception:
            pass
    # Fallback: scan raw/crunchtime/2065/ for the most recent cogs_variance.json with pct
    base = DATA / "raw" / "crunchtime" / "2065"
    if base.exists():
        for d in sorted([x for x in base.iterdir() if x.is_dir()],
                        key=lambda p: p.name, reverse=True):
            cv = d / "cogs_variance.json"
            if cv.exists():
                try:
                    snap = json.loads(cv.read_text(encoding="utf-8"))
                    pct = snap.get("cogs_pct_week")
                    if pct is not None:
                        week_end = snap.get("meta", {}).get("week_end", d.name)
                        return datetime.date.fromisoformat(week_end[:10]), f"FP% {pct}% w/e {week_end[:10]}"
                except Exception:
                    continue
        # No snapshot with pct found — return date of most recent file as yellow signal
        for d in sorted([x for x in base.iterdir() if x.is_dir()],
                        key=lambda p: p.name, reverse=True):
            cv = d / "cogs_variance.json"
            if cv.exists():
                return datetime.date.fromisoformat(d.name[:10]), "cogs items only (no pct)"
    return None, "no cogs data"

def main():
    sales_d, sales_n = newest_parbrink("sales_summary.json")
    ct_d, ct_n   = as_of_from("latest.json")
    food_d, food_n = newest_cogs()
    shops_d, shops_n = newest_shops()
    cm_d, cm_n   = as_of_from("compliancemate.json", prefer_report_date=False)
    dn_d, dn_n   = as_of_from("daily_numbers.json", prefer_report_date=False)

    sources = [
        src("sales",      "Sales / Labor",  sales_d, sales_n),
        src("crunchtime", "CrunchTime",     ct_d, ct_n),
        src("foodcost",   "Food Cost %",    food_d, food_n),
        src("shops",      "Secret Shops",   shops_d, shops_n),
        src("compliance", "ComplianceMate", cm_d, cm_n),
        src("daily",      "Daily Numbers",  dn_d, dn_n),
    ]
    rank = {"green":0,"yellow":1,"red":2}
    overall = max((s["status"] for s in sources), key=lambda x: rank[x])
    out = {"generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M ET"),
           "overall": overall, "sources": sources}
    (DATA / "status.json").write_text(json.dumps(out, indent=2))
    dots = "  ".join(f"{ {'green':'🟢','yellow':'🟡','red':'🔴'}[s['status']] } {s['label']}" for s in sources)
    print(f"OVERALL: {overall.upper()}")
    print(dots)

if __name__ == "__main__":
    main()
