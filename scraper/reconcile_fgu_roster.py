#!/usr/bin/env python3
"""
Reconcile the FGU (Schoox) learner roster against the ACTIVE 2065 employee
directory — the "FGU accounts are not current" fix.

Two mismatch classes:
  (a) fgu_not_in_directory  — a Schoox learner whose name doesn't match any
      active 2065 employee. Usually a termed employee whose FGU account was
      never deactivated. Bobby should ignore/archive these in Schoox.
  (b) directory_missing_from_fgu — an active 2065 employee with no matching
      Schoox learner record, OR a learner record present but stuck at 0%
      (account exists, training never started). These are "not current"
      in the other direction: onboarding/training was never set up or never
      opened.

Sources:
  - scripts/build_employee_directory.py  EMPLOYEES  (first-name, phone, status)
    — the single source of truth for who's active at 2065.
  - data/employee_name_map.json          first_name -> "Full Name"
    — resolver used across the dashboard (shops, tips, etc). Reused here to
      expand directory first-names to full names for the FGU-name match.
  - data/fgu_training.json               learners[] (from scraper/scrape_fgu.py)

Output: data/fgu_reconciliation.json
    {
      "generated_at": iso,
      "fgu_pulled_at": <pulled_at from fgu_training.json, or null>,
      "active_employee_count": N,
      "fgu_learner_count": N,
      "fgu_not_in_directory": [ {"full_name": ..., "completion_rate": ...} ],
      "directory_missing_from_fgu": [ {"first_name": ..., "full_name": ..., "reason": "no_account"|"zero_percent", "completion_rate": ...|null} ],
    }

Usage: python scraper/reconcile_fgu_roster.py
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DIRECTORY_SCRIPT = ROOT / "scripts" / "build_employee_directory.py"
NAME_MAP_FILE = DATA / "employee_name_map.json"
FGU_FILE = DATA / "fgu_training.json"
OUT_FILE = DATA / "fgu_reconciliation.json"


def _norm(name: str) -> str:
    return re.sub(r"[^a-z]", "", (name or "").lower())


# The crew phone directory (build_employee_directory.py) intentionally excludes
# management who don't need a line in the crew phone list. Never flag these as
# "termed" just because they're absent from EMPLOYEES.
KNOWN_MANAGEMENT_EXCLUDE = {"Robert Cline"}   # Bobby — GM, always active

# Nickname/legal-name pairs the resolver doesn't yet carry (surfaced by this
# script's first pass 2026-07-11 — same person, not a roster mismatch).
# Confirm with Bobby, then add the canonical entry to employee_name_map.json
# and delete the pair here.
SUSPECTED_NICKNAME_PAIRS = [
    ("Kenzie", "Mykenize Milledge"),
]


def load_active_employees() -> list[str]:
    """Parse EMPLOYEES tuples straight from the source script (single source
    of truth per new-hire-auto-add.md / agents-auto-update.md) rather than
    importing the module (avoids executing its side effects)."""
    src = DIRECTORY_SCRIPT.read_text(encoding="utf-8")
    m = re.search(r"EMPLOYEES\s*=\s*\[(.*?)\]", src, re.DOTALL)
    if not m:
        raise RuntimeError("Could not find EMPLOYEES list in build_employee_directory.py")
    rows = re.findall(r'\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\)', m.group(1))
    return [name for name, _phone, status in rows if "active" in status.lower()]


def load_name_map() -> dict:
    if NAME_MAP_FILE.exists():
        return json.loads(NAME_MAP_FILE.read_text(encoding="utf-8"))
    return {}


def main() -> None:
    active_first_names = load_active_employees()
    name_map = load_name_map()

    # Expand each active directory entry to its likely full name.
    # Entries that are already "First Last" (disambiguated in EMPLOYEES) pass through.
    directory_full_names = {}   # full_name -> first_name (directory key)
    for first in active_first_names:
        full = name_map.get(first, first)
        if full.startswith("UNRESOLVED"):
            full = first  # keep the nickname itself as the matchable name
        directory_full_names[full] = first

    if not FGU_FILE.exists():
        print(f"[reconcile] {FGU_FILE} not found — run scrape_fgu.py first", file=sys.stderr)
        sys.exit(1)

    fgu = json.loads(FGU_FILE.read_text(encoding="utf-8"))
    learners = fgu.get("learners", [])
    pulled_at = fgu.get("pulled_at")

    learners_by_full = {_norm(l.get("full_name")): l for l in learners}
    learners_by_first = {}
    for l in learners:
        learners_by_first.setdefault(_norm(l.get("name")), []).append(l)

    nickname_map = {a: b for a, b in SUSPECTED_NICKNAME_PAIRS}

    matched_learner_keys: set[str] = set()   # normalized full_name of matched learners
    directory_missing_from_fgu = []
    suspected_name_mismatches = []

    for full, first in directory_full_names.items():
        # Pass 1: exact full-name match (via employee_name_map.json resolution).
        match = learners_by_full.get(_norm(full))
        match_full_key = _norm(full)
        if match is None:
            # Pass 2: first-name-only fallback — catches directory entries that
            # are bare first names not yet resolved in employee_name_map.json
            # (e.g. "Angela" matching FGU's "Angela Ashby").
            candidates = learners_by_first.get(_norm(first)) or []
            if len(candidates) == 1:
                match = candidates[0]
                match_full_key = _norm(match.get("full_name"))
            elif len(candidates) > 1:
                # Ambiguous first name (e.g. two "Robert"s) — leave unmatched,
                # surfaced via directory_missing_from_fgu for a human look.
                pass
        if match is None:
            # Pass 3: known nickname/legal-name pairs pending a resolver fix.
            if first in nickname_map:
                nk_key = _norm(nickname_map[first])
                nk_match = learners_by_full.get(nk_key)
                if nk_match:
                    suspected_name_mismatches.append({
                        "directory_first_name": first,
                        "fgu_full_name": nk_match.get("full_name"),
                        "completion_rate": nk_match.get("completion_rate"),
                        "note": "Probable same person — add to employee_name_map.json, not a real mismatch.",
                    })
                    matched_learner_keys.add(_norm(nk_match.get("full_name")))
                continue

        if match is None:
            directory_missing_from_fgu.append({
                "first_name": first,
                "full_name": full,
                "reason": "no_account",
                "completion_rate": None,
            })
        else:
            matched_learner_keys.add(match_full_key)
            if (match.get("completion_rate") or 0) == 0:
                directory_missing_from_fgu.append({
                    "first_name": first,
                    "full_name": full,
                    "reason": "zero_percent",
                    "completion_rate": match.get("completion_rate"),
                })

    # (a) FGU learners not matched to any active directory entry (by any pass
    # above) and not a known management exclusion — likely termed / stale accounts.
    fgu_not_in_directory = []
    for l in learners:
        key = _norm(l.get("full_name"))
        if key in matched_learner_keys:
            continue
        if l.get("full_name") in KNOWN_MANAGEMENT_EXCLUDE:
            continue
        fgu_not_in_directory.append({
            "full_name": l.get("full_name"),
            "completion_rate": l.get("completion_rate"),
        })

    payload = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "fgu_pulled_at": pulled_at,
        "active_employee_count": len(active_first_names),
        "fgu_learner_count": len(learners),
        "note": (
            "fgu_not_in_directory is a REVIEW list, not confirmed-termed: the crew "
            "phone directory (build_employee_directory.py) is built incrementally and "
            "may lag reality or omit management. Known management (GM Bobby/Robert "
            "Cline) is excluded automatically. Confirm each name with Bobby before "
            "deactivating in Schoox."
        ),
        "fgu_not_in_directory": sorted(fgu_not_in_directory, key=lambda x: x["full_name"] or ""),
        "directory_missing_from_fgu": sorted(directory_missing_from_fgu, key=lambda x: x["full_name"] or ""),
        "suspected_name_mismatches": suspected_name_mismatches,
    }
    OUT_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"[reconcile] active employees: {len(active_first_names)}, FGU learners: {len(learners)}")
    print(f"[reconcile] FGU accounts not in active directory (likely termed): {len(fgu_not_in_directory)}")
    for x in payload["fgu_not_in_directory"]:
        print(f"    - {x['full_name']} ({x['completion_rate']}%)")
    print(f"[reconcile] active employees missing/0% in FGU: {len(directory_missing_from_fgu)}")
    for x in payload["directory_missing_from_fgu"]:
        print(f"    - {x['full_name']} [{x['reason']}]")
    if suspected_name_mismatches:
        print(f"[reconcile] suspected nickname/legal-name mismatches (not real gaps): {len(suspected_name_mismatches)}")
        for x in suspected_name_mismatches:
            print(f"    - directory '{x['directory_first_name']}' == FGU '{x['fgu_full_name']}'?")
    print(f"[reconcile] wrote {OUT_FILE}")


if __name__ == "__main__":
    main()
