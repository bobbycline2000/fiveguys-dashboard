#!/usr/bin/env python3
"""
Consolidated Sales Entry Summary — Charged Tips pull for KY-2065.

Reverse-engineered 2026-08-03 to replace the wrong-endpoint Charged Tips source
in api_enter_tips.py (which reads `registerSales/summary`'s `chargedTips` field —
same underlying POS-import data, same total, NOT the DM's manual-entry-adjusted
figure some weeks show). This module hits the exact endpoint behind the UI report
"Consolidated Sales Entry Summary" (top Search bar -> type the name -> set
From/To + Hierarchy -> Retrieve), which is the source of truth named in
skills/crunchtime-enter-tips.md Step 1.

Endpoint:
    POST /resource/salesentrysummary/consolidated?_dc=<ms>
    body: {
        "extraCriteriaMap": {
            "startDate": "MM/DD/YYYY",   # Monday of the week
            "endDate":   "MM/DD/YYYY",   # Sunday of the week
            "hierarchyId": 18380,         # New Gator Subs-3-GM30 (Dixie Highway) = KY-2065
            "locationId": 13969,          # KY-2065-Dixie Highway
            "isConsolidated": true
        },
        "pagingInfo": {"page": 1, "start": 0, "limit": 75}
    }
    response: {
        "rows": [{"locationCode": "2065", "locationName": "KY-2065-Dixie Highway",
                   "net": <net sales>, "tips": <CHARGED TIPS - this is the field>,
                   "taxExempt", "gifts", "overrings", "voidsAmount", "voidsQty",
                   "morningCount", "middayCount", "endCount", "avgTrans", ...}],
        "totalSummary": [ ... same shape, locationName="Total:" ... ],
        "total": 1
    }

hierarchyId=18380 is the hierarchyDetailId for "New Gator Subs-3-GM30 (Dixie
Highway)" (confirmed via GET /resource/hierarchy/display) — stable, hardcode it
for 2065. If this is ever extended to another store, walk hierarchy/display for
that store's GM node and swap the id.

⚠ VERIFIED 2026-08-03 — for WE 08/02/2026 (Mon 07/27 -> Sun 08/02) this endpoint,
driven exactly the way the skill describes (same dates, same hierarchy row),
returns Charged Tips = $644.91 — IDENTICAL to registerSales/summary, NOT the
$693.38 the DM reportedly used Monday morning. Tried and ruled out as the cause
of the mismatch (all via this same endpoint / the sibling non-consolidated
"Sales Entry Summary" report, which also returned $644.91 for the same week):
  - Date-range shifts: Sun-Sat week (07/26-08/01) = $633.30; extending End to
    07/26-08/02 = $730.12; 07/28-08/03 = $595.87. None match $693.38.
  - Non-consolidated "Sales Entry Summary" report (per-register/per-day, no
    hierarchy filter, same location) — same $644.91 total, confirms the
    consolidated report isn't under/over-counting vs the raw per-day rows.
  - Per-day registerSales/summary rows for Mon-Sun sum to $644.91 exactly
    (49.04+95.84+94.02+96.14+92.74+120.31+96.82), so the two data sources are
    self-consistent with each other, just not with the DM's remembered number.
This endpoint is a faithful, verified replica of what a human sees clicking
through the exact UI steps in the skill RIGHT NOW. If the live total still
doesn't match what Bobby/the DM expects, the likely explanation is that CT data
for this week changed between the DM's Monday pull and now (a manager
correction/void, or a late-settling register batch) — not a wrong endpoint.
Re-pull close to Monday's tip-entry cutoff and compare; if it still disagrees,
screenshot the live report next to this function's output for Bobby to review.
"""

import datetime as dt
import time

import requests

NETCHEF_BASE = "https://fiveguysfr77.net-chef.com"
SALES_ENTRY_SUMMARY_URL = f"{NETCHEF_BASE}/resource/salesentrysummary/consolidated"

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json;charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": NETCHEF_BASE,
    "Referer": f"{NETCHEF_BASE}/ncext/modern.ct",
}

# KY-2065-Dixie Highway
LOCATION_ID = 13969
# hierarchyDetailId for "New Gator Subs-3-GM30 (Dixie Highway)" — confirmed via
# GET /resource/hierarchy/display 2026-08-03. Stable unless CT restructures the
# New Gator Subs hierarchy tree.
HIERARCHY_ID = 18380


def pull_charged_tips_sales_entry(jar: dict, mon: dt.date, sun: dt.date) -> dict:
    """
    Pull Charged Tips from the Consolidated Sales Entry Summary report for the
    Mon->Sun week (mon, sun are date objects). Returns the full row dict plus a
    top-level 'charged_tips' float for convenience.

    Raises RuntimeError on non-200 or an unexpected/empty response shape.
    """
    body = {
        "extraCriteriaMap": {
            "startDate": mon.strftime("%m/%d/%Y"),
            "endDate": sun.strftime("%m/%d/%Y"),
            "hierarchyId": HIERARCHY_ID,
            "locationId": LOCATION_ID,
            "isConsolidated": True,
        },
        "pagingInfo": {"page": 1, "start": 0, "limit": 75},
    }
    url = f"{SALES_ENTRY_SUMMARY_URL}?_dc={int(time.time() * 1000)}"
    r = requests.post(url, json=body, cookies=jar, headers=HEADERS, timeout=30)
    r.raise_for_status()
    j = r.json()

    rows = j.get("rows") or []
    if not rows:
        raise RuntimeError(
            f"Consolidated Sales Entry Summary returned no rows for "
            f"{body['extraCriteriaMap']['startDate']}-{body['extraCriteriaMap']['endDate']} "
            f"(hierarchyId={HIERARCHY_ID}, locationId={LOCATION_ID}): {j}"
        )

    row = rows[0]
    tips = row.get("tips")
    if tips is None:
        raise RuntimeError(f"row missing 'tips' field: {row}")

    return {
        "charged_tips": float(tips),
        "net_sales": row.get("net"),
        "location_code": row.get("locationCode"),
        "location_name": row.get("locationName"),
        "avg_trans": row.get("avgTrans"),
        "ending_count": row.get("endCount"),
        "raw_row": row,
        "raw_response": j,
        "week_start": body["extraCriteriaMap"]["startDate"],
        "week_end": body["extraCriteriaMap"]["endDate"],
    }


if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path

    ROOT = Path(__file__).parent.parent

    def load_cookies():
        f = ROOT / "data" / "ct_cookies.json"
        return {c["name"]: c["value"] for c in json.loads(f.read_text())}

    if len(sys.argv) > 1:
        sun = dt.datetime.strptime(sys.argv[1], "%m/%d/%Y").date()
    else:
        sun = dt.date.today()
    mon = sun - dt.timedelta(days=6)

    jar = load_cookies()
    result = pull_charged_tips_sales_entry(jar, mon, sun)
    print(f"WE {result['week_end']} (Mon {result['week_start']} -> Sun {result['week_end']})")
    print(f"  Charged Tips: ${result['charged_tips']:,.2f}")
    print(f"  Net Sales:    ${result['net_sales']:,.2f}")
    print(f"  Location:     {result['location_code']} {result['location_name']}")
