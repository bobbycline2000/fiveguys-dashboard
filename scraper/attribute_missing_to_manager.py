#!/usr/bin/env python3
"""
Join ComplianceMate "missing temps & checklists" items to the Teamworx
manager-on-shift schedule, so every missing item names the manager who was
working that shift.

Inputs:
  --missing   JSON from report_missing_temps_checklists.py (has missing_items[])
  --schedule  JSON from Teamworx daily-roster pull (has schedule[] with
              date / am_manager / pm_manager / shift_change_manager)

Attribution rule (which manager owns a missed item):
  AM_TEMP            -> am_manager
  PM_TEMP           -> pm_manager
  SHIFT_CHANGE_TEMP  -> shift_change_manager (falls back to "AM->PM handoff"
                         naming both am_manager and pm_manager when no distinct
                         mid-shift manager was scheduled)
  CHECKLIST shift AM -> am_manager
  CHECKLIST shift PM -> pm_manager
  CHECKLIST shift N/A:
      Closing / Milkshake / any closing-type task -> pm_manager (closing owns it)
      AM Pre-Shift / opening-type                  -> am_manager
      otherwise                                     -> pm_manager (default owner)

Output JSON adds a "manager" and "manager_basis" field to every missing item,
plus a "by_manager" rollup (count of misses per manager) and a "by_category"
rollup.

Usage:
    python scraper/attribute_missing_to_manager.py \
        --missing ../data/missing_temps_checklists_4wk.json \
        --schedule /path/to/twx_schedule.json \
        --out ../data/missing_temps_checklists_4wk_attributed.json

Built 2026-07-11.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


CLOSING_HINTS = ("clos", "milkshake", "pm ", "9pm", "7pm", "5pm")
OPENING_HINTS = ("am pre", "pre open", "11am", "open")


def attribute(item: dict, sched: dict | None) -> tuple[str, str]:
    """Return (manager, basis) for a single missing item given that day's schedule."""
    if sched is None:
        return ("UNKNOWN (no schedule for date)", "no_schedule")

    am = sched.get("am_manager") or "UNKNOWN"
    pm = sched.get("pm_manager") or "UNKNOWN"
    sc = sched.get("shift_change_manager")
    cat = item["category"]
    shift = item.get("shift", "N/A")
    name = item["task_name"].lower()

    if cat == "AM_TEMP":
        return (am, "am_manager")
    if cat == "PM_TEMP":
        return (pm, "pm_manager")
    if cat == "SHIFT_CHANGE_TEMP":
        if sc:
            return (sc, "shift_change_manager")
        return (f"{am} -> {pm}", "am_pm_handoff (no distinct mid-shift mgr)")
    # CHECKLIST
    if shift == "AM":
        return (am, "am_manager")
    if shift == "PM":
        return (pm, "pm_manager")
    # shift N/A -- infer from task name
    if any(h in name for h in CLOSING_HINTS):
        return (pm, "pm_manager (closing task)")
    if any(h in name for h in OPENING_HINTS):
        return (am, "am_manager (opening task)")
    return (pm, "pm_manager (default owner)")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--missing", required=True)
    p.add_argument("--schedule", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    missing = json.loads(Path(args.missing).read_text())
    schedule_doc = json.loads(Path(args.schedule).read_text())
    sched_by_date = {row["date"]: row for row in schedule_doc.get("schedule", [])}

    by_manager: Counter = Counter()
    by_category: Counter = Counter()
    attributed = []
    for item in missing.get("missing_items", []):
        sched = sched_by_date.get(item["date"])
        mgr, basis = attribute(item, sched)
        row = dict(item)
        row["manager"] = mgr
        row["manager_basis"] = basis
        attributed.append(row)
        by_manager[mgr] += 1
        by_category[item["category"]] += 1

    out = {
        "store": missing.get("store"),
        "window": missing.get("window"),
        "compliancemate_pulled_at": missing.get("pulled_at"),
        "teamworx_pulled_at": schedule_doc.get("pulled_at"),
        "joined_at": None,  # stamped by caller if desired; Date.now unavailable in some envs
        "total_missing": len(attributed),
        "days_fully_compliant": missing.get("days_fully_compliant", []),
        "flagged_lists_never_active": missing.get("flagged_lists_never_active", []),
        "by_manager": dict(by_manager.most_common()),
        "by_category": dict(by_category.most_common()),
        "missing_items": attributed,
        "notes": missing.get("notes"),
        "attribution_note": (
            "manager = the scheduled manager/shift-leader who owned that shift "
            "per Teamworx (am_manager/pm_manager/shift_change_manager). "
            "manager_basis explains which schedule field / inference was used. "
            "On high-coverage days shift_change_manager may list multiple "
            "overlapping names; treat those as 'also on duty', not sole owner."
        ),
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2))
    print(f"WROTE {out_path} -- {len(attributed)} items attributed across "
          f"{len(by_manager)} managers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
