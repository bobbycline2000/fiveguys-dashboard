#!/usr/bin/env python3
"""
FGU (Schoox) daily alert routing — feeds BOTH the dashboard Team Notes card
(data/team_notes.json) and the daily brief's FGU section reads the same
underlying files directly (see _build_fgu_section in read_outlook_via_gmail.py).

This script is the dashboard-side alert writer. It APPENDS to
data/team_notes.json (role: "alert") rather than owning the whole file —
other scripts (brief generator, ComplianceMate) also write entries into the
same notes list, so this script only ever touches its own FGU-tagged entries,
identified by a fixed set of `from` values, and is safe to re-run daily
(replaces its own entries for today rather than duplicating them).

Alert conditions (any/all may fire on a given day):
  1. Overdue rate ROSE vs the last recorded pull (tracked in
     data/fgu_overdue_history.json, trimmed to the last 60 entries).
  2. A new hire (data/employee_hire_dates.json) is within 7 days of their
     30-day onboarding deadline, or already past it, and still < 100%.
  3. Roster mismatch: FGU accounts not in the active directory (review) and/or
     active employees with no FGU account / stuck at 0% (data/fgu_reconciliation.json,
     written by scraper/reconcile_fgu_roster.py).

Usage: python scraper/fgu_alerts.py
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FGU_FILE = DATA / "fgu_training.json"
RECON_FILE = DATA / "fgu_reconciliation.json"
HIRE_FILE = DATA / "employee_hire_dates.json"
HISTORY_FILE = DATA / "fgu_overdue_history.json"
TEAM_NOTES_FILE = DATA / "team_notes.json"

ONBOARDING_WINDOW_DAYS = 30   # keep in sync with _build_fgu_section in read_outlook_via_gmail.py

# Fixed `from` tags this script owns in team_notes.json — used to replace
# today's entries on re-run without touching notes written by other scripts.
OWNED_FROM_TAGS = {"FGU Overdue Rate", "FGU New Hire Onboarding", "FGU Roster Check"}


def _load(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default


def update_overdue_history(overdue_now, today_iso: str) -> tuple[bool, float | None]:
    """Append today's overdue rate; return (rose, previous_value)."""
    hist = _load(HISTORY_FILE, [])
    if not isinstance(hist, list):
        hist = []
    prev_val = hist[-1]["overdue_rate"] if hist else None
    # Replace today's entry if this is a same-day re-run.
    hist = [h for h in hist if h.get("date") != today_iso]
    if overdue_now is not None:
        hist.append({"date": today_iso, "overdue_rate": overdue_now})
    hist = hist[-60:]
    HISTORY_FILE.write_text(json.dumps(hist, indent=2), encoding="utf-8")
    rose = (prev_val is not None and overdue_now is not None and overdue_now > prev_val)
    return rose, prev_val


def build_alerts(today: date) -> list[dict]:
    alerts: list[dict] = []
    now_str = datetime.now().strftime("%I:%M %p").lstrip("0")  # cross-platform (no %-I on Windows)

    fgu = _load(FGU_FILE, {})
    learners = fgu.get("learners", [])
    stats = fgu.get("stats", {})
    today_iso = today.isoformat()

    # ── 1. Overdue rate rising ──────────────────────────────────────────
    overdue_now = stats.get("coursesOverdueRate")
    rose, prev_val = update_overdue_history(overdue_now, today_iso)
    if rose:
        alerts.append({
            "from": "FGU Overdue Rate",
            "role": "alert",
            "role_label": "FGU / Schoox",
            "time": f"Today {now_str}",
            "body": (f"⚠️ Overdue rate rose {prev_val:.0f}% → {overdue_now:.0f}%. "
                     "Push crew below 100% before it compounds — see Training card."),
        })

    # ── 2. New hires approaching/past their onboarding deadline ────────
    hire_dates = _load(HIRE_FILE, {})
    if isinstance(hire_dates, dict):
        hire_dates = {k: v for k, v in hire_dates.items() if not k.startswith("_")}
    else:
        hire_dates = {}

    learners_by_name = {}
    for l in learners:
        for key in (l.get("full_name"), l.get("name")):
            if key:
                learners_by_name[key] = l

    onboarding_flags = []
    for name, hire_str in hire_dates.items():
        try:
            hd = date.fromisoformat(hire_str)
        except Exception:
            continue
        l = learners_by_name.get(name)
        rate = (l.get("completion_rate") if l else None) or 0
        if l is not None and rate >= 100:
            continue
        deadline = hd + timedelta(days=ONBOARDING_WINDOW_DAYS)
        days_left = (deadline - today).days
        if days_left > 7:
            continue   # not yet within the alert window — avoid 30 days of noise
        status = "PAST DEADLINE" if days_left < 0 else f"{days_left}d left"
        if l is None:
            onboarding_flags.append(f"{name} — NO FGU account yet, onboarding due {deadline.isoformat()} ({status})")
        else:
            onboarding_flags.append(f"{name} — {rate}% done, onboarding due {deadline.isoformat()} ({status})")

    if onboarding_flags:
        alerts.append({
            "from": "FGU New Hire Onboarding",
            "role": "alert",
            "role_label": "FGU / Schoox",
            "time": f"Today {now_str}",
            "body": "🎓 New-hire onboarding at risk: " + "; ".join(onboarding_flags) + ".",
        })

    # ── 3. Roster mismatch (termed-but-listed / active-but-missing) ────
    recon = _load(RECON_FILE, {})
    n_termed = len(recon.get("fgu_not_in_directory", []))
    n_missing = len(recon.get("directory_missing_from_fgu", []))
    if n_termed or n_missing:
        parts = []
        if n_termed:
            parts.append(f"{n_termed} FGU account(s) not matched to the active directory (review for termed crew)")
        if n_missing:
            names = ", ".join(x["full_name"] for x in recon.get("directory_missing_from_fgu", [])[:6])
            more = "" if n_missing <= 6 else f" +{n_missing - 6} more"
            parts.append(f"{n_missing} active crew with no FGU account or stuck at 0% ({names}{more})")
        alerts.append({
            "from": "FGU Roster Check",
            "role": "alert",
            "role_label": "FGU / Schoox",
            "time": f"Today {now_str}",
            "body": "🧾 Roster check: " + "; ".join(parts) + ". See fgu_reconciliation.json for full detail.",
        })

    return alerts


def write_team_notes(alerts: list[dict]) -> None:
    payload = _load(TEAM_NOTES_FILE, {"notes": [], "new_count": 0, "date": date.today().isoformat()})
    notes = payload.get("notes", [])
    # Drop our own previous entries (same-day or stale), then append fresh ones.
    notes = [n for n in notes if n.get("from") not in OWNED_FROM_TAGS]
    notes.extend(alerts)
    payload["notes"] = notes
    payload["new_count"] = len(notes)
    payload["date"] = date.today().isoformat()
    TEAM_NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)
    TEAM_NOTES_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    today = date.today()
    alerts = build_alerts(today)
    write_team_notes(alerts)
    print(f"[fgu-alerts] {len(alerts)} FGU alert(s) written to team_notes.json")
    for a in alerts:
        print(f"    - {a['from']}: {a['body'][:100]}")


if __name__ == "__main__":
    main()
