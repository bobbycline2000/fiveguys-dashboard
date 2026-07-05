#!/usr/bin/env python3
"""
Five Guys University (Schoox) training-completion pull for store KY-2065.

FGU == Schoox. Reverse-engineered 2026-07-05 — see scraper/FGU_API.md.

Auth: a Bearer JWT from a logged-in Schoox tab's localStorage['token'].
Cookie auth alone returns 401. This script does NOT log in — the fgu-professor
agent captures a fresh token from Bobby's Chrome session and writes it to a
session file (default: data/fgu_session.json):

    { "token": "<bearer jwt>" }

Because Schoox login is Google-SSO/MFA gated, token capture runs through the
agent's Chrome session (same pattern as the Outlook MSAL grab). Once the token
is fresh, every call here is pure requests — no browser at runtime.

Output: data/fgu_training.json
    {
      "store": "2065", "academy_id": 1177, "org_unit": 1291469,
      "pulled_at": "<iso>",
      "stats": { totalLearners, coursesCompletionRate, coursesOverdueRate, ... },
      "learners": [ { name, surname, full_name, total_courses,
                      completion_rate, compliance_rate, learner_id }, ... ],
      "behind": [ ...subset with completion_rate < 100, sorted asc... ]
    }

Usage:
    python scraper/scrape_fgu.py                 # uses data/fgu_session.json
    FGU_TOKEN=<jwt> python scraper/scrape_fgu.py # or pass token via env
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SESSION_FILE = DATA / "fgu_session.json"
OUT_FILE = DATA / "fgu_training.json"

ACADEMY_ID = 1177
ORG_UNIT = 1291469          # KY2065
STORE = os.environ.get("STORE_ID", "2065")
BASE = "https://app.schoox.com/api/v2"

FILTERS = ("trainingFilterSet=teamDashboardLearners"
           "&trainingFilters[]=orgStructure,%d,orgUnit"
           "&trainingFilters[]=sorting,alphabetically,asc" % ORG_UNIT)


def load_token() -> str:
    tok = os.environ.get("FGU_TOKEN", "").strip()
    if tok:
        return tok
    if SESSION_FILE.exists():
        tok = json.loads(SESSION_FILE.read_text(encoding="utf-8")).get("token", "").strip()
        if tok:
            return tok
    print(f"[fgu] no token — set FGU_TOKEN or write {SESSION_FILE}", file=sys.stderr)
    sys.exit(1)


def session(tok: str) -> requests.Session:
    s = requests.Session()
    s.headers.update({"Accept": "application/json", "Authorization": f"Bearer {tok}"})
    return s


def pull_learners(s: requests.Session) -> list[dict]:
    out, page = [], 1
    while page <= 20:  # 34 learners today; hard cap is a runaway guard
        url = f"{BASE}/academies/{ACADEMY_ID}/team-dashboard/learners?{FILTERS}&page={page}"
        r = s.get(url, timeout=30)
        if r.status_code == 401:
            print("[fgu] 401 — token expired, re-capture from Chrome", file=sys.stderr)
            sys.exit(2)
        r.raise_for_status()
        j = r.json()
        for x in j.get("_embedded", {}).get("learners", []):
            full = f"{x.get('name','')} {x.get('surname','')}".strip()
            out.append({
                "learner_id": x.get("id"),
                "name": x.get("name"),
                "surname": x.get("surname"),
                "full_name": full,
                "total_courses": x.get("totalCourses"),
                "completion_rate": x.get("coursesCompletionRate"),
                "compliance_rate": x.get("coursesComplianceRate"),
            })
        if not j.get("more"):
            break
        page += 1
    return out


def pull_stats(s: requests.Session) -> dict:
    url = f"{BASE}/academies/{ACADEMY_ID}/team-dashboard/learners/statistics?refresh=0&{FILTERS}"
    r = s.get(url, timeout=30)
    r.raise_for_status()
    j = r.json()
    return {k: j.get(k) for k in ("totalLearners", "coursesCompletionRate",
                                  "coursesComplianceRate", "coursesOverdueRate",
                                  "calculatedAt")}


def main() -> None:
    s = session(load_token())
    learners = pull_learners(s)
    stats = pull_stats(s)
    behind = sorted([l for l in learners if (l["completion_rate"] or 0) < 100],
                    key=lambda l: l["completion_rate"] or 0)
    payload = {
        "store": STORE, "academy_id": ACADEMY_ID, "org_unit": ORG_UNIT,
        "pulled_at": datetime.now(tz=timezone.utc).isoformat(),
        "stats": stats, "learners": learners, "behind": behind,
    }
    OUT_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    # Sanity: completion rates are 0-100.
    bad = [l["full_name"] for l in learners if not (0 <= (l["completion_rate"] or 0) <= 100)]
    print(f"[fgu] {len(learners)} learners, "
          f"store completion {stats.get('coursesCompletionRate')}%, "
          f"{len(behind)} behind, overdue {stats.get('coursesOverdueRate')}%")
    if bad:
        print(f"[fgu] WARN out-of-range completion for: {bad}", file=sys.stderr)
    print(f"[fgu] wrote {OUT_FILE}")


if __name__ == "__main__":
    main()
