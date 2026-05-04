#!/usr/bin/env python3
"""
Teamworx internal-API client (lights-out replacement for Playwright scraping).

Reverse-engineered 2026-05-04. Full endpoint catalog in scraper/TEAMWORX_API.md.

Usage (one-shot daily roster pull, lights-out):

    python scraper/teamworx_api.py daily-roster --date 2026-05-04 --store 2065

Cookies:
    Reads cookies from `data/twx_cookies.json` (Playwright/Requests cookie format).
    Mint with `scraper/api_discover_teamworx.py` (TODO — not yet built; for now use
    the manual extraction path documented in TEAMWORX_API.md).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date as date_cls, datetime, timezone, timedelta
from pathlib import Path
from typing import Any

import requests

sys.stdout.reconfigure(encoding="utf-8")

ROOT          = Path(__file__).resolve().parents[1]
DATA_DIR      = ROOT / "data"
COOKIE_FILE   = DATA_DIR / "twx_cookies.json"

BASE          = "https://fiveguysfr77.ct-teamworx.com"
HEADERS_JSON  = {"Content-Type": "application/json", "Accept": "application/json"}

ET            = timezone(timedelta(hours=-4))


class TeamworxAuthError(RuntimeError):
    pass


def load_session() -> requests.Session:
    """Build a requests.Session with cookies from disk."""
    if not COOKIE_FILE.exists():
        raise TeamworxAuthError(
            f"No Teamworx cookies at {COOKIE_FILE}. "
            f"Mint with the discovery script or extract from a live browser session."
        )
    raw = json.loads(COOKIE_FILE.read_text())
    s = requests.Session()
    # Accept either a Playwright-style storage_state cookies array OR
    # a flat list/dict of cookies.
    if isinstance(raw, dict) and "cookies" in raw:
        cookies = raw["cookies"]
    else:
        cookies = raw
    for c in cookies:
        # Tolerate both Playwright shape and a simple {name, value, domain} shape
        s.cookies.set(
            name=c["name"],
            value=c["value"],
            domain=c.get("domain", ".ct-teamworx.com"),
            path=c.get("path", "/"),
        )
    s.headers.update({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) teamworx-api-client/1.0"})
    return s


def _post_json(s: requests.Session, path: str, body: dict) -> dict:
    r = s.post(BASE + path, headers=HEADERS_JSON, json=body, timeout=30)
    if r.status_code in (401, 403):
        raise TeamworxAuthError(f"{r.status_code} from {path} — cookies expired, re-mint")
    r.raise_for_status()
    j = r.json()
    if not j.get("success", False):
        raise RuntimeError(f"{path} returned success=false: {j.get('messageList')}")
    return j["data"]


def get_daily_roster(s: requests.Session, day: str) -> dict:
    """day: 'YYYY-MM-DD' string."""
    return _post_json(s, "/json/mn/dailyRoster/getPageData",
                      {"laborDate": day, "loadForecastData": False})


def get_employee_list(s: requests.Session, limit: int = 200) -> list[dict]:
    """Return all employees (auto-paginates up to `limit`)."""
    out: list[dict] = []
    start = 1
    page_size = 100
    while len(out) < limit:
        d = _post_json(s, "/json/emn/employee-list", {
            "sortInfo":   {"column": "NAME", "asc": True},
            "filter":     {"searchText": "", "positionIds": [], "primaryLocation": True},
            "pagingInfo": {"start": start, "limit": page_size},
        })
        emps = d.get("employees", [])
        out.extend(emps)
        if len(emps) < page_size:
            break
        start += page_size
    return out


def get_manager_home(s: requests.Session) -> dict:
    r = s.get(f"{BASE}/json/mn/getManagerHomePageData",
              headers={"Accept": "application/json"}, timeout=30)
    r.raise_for_status()
    j = r.json()
    return j.get("data", {})


# ─── Schema mapping: API response → dashboard weekly_schedule.json ─────────────

def _short_name(full: str) -> str:
    """Match the convention from scrape_teamworx_roster.py:short_name()."""
    full = (full or "").strip()
    if "," in full:
        last, first = (p.strip() for p in full.split(",", 1))
        first_word  = first.split()[0] if first.split() else ""
        last_first  = last.split()[0]  if last.split()  else ""
        return f"{first_word} {last_first[:1]}." if first_word and last_first else full
    parts = full.split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[-1][:1]}."
    return full


def _map_role(position_name: str) -> str:
    p = (position_name or "").lower()
    if "general manager" in p:        return "GM"
    if "shift manager" in p:          return "Shift Manager"
    if "manager" in p:                return "Manager"
    if "trainer" in p:                return "Trainer"
    if "minor" in p:                  return "Minor"
    if "crew" in p:                   return "Crew"
    return position_name or ""


def _ms_to_hhmm_et(ms: int | str | None) -> str:
    if ms in (None, "", "null"):
        return ""
    try:
        ts = int(ms) / 1000.0
        dt = datetime.fromtimestamp(ts, tz=ET)
        return dt.strftime("%-I:%M %p") if hasattr(dt, "strftime") else dt.strftime("%I:%M %p").lstrip("0")
    except Exception:
        return ""


def roster_to_weekly_schedule_json(roster_data: dict, store: str, day: str) -> dict:
    """Map the raw API response into the schema the dashboard wire expects."""
    shifts_in = roster_data.get("dayData", {}).get("shifts", [])
    shifts_out = []
    for sh in shifts_in:
        shifts_out.append({
            "name":      _short_name(sh.get("employeeName")),
            "full_name": sh.get("employeeName"),
            "position":  sh.get("positionName"),
            "role":      _map_role(sh.get("positionName")),
            "in_text":   sh.get("inTimeText"),
            "out_text":  sh.get("outTimeText"),
            "in_ms":     sh.get("inTime"),
            "out_ms":    sh.get("outTime"),
            "hours":     sh.get("hours"),
            "minor":     bool(sh.get("minor")),
        })
    total_hours = sum(float(s.get("hours") or 0) for s in shifts_out)
    return {
        "source":       "teamworx_api",
        "source_url":   f"{BASE}/json/mn/dailyRoster/getPageData",
        "store":        store,
        "labor_date":   day,
        "fetched_at":   datetime.now(tz=ET).isoformat(),
        "shift_count":  len(shifts_out),
        "total_hours":  round(total_hours, 2),
        "shifts":       shifts_out,
    }


# ─── CLI ───────────────────────────────────────────────────────────────────────

def _cli_daily_roster(args: argparse.Namespace) -> int:
    s = load_session()
    day = args.date or datetime.now(tz=ET).strftime("%Y-%m-%d")
    raw = get_daily_roster(s, day)
    out = roster_to_weekly_schedule_json(raw, args.store, day)

    out_dir = DATA_DIR / "raw" / "parbrink" / args.store / day
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "weekly_schedule.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"OK  {len(out['shifts'])} shifts, {out['total_hours']} hrs  ->  {out_path}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("daily-roster", help="Pull today's (or --date) daily roster")
    pr.add_argument("--store", required=True)
    pr.add_argument("--date",  default=None, help="YYYY-MM-DD (default: today ET)")
    pr.set_defaults(fn=_cli_daily_roster)

    args = p.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
