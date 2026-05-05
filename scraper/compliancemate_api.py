#!/usr/bin/env python3
"""
ComplianceMate URL-replay client (lights-out replacement for Playwright scraping).

Reverse-engineered 2026-05-04. Full discovery notes in scraper/COMPLIANCEMATE_API.md.

Usage:
    python scraper/compliancemate_api.py list-completions --store 2065 --date yesterday
    python scraper/compliancemate_api.py list-completions --store 2065 --date 2026-05-03
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date as date_cls, datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8")

ROOT     = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

BASE     = "https://fg-beta.compliancemate.com"
ET       = timezone(timedelta(hours=-4))

# ─── Per-store IDs (extend as more stores are onboarded) ──────────────────────
STORES = {
    "2065": {"group_id": "21792", "location_id": "18170", "name": "2065 - Louisville, KY"},
}


# ─── Auth ─────────────────────────────────────────────────────────────────────

def _load_env():
    if not os.environ.get("COMPLIANCEMATE_USERNAME"):
        env_path = ROOT / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def login(session: requests.Session, username: str, password: str) -> None:
    """
    POST credentials to ComplianceMate's login form and persist session cookies.

    The exact form action + field names are discovered on first call by GETting
    the login page and parsing the form. Logged in == subsequent GET to /
    returns the dashboard, not the login page.
    """
    login_url = f"{BASE}/users/sign_in"
    r = session.get(login_url, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    form = soup.find("form", {"action": re.compile(r"sign_in")}) or soup.find("form")
    if not form:
        raise RuntimeError("Could not find login form on " + login_url)
    action = form.get("action", "/users/sign_in")
    if not action.startswith("http"):
        action = BASE + action

    # Build payload from hidden fields + creds
    payload: dict[str, str] = {}
    for inp in form.find_all("input"):
        name = inp.get("name")
        if not name:
            continue
        payload[name] = inp.get("value", "")

    # Best-effort field detection for username + password
    for fname in ("user[email]", "user[login]", "user[username]"):
        if fname in payload:
            payload[fname] = username
            break
    else:
        # Heuristic: pick first text-like input that isn't password / hidden
        for inp in form.find_all("input"):
            t = inp.get("type", "text")
            if t in ("email", "text") and inp.get("name"):
                payload[inp["name"]] = username
                break
    for fname in ("user[password]", "password"):
        if fname in payload:
            payload[fname] = password
            break
    else:
        for inp in form.find_all("input"):
            if inp.get("type") == "password" and inp.get("name"):
                payload[inp["name"]] = password
                break

    r2 = session.post(action, data=payload, allow_redirects=True, timeout=30)
    r2.raise_for_status()
    # Logged in if we DON'T see the sign_in form on the response
    if "sign_in" in r2.url or "sign in" in r2.text.lower()[:5000]:
        raise RuntimeError("Login failed — credentials rejected or MFA required")


def get_csrf_token(session: requests.Session, group_id: str) -> str:
    """Fetch any authenticated page and pluck the <meta name=csrf-token>."""
    r = session.get(f"{BASE}/groups/{group_id}/report/list_completions", timeout=30)
    r.raise_for_status()
    m = re.search(r'<meta\s+name=["\']csrf-token["\']\s+content=["\']([^"\']+)', r.text)
    if not m:
        raise RuntimeError("No csrf-token meta found")
    return m.group(1)


# ─── List Completions report ─────────────────────────────────────────────────

def get_list_completions(
    session: requests.Session,
    group_id: str,
    location_id: str,
    target_date: str,
    csrf: str | None = None,
) -> dict:
    """
    target_date: 'YYYY-MM-DD' string (the day to report on).
    Returns: {
      'date': 'YYYY-MM-DD',
      'location_id': '18170',
      'overall_required_pct': float,
      'overall_all_pct':      float,
      'lists': [{'name': '11AM: Time and Temp', 'required_pct': 100, 'all_pct': 100}, ...]
    }
    """
    if csrf is None:
        csrf = get_csrf_token(session, group_id)
    params = {
        "authenticity_token": csrf,
        "commit": "Apply",
        "report_filters_presenter[date_range]": "custom",
        "report_filters_presenter[start_date]": target_date,
        "report_filters_presenter[end_date]":   target_date,
        "report_filters_presenter[filter_for]": "reports_form",
        "report_filters_presenter[filter_type]": "lists",
        "report_filters_presenter[name]": "",
        "report_filters_presenter[report_type]": "list_completions",
        "report_form_submit": "true",
        "requested_timezone": "America/New_York",
    }
    r = session.get(f"{BASE}/groups/{group_id}/report/list_completions",
                    params=params, timeout=30)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    # Find the location's collapse container
    container = soup.find("div", id=f"location_{location_id}_lists")
    lists: list[dict] = []
    if container:
        for card in container.select("div.card.mb-0"):
            txt = card.get_text("\n", strip=True)
            # Expected shape:  "<list name>\n<n>% | <n>%"
            m = re.search(r"^(.+?)\n(\d+)%\s*\|\s*(\d+)%", txt)
            if m:
                lists.append({
                    "name":          m.group(1).strip(),
                    "required_pct":  int(m.group(2)),
                    "all_pct":       int(m.group(3)),
                })

    # Also pull the location header summary
    overall_req, overall_all = 0, 0
    header = soup.find("div", id=f"location_{location_id}_card") or soup.find(
        "div", string=re.compile(r"\d+%\s*\|\s*\d+%")
    )
    # Fallback: scan the page for the location's own summary line
    for div in soup.select("div.card-header"):
        t = div.get_text("\n", strip=True)
        if STORES.get(location_id, {}).get("name", "") in t or "Louisville" in t:
            m = re.search(r"(\d+)%\s*\|\s*(\d+)%", t)
            if m:
                overall_req, overall_all = int(m.group(1)), int(m.group(2))
                break

    return {
        "date":                 target_date,
        "location_id":          location_id,
        "list_count":           len(lists),
        "overall_required_pct": overall_req,
        "overall_all_pct":      overall_all,
        "lists":                lists,
        "fetched_at":           datetime.now(tz=ET).isoformat(),
        "source":               "compliancemate_url_replay",
    }


# ─── CLI ──────────────────────────────────────────────────────────────────────

def _resolve_date(arg: str) -> str:
    if arg == "today":
        return datetime.now(tz=ET).strftime("%Y-%m-%d")
    if arg == "yesterday":
        return (datetime.now(tz=ET) - timedelta(days=1)).strftime("%Y-%m-%d")
    return arg


def _cli_list_completions(args: argparse.Namespace) -> int:
    _load_env()
    user = os.environ["COMPLIANCEMATE_USERNAME"]
    pwd  = os.environ["COMPLIANCEMATE_PASSWORD"]

    cfg = STORES[args.store]
    target = _resolve_date(args.date)

    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 cm-api-client/1.0"})
    login(s, user, pwd)
    out = get_list_completions(s, cfg["group_id"], cfg["location_id"], target)

    out_dir = DATA_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "compliancemate.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"OK  {out['list_count']} lists, overall {out['overall_required_pct']}% req / "
          f"{out['overall_all_pct']}% all  ->  {out_path}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("list-completions", help="Pull a day's list completion report")
    pr.add_argument("--store", required=True, choices=list(STORES.keys()))
    pr.add_argument("--date",  default="yesterday",
                    help="'today' | 'yesterday' | 'YYYY-MM-DD' (default: yesterday)")
    pr.set_defaults(fn=_cli_list_completions)
    args = p.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
