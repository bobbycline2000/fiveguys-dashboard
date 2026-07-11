#!/usr/bin/env python3
"""
4-week "missing temps & checklists" report for a ComplianceMate store.

Loops compliancemate_api.get_list_completions() over every date in a window,
classifies each sub-100%-required list into one of Bobby's 4 report buckets
(AM_TEMP / PM_TEMP / SHIFT_CHANGE_TEMP / CHECKLIST), and writes a single JSON
report.

Usage:
    python scraper/report_missing_temps_checklists.py --store 2065 \
        --start 2026-06-14 --end 2026-07-11 \
        --out ../data/missing_temps_checklists_4wk.json

Built 2026-07-11. See scraper/COMPLIANCEMATE_API.md "Historical range pulls
and list-name taxonomy" section for the categorization rationale.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date as date_cls, datetime, timedelta, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compliancemate_api as cm  # noqa: E402

ET = timezone(timedelta(hours=-4))

# ─── List-name → report-category taxonomy ──────────────────────────────────
# Discovered from data/compliancemate.json (2026-07-11 pull) — full known
# account list roster for store 2065. ComplianceMate does not natively split
# lists into Bobby's 4 buckets, so this mapping is our interpretation:
#
#   AM_TEMP           -> 11AM: Time and Temp (opening/morning temp round)
#   SHIFT_CHANGE_TEMP -> Shift Change, 1PM: Time and Temp, 3PM: Time and Temp
#                         (midday temp rounds bridging the shift change)
#   PM_TEMP           -> 5PM / 7PM / 9PM: Time and Temp (closing/evening rounds)
#   CHECKLIST         -> AM Pre-Shift Check, PM Pre-Shift Check, Pre Open,
#                         Closing, Closing Checklist, Friday Milkshake
#                         Cleaning Check (Fridays only)
#
# EXCLUDED from missing-item detection (periodic/audit lists, cadence not
# confirmed daily — flagging every day they show <100% would false-positive
# on lists that are only due weekly/monthly/quarterly):
#   Weekly Store Inspection, Delivery Check, Temperature Sample,
#   Calibration Test, Operational Spot Check, Battery Swap Checklist, MMCCA

AM_TEMP_LISTS = {"11AM: Time and Temp"}
SHIFT_CHANGE_LISTS = {"Shift Change", "1PM: Time and Temp", "3PM: Time and Temp"}
PM_TEMP_LISTS = {"5PM: Time and Temp", "7PM: Time and Temp", "9PM: Time and Temp"}
CHECKLIST_DAILY = {"AM Pre-Shift Check", "PM Pre-Shift Check"}
CHECKLIST_WEEKLY_BY_DOW = {
    "Friday Milkshake Cleaning Check": "Friday",
}
# Lists with unconfirmed cadence -- observed sitting at a constant 0%|0% in
# spot checks (2026-06-16, 2026-07-11), which looks more like an inactive/
# superseded list (e.g. "Pre Open"/"Closing"/"Closing Checklist" look like
# legacy names predating "AM/PM Pre-Shift Check") than a genuine daily miss.
# Cross-day activity check below decides, per list, whether to include it.
EXCLUDED_PERIODIC = {
    "Weekly Store Inspection", "Delivery Check", "Temperature Sample",
    "Calibration Test", "Operational Spot Check", "Battery Swap Checklist",
    "MMCCA", "Pre Open", "Closing", "Closing Checklist",
}


import re

MILKSHAKE_RE = re.compile(r"^(\w+) Milkshake Cleaning Check$")


def classify(name: str, day_of_week: str) -> tuple[str, str] | None:
    """Return (category, shift) or None if list is out of scope for the report."""
    if name in AM_TEMP_LISTS:
        return ("AM_TEMP", "AM")
    if name in SHIFT_CHANGE_LISTS:
        return ("SHIFT_CHANGE_TEMP", "SHIFT_CHANGE")
    if name in PM_TEMP_LISTS:
        return ("PM_TEMP", "PM")
    if name in CHECKLIST_DAILY:
        shift = "AM" if "AM" in name or "Pre Open" in name else (
            "PM" if "PM" in name or "Clos" in name else "N/A"
        )
        return ("CHECKLIST", shift)
    m = MILKSHAKE_RE.match(name)
    if m:
        return ("CHECKLIST", "N/A")  # day-named milkshake check, always in-scope
    if name in EXCLUDED_PERIODIC:
        return None  # cadence not confirmed daily; excluded, see notes -- handled
        # separately via the "never active in window" cross-day check
    # Unknown list name never seen before -- surface it, don't silently drop.
    return ("CHECKLIST", "N/A")


def status_for_pct(pct: int) -> str:
    if pct <= 0:
        return "MISSED"
    return "INCOMPLETE"


def daterange(start: date_cls, end: date_cls):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--store", required=True, choices=list(cm.STORES.keys()))
    p.add_argument("--start", required=True, help="YYYY-MM-DD")
    p.add_argument("--end", required=True, help="YYYY-MM-DD")
    p.add_argument("--out", required=True, help="Output path (relative to cwd or absolute)")
    args = p.parse_args()

    cm._load_env()
    user = os.environ["COMPLIANCEMATE_USERNAME"]
    pwd = os.environ["COMPLIANCEMATE_PASSWORD"]
    cfg = cm.STORES[args.store]

    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 cm-api-client/1.0"})
    cm.login(s, user, pwd)
    csrf = cm.get_csrf_token(s, cfg["group_id"])

    start = datetime.strptime(args.start, "%Y-%m-%d").date()
    end = datetime.strptime(args.end, "%Y-%m-%d").date()

    unknown_lists_seen = set()
    day_errors = []
    raw_days = {}  # date -> result dict (from all_list_completions pull)
    periodic_max_pct: dict[str, int] = {}  # list name -> max required_pct seen in window

    # Pass 1: pull every day with report_type=all_list_completions so we see the
    # FULL list roster (Time-and-Temp, AM/PM Pre-Shift Check, Shift Change, and
    # the periodic/audit lists) -- not just the "required-only" subset, which
    # was found (2026-07-11) to silently omit Pre-Shift Check and Shift Change
    # entirely even on days they were completed at 100%.
    for d in daterange(start, end):
        d_str = d.strftime("%Y-%m-%d")
        dow = d.strftime("%A")
        try:
            result = cm.get_list_completions(
                s, cfg["group_id"], cfg["location_id"], d_str, csrf=csrf,
                report_type="all_list_completions",
            )
        except Exception as e:  # noqa: BLE001
            day_errors.append({"date": d_str, "error": str(e)})
            print(f"ERROR {d_str}: {e}", file=sys.stderr)
            continue

        raw_days[d_str] = result
        for lst in result["lists"]:
            if lst["name"] in EXCLUDED_PERIODIC:
                periodic_max_pct[lst["name"]] = max(
                    periodic_max_pct.get(lst["name"], 0), lst["required_pct"]
                )

        print(f"OK  {d_str} ({dow}) -- {len(result['lists'])} lists, "
              f"overall {result['overall_required_pct']}% req", file=sys.stderr)

    # Lists that show 0% on EVERY day of the window are flagged separately
    # rather than folded into missing_items as 28 individual "MISSED" rows --
    # a constant 0% across 4 straight weeks is much more likely an inactive/
    # unused list in this store's CM config than a genuine daily miss. Bobby
    # should confirm; if these ARE meant to be daily, re-run with them promoted.
    never_active_periodic = {
        name for name in EXCLUDED_PERIODIC if periodic_max_pct.get(name, 0) == 0
    }

    # Pass 2: build missing_items + days_fully_compliant from the pulled data.
    missing_items = []
    days_fully_compliant = []
    for d_str, result in raw_days.items():
        dow = datetime.strptime(d_str, "%Y-%m-%d").strftime("%A")
        day_had_gap = False
        for lst in result["lists"]:
            name = lst["name"]
            req_pct = lst["required_pct"]
            if name in EXCLUDED_PERIODIC and name in never_active_periodic:
                continue  # flagged separately, not per-day noise
            if name in EXCLUDED_PERIODIC:
                # active-at-some-point periodic list -- treat gaps as CHECKLIST
                if req_pct < 100:
                    day_had_gap = True
                    missing_items.append({
                        "date": d_str, "day_of_week": dow, "category": "CHECKLIST",
                        "shift": "N/A", "task_name": name,
                        "status": status_for_pct(req_pct),
                        "required_pct": req_pct, "all_pct": lst["all_pct"],
                    })
                continue
            classification = classify(name, dow)
            if classification is None:
                continue
            category, shift = classification
            known = (AM_TEMP_LISTS | SHIFT_CHANGE_LISTS | PM_TEMP_LISTS
                     | CHECKLIST_DAILY | EXCLUDED_PERIODIC)
            if name not in known and not MILKSHAKE_RE.match(name):
                unknown_lists_seen.add(name)
            if req_pct < 100:
                day_had_gap = True
                missing_items.append({
                    "date": d_str,
                    "day_of_week": dow,
                    "category": category,
                    "shift": shift,
                    "task_name": name,
                    "status": status_for_pct(req_pct),
                    "required_pct": req_pct,
                    "all_pct": lst["all_pct"],
                })

        if not day_had_gap:
            days_fully_compliant.append(d_str)

    missing_items.sort(key=lambda x: (x["date"], x["category"]))
    days_fully_compliant.sort()

    today_str = datetime.now(tz=ET).strftime("%Y-%m-%d")
    notes_parts = [
        "Categorization is our interpretation of ComplianceMate's list names into "
        "AM_TEMP / PM_TEMP / SHIFT_CHANGE_TEMP / CHECKLIST -- CM has no native "
        "4-bucket taxonomy. See scraper/COMPLIANCEMATE_API.md for the mapping table.",
        "LATE status is not derivable from the list_completions endpoint (no "
        "per-entry timestamps vs due-time) -- only MISSED (0%) and INCOMPLETE "
        "(1-99%) are reported. A true LATE distinction would require drilling "
        "into each list's /responses?date=...&list_id=... page per entry.",
        "Lists with unconfirmed cadence (Weekly Store Inspection, Delivery Check, "
        "Temperature Sample, Calibration Test, Operational Spot Check, Battery "
        "Swap Checklist, MMCCA, Pre Open, Closing, Closing Checklist) that sat at "
        "0% on EVERY day of the 4-week window are EXCLUDED from missing_items "
        "(see flagged_lists_never_active) -- a constant 0% across 28 straight "
        "days is more consistent with an inactive/superseded CM list than a "
        "genuine daily miss; if any of these should be daily-required, tell "
        "Bobby's CM Professor and they get promoted into missing_items on re-run. "
        "Any of these lists that DID show activity somewhere in the window are "
        "included as CHECKLIST items on the days they fell short.",
    ]
    if today_str in [d.strftime("%Y-%m-%d") for d in daterange(start, end)]:
        notes_parts.append(
            f"{today_str} is TODAY -- that day's checklists are still in "
            "progress at pull time, not a final end-of-day snapshot. Re-pull "
            "after close for a final read on today."
        )
    if unknown_lists_seen:
        notes_parts.append(
            "Unknown list names encountered (not in the known taxonomy, "
            "defaulted to CHECKLIST/N/A): " + ", ".join(sorted(unknown_lists_seen))
        )
    if day_errors:
        notes_parts.append(
            f"{len(day_errors)} day(s) failed to pull: "
            + ", ".join(e["date"] for e in day_errors)
        )

    report = {
        "store": args.store,
        "window": {"start": args.start, "end": args.end},
        "pulled_at": datetime.now(tz=ET).isoformat(),
        "missing_items": missing_items,
        "days_fully_compliant": days_fully_compliant,
        "flagged_lists_never_active": sorted(never_active_periodic),
        "notes": " | ".join(notes_parts),
        "day_errors": day_errors,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))
    print(f"WROTE {out_path} -- {len(missing_items)} missing items, "
          f"{len(days_fully_compliant)} fully compliant days", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
