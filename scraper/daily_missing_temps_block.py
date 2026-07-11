#!/usr/bin/env python3
"""
Daily "Missing Time & Temps & Checklists" block for the morning brief.

Lights-out single-day path: for one target date (default = yesterday ET) it
  1. pulls that day's ComplianceMate list completions (all_list_completions),
     classifies every sub-100% list into AM_TEMP / PM_TEMP / SHIFT_CHANGE_TEMP
     / CHECKLIST (reusing report_missing_temps_checklists.classify),
  2. pulls that day's Teamworx daily roster and derives the AM / PM / shift-change
     manager on duty,
  3. attributes each missing item to the manager who owned that shift
     (reusing attribute_missing_to_manager.attribute),
  4. writes data/daily_missing_temps.json and prints a markdown block for the
     brief.

Runs with no browser — pure requests via compliancemate_api + teamworx_api.

Usage:
    python scraper/daily_missing_temps_block.py --store 2065          # yesterday
    python scraper/daily_missing_temps_block.py --store 2065 --date 2026-07-10
    python scraper/daily_missing_temps_block.py --store 2065 --markdown-only

Built 2026-07-11. Feeds the outlook-daily-pull-7am brief. See
COMPLIANCEMATE_API.md + TEAMWORX_API.md for the underlying endpoints.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compliancemate_api as cm  # noqa: E402
import teamworx_api as twx  # noqa: E402
from report_missing_temps_checklists import (  # noqa: E402
    classify, status_for_pct, EXCLUDED_PERIODIC,
)
from attribute_missing_to_manager import attribute  # noqa: E402

ET = timezone(timedelta(hours=-4))

CAT_LABEL = {
    "AM_TEMP": "AM temp",
    "PM_TEMP": "PM temp",
    "SHIFT_CHANGE_TEMP": "Shift-change temp",
    "CHECKLIST": "Checklist",
}

# Lists that live in the CM "periodic/audit" bucket in the 4-week report but
# are confirmed ACTIVE daily/weekly tasks (they showed genuine completion
# activity across the 2026-06-14..07-11 window). A single day lacks the
# cross-day context the 4-week script uses to detect this, so we pin them here:
#   Closing Checklist -> nightly (biggest recurring gap, 12/28 days) -> include
#                        at any <100% on every day
#   Milkshake Pump Cleaning Check -> only ever surfaced on Wednesdays in the
#                        window -> weekly, gated to Wednesday only (avoids
#                        false-flagging it 6 days a week in a DAILY brief)
ACTIVE_DAILY_EXTRA = {"Closing Checklist"}
WEEKLY_BY_DOW_EXTRA = {"Milkshake Pump Cleaning Check": "Wednesday"}


# ─── ComplianceMate: single-day missing items ──────────────────────────────
def cm_missing_for_day(store: str, day: str) -> list[dict]:
    cm._load_env()
    user = os.environ["COMPLIANCEMATE_USERNAME"]
    pwd = os.environ["COMPLIANCEMATE_PASSWORD"]
    cfg = cm.STORES[store]

    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 cm-api-client/1.0"})
    cm.login(s, user, pwd)
    csrf = cm.get_csrf_token(s, cfg["group_id"])

    result = cm.get_list_completions(
        s, cfg["group_id"], cfg["location_id"], day, csrf=csrf,
        report_type="all_list_completions",
    )
    dow = datetime.strptime(day, "%Y-%m-%d").strftime("%A")
    items = []
    for lst in result["lists"]:
        name = lst["name"]
        req_pct = lst["required_pct"]
        # Confirmed-active nightly checklist (e.g. Closing Checklist): include
        # at any <100%, even a flat 0% (that IS the miss we care about).
        if name in ACTIVE_DAILY_EXTRA:
            if req_pct < 100:
                items.append({
                    "date": day, "day_of_week": dow, "category": "CHECKLIST",
                    "shift": "N/A", "task_name": name,
                    "status": status_for_pct(req_pct),
                    "required_pct": req_pct, "all_pct": lst["all_pct"],
                })
            continue
        # Weekly-cadence checklist gated to its day-of-week (e.g. Milkshake on
        # Wednesdays) — only a miss when it's actually due that day.
        if name in WEEKLY_BY_DOW_EXTRA:
            if WEEKLY_BY_DOW_EXTRA[name] == dow and req_pct < 100:
                items.append({
                    "date": day, "day_of_week": dow, "category": "CHECKLIST",
                    "shift": "N/A", "task_name": name,
                    "status": status_for_pct(req_pct),
                    "required_pct": req_pct, "all_pct": lst["all_pct"],
                })
            continue
        # skip periodic/audit lists that never carry a daily cadence
        if name in EXCLUDED_PERIODIC:
            # only include if it actually showed activity (>0%) but fell short
            if 0 < req_pct < 100:
                items.append({
                    "date": day, "day_of_week": dow, "category": "CHECKLIST",
                    "shift": "N/A", "task_name": name,
                    "status": status_for_pct(req_pct),
                    "required_pct": req_pct, "all_pct": lst["all_pct"],
                })
            continue
        classification = classify(name, dow)
        if classification is None:
            continue
        category, shift = classification
        if req_pct < 100:
            items.append({
                "date": day, "day_of_week": dow, "category": category,
                "shift": shift, "task_name": name,
                "status": status_for_pct(req_pct),
                "required_pct": req_pct, "all_pct": lst["all_pct"],
            })
    return items


# ─── Teamworx: single-day manager derivation ───────────────────────────────
def twx_managers_for_day(day: str) -> dict:
    """Return {date, day_of_week, am_manager, pm_manager, shift_change_manager}."""
    s = twx.load_session()
    roster = twx.get_daily_roster(s, day)
    shifts = roster.get("dayData", {}).get("shifts", [])
    mgr_shifts = [
        sh for sh in shifts
        if any(k in (sh.get("positionName") or "").lower()
               for k in ("manager", "shift leader"))
    ]
    dow = datetime.strptime(day, "%Y-%m-%d").strftime("%A")
    out = {"date": day, "day_of_week": dow,
           "am_manager": None, "pm_manager": None, "shift_change_manager": None}
    if not mgr_shifts:
        return out

    def in_ms(sh):
        try:
            return int(sh.get("inTime") or 0)
        except (TypeError, ValueError):
            return 0

    def out_ms(sh):
        try:
            return int(sh.get("outTime") or 0)
        except (TypeError, ValueError):
            return 0

    am_shift = min(mgr_shifts, key=in_ms)
    pm_shift = max(mgr_shifts, key=out_ms)
    out["am_manager"] = am_shift.get("employeeName")
    out["pm_manager"] = pm_shift.get("employeeName")
    mids = [sh.get("employeeName") for sh in mgr_shifts
            if sh is not am_shift and sh is not pm_shift]
    if mids:
        out["shift_change_manager"] = " & ".join(m for m in mids if m)
    return out


def build_markdown(day: str, dow: str, items: list[dict], sched: dict) -> str:
    if not items:
        return (f"### 🌡️ Missing Time & Temps & Checklists — {dow} {day}\n"
                f"✅ All temps and checklists complete. Clean day.\n")
    lines = [f"### 🌡️ Missing Time & Temps & Checklists — {dow} {day}",
             f"**{len(items)} missed/incomplete** "
             f"(AM mgr: {sched.get('am_manager') or '—'} · "
             f"PM mgr: {sched.get('pm_manager') or '—'})", ""]
    for it in sorted(items, key=lambda x: (x["category"], x["task_name"])):
        label = CAT_LABEL.get(it["category"], it["category"])
        pct = "" if it["status"] == "MISSED" else f" ({it['required_pct']}%)"
        lines.append(
            f"- **{label}: {it['task_name']}** — {it['status']}{pct} → "
            f"**{it['manager']}**"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--store", default="2065", choices=list(cm.STORES.keys()))
    p.add_argument("--date", help="YYYY-MM-DD (default: yesterday ET)")
    p.add_argument("--out", default=None,
                   help="JSON output path (default: ../data/daily_missing_temps.json)")
    p.add_argument("--markdown-only", action="store_true",
                   help="Print only the markdown block, no JSON write")
    args = p.parse_args()

    if args.date:
        day = args.date
    else:
        day = (datetime.now(tz=ET) - timedelta(days=1)).strftime("%Y-%m-%d")
    dow = datetime.strptime(day, "%Y-%m-%d").strftime("%A")

    items = cm_missing_for_day(args.store, day)
    sched = twx_managers_for_day(day)
    for it in items:
        mgr, basis = attribute(it, sched)
        it["manager"] = mgr
        it["manager_basis"] = basis

    md = build_markdown(day, dow, items, sched)
    print(md)

    if not args.markdown_only:
        out_path = Path(args.out) if args.out else (
            Path(__file__).resolve().parent.parent / "data" / "daily_missing_temps.json"
        )
        payload = {
            "store": args.store,
            "date": day,
            "day_of_week": dow,
            "generated_at": datetime.now(tz=ET).isoformat(),
            "schedule": sched,
            "missing_count": len(items),
            "missing_items": items,
            "markdown": md,
        }
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2))
        print(f"WROTE {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
