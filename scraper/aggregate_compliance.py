"""
Roll up daily ComplianceMate snapshots into Week / Month / Quarter averages.

Reads:  data/raw/compliancemate/{store}/<YYYY-MM-DD>/compliance.json
Writes: data/compliance_rollups.json

Schema:
{
  "meta": {
    "store_id": "2065",
    "anchor_date": "YYYY-MM-DD",
    "days_seen_total": <int>,
    "days_in_week": <int>,
    "days_in_month": <int>,
    "days_in_quarter": <int>,
    "generated": "ISO timestamp"
  },
  "week":    {"required_pct_avg": 95.4, "lists_at_100_avg": 8.6, "days": 7},
  "month":   {...},
  "quarter": {...}
}

`required_pct_avg` is the mean of each daily snapshot's required-only overall %
(same REQUIRED filter wire_dashboard.py uses for the Compliance KPI). When fewer
than `window_days` of snapshots exist, the average is over whatever IS present.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Keep in sync with wire_dashboard.py _REQUIRED_SRC.
REQUIRED_SRC = {"AM Pre-Shift Check", "11AM: Time and Temp", "Shift Change",
                "3PM: Time and Temp", "5PM: Time and Temp", "PM Pre-Shift Check",
                "7PM: Time and Temp", "9PM: Time and Temp", "Closing Checklist"}


def load_snapshots(store_id: str) -> list[dict]:
    base = ROOT / "data" / "raw" / "compliancemate" / store_id
    if not base.exists():
        return []
    rows = []
    for date_dir in sorted(base.iterdir()):
        if not date_dir.is_dir():
            continue
        snap = date_dir / "compliance.json"
        if not snap.exists():
            continue
        try:
            data = json.loads(snap.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        snap_date_str = data.get("meta", {}).get("date") or date_dir.name
        try:
            snap_date = datetime.strptime(snap_date_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        req = [l for l in data.get("lists", []) if l.get("name") in REQUIRED_SRC]
        if not req:
            continue
        required_pct = sum(l.get("pct", 0) for l in req) / len(req)
        lists_at_100 = sum(1 for l in req if l.get("pct") == 100)
        rows.append({
            "_date": snap_date,
            "required_pct": required_pct,
            "lists_at_100": lists_at_100,
            "required_count": len(req),
        })
    rows.sort(key=lambda r: r["_date"])
    return rows


def rollup(rows: list[dict], anchor: date, window_days: int) -> dict:
    cutoff = anchor - timedelta(days=window_days - 1)
    in_window = [r for r in rows if cutoff <= r["_date"] <= anchor]
    if not in_window:
        return {"required_pct_avg": None, "lists_at_100_avg": None, "days": 0}
    return {
        "required_pct_avg": round(sum(r["required_pct"] for r in in_window) / len(in_window), 1),
        "lists_at_100_avg": round(sum(r["lists_at_100"] for r in in_window) / len(in_window), 1),
        "days": len(in_window),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True)
    args = ap.parse_args()

    rows = load_snapshots(args.store)
    if not rows:
        print(f"No ComplianceMate snapshots found for store {args.store} — nothing to roll up.", file=sys.stderr)
        # Write an empty stub so wire_dashboard can detect "no rollup yet" cleanly.
        out = {
            "meta": {
                "store_id": args.store,
                "anchor_date": None,
                "days_seen_total": 0,
                "days_in_week": 0,
                "days_in_month": 0,
                "days_in_quarter": 0,
                "generated": datetime.now().isoformat(timespec="seconds"),
            },
            "week": {"required_pct_avg": None, "lists_at_100_avg": None, "days": 0},
            "month": {"required_pct_avg": None, "lists_at_100_avg": None, "days": 0},
            "quarter": {"required_pct_avg": None, "lists_at_100_avg": None, "days": 0},
        }
        (ROOT / "data" / "compliance_rollups.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
        return 0

    anchor = max(r["_date"] for r in rows)
    week = rollup(rows, anchor, 7)
    month = rollup(rows, anchor, 30)
    quarter = rollup(rows, anchor, 90)

    out = {
        "meta": {
            "store_id": args.store,
            "anchor_date": anchor.isoformat(),
            "days_seen_total": len(rows),
            "days_in_week": week["days"],
            "days_in_month": month["days"],
            "days_in_quarter": quarter["days"],
            "generated": datetime.now().isoformat(timespec="seconds"),
        },
        "week": week,
        "month": month,
        "quarter": quarter,
    }

    out_path = ROOT / "data" / "compliance_rollups.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"  Anchor: {anchor.isoformat()}, snapshots seen: {len(rows)}")
    print(f"  Week  ({week['days']}d):    {week['required_pct_avg']}% avg, {week['lists_at_100_avg']} lists at 100%")
    print(f"  Month ({month['days']}d):   {month['required_pct_avg']}% avg, {month['lists_at_100_avg']} lists at 100%")
    print(f"  Qtr   ({quarter['days']}d): {quarter['required_pct_avg']}% avg, {quarter['lists_at_100_avg']} lists at 100%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
