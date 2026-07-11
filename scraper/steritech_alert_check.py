"""
steritech_alert_check.py — compares the previous committed data/steritech.json
against the freshly-scraped one. If a NEW audit landed (last_audit_date or
latest_score changed) and the new score is below 100 (or below the 90 goal),
appends an alert into data/team_notes.json so the daily brief AND the
dashboard both surface it. No-op if nothing changed, or the new score is a
clean 100 — avoids nagging every month for an already-known result between
Steritech's quarterly visits.

Usage:
    python scraper/steritech_alert_check.py --previous /path/to/pre-scrape-steritech.json
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "data" / "steritech.json"
NOTES = ROOT / "data" / "team_notes.json"


def _short_date_today() -> str:
    now = datetime.now(timezone.utc)
    if sys.platform == "win32":
        return now.strftime("%m/%d").lstrip("0").replace("/0", "/")
    return now.strftime("%-m/%-d")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--previous", required=True,
                     help="Path to the pre-scrape copy of data/steritech.json (captured before the scraper ran)")
    args = ap.parse_args()

    if not CURRENT.exists():
        print("No data/steritech.json produced — nothing to check.")
        return

    new = json.loads(CURRENT.read_text(encoding="utf-8"))
    prev_path = Path(args.previous)
    prev = json.loads(prev_path.read_text(encoding="utf-8")) if prev_path.exists() else {}

    new_score = new.get("latest_score")
    new_date = new.get("last_audit_date")
    prev_date = prev.get("last_audit_date")
    prev_score = prev.get("latest_score")

    changed = (new_date != prev_date) or (new_score != prev_score)
    if not changed:
        print(f"No change since last check (audit {new_date}, score {new_score}). No alert.")
        return

    if new_score is None or new_score >= 100:
        print(f"Score is {new_score!r} (clean/unknown) — no alert needed.")
        return

    severity = "BELOW the 90 goal — CAP required" if new_score < 90 else "below 100"
    body = (
        f"New Steritech assessment {new_date}: {new_score}% ({new.get('status', 'Unknown')}), "
        f"{severity}. {new.get('critical_violations', 0)} critical / {new.get('non_critical', 0)} "
        f"non-critical finding(s). CAP due {new.get('cap_due_date') or 'TBD'}."
    )

    notes_data = {"date": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "new_count": 0, "notes": []}
    if NOTES.exists():
        try:
            notes_data = json.loads(NOTES.read_text(encoding="utf-8"))
        except Exception:
            pass
    notes_data.setdefault("notes", [])
    notes_data["notes"].insert(0, {
        "from": "Steritech",
        "role": "alert",
        "role_label": "Food Safety Audit",
        "time": _short_date_today(),
        "body": body,
    })
    notes_data["new_count"] = notes_data.get("new_count", 0) + 1
    NOTES.write_text(json.dumps(notes_data, indent=2), encoding="utf-8")
    print(f"Alert written to {NOTES}: {body}")


if __name__ == "__main__":
    main()
