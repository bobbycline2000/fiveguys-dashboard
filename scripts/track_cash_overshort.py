"""Append today's Total Cash Over/Short to a rolling history file.

Reads `data/latest.json` written by scraper/main.py and pulls
`cash.over_short`. The value reported by CrunchTime is:
  - Running total for TODAY's date during open hours.
  - At ~4 AM ET End-of-Day, the value rolls to YESTERDAY's final deposit.

Workflow runs at 5 AM ET — so the value scraped is yesterday's final.
We label the history entry as the BUSINESS DATE = today - 1.

Output: data/cash_overshort_history.json  (list of {business_date, over_short, captured_at})
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LATEST = REPO / "data" / "latest.json"
HISTORY = REPO / "data" / "cash_overshort_history.json"


def load_history() -> list[dict]:
    if not HISTORY.exists():
        return []
    try:
        return json.loads(HISTORY.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_history(rows: list[dict]) -> None:
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    HISTORY.write_text(json.dumps(rows, indent=2), encoding="utf-8")


def main() -> int:
    if not LATEST.exists():
        print(f"[track_cash_overshort] {LATEST} not found — nothing to track.")
        return 0

    try:
        latest = json.loads(LATEST.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[track_cash_overshort] failed to parse latest.json: {e}")
        return 1

    val = latest.get("cash", {}).get("over_short")
    if val is None:
        print("[track_cash_overshort] cash.over_short missing in latest.json.")
        return 0

    business_date = (date.today() - timedelta(days=1)).isoformat()
    captured_at = datetime.now().isoformat(timespec="seconds")

    rows = load_history()
    # Replace any existing row for this business_date (idempotent).
    rows = [r for r in rows if r.get("business_date") != business_date]
    rows.append({
        "business_date": business_date,
        "over_short": float(val),
        "captured_at": captured_at,
    })
    rows.sort(key=lambda r: r["business_date"])
    # Keep last 365 entries
    rows = rows[-365:]
    save_history(rows)
    print(f"[track_cash_overshort] {business_date}: ${val:,.2f}  (n={len(rows)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
