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
    # CM redirects unauthenticated GET / to the login form on the same page.
    r = session.get(BASE + "/", timeout=30, allow_redirects=True)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    # Pick the form whose action looks login-shaped, or the one with a password field.
    forms = soup.find_all("form")
    form = None
    for f in forms:
        action = (f.get("action") or "").lower()
        if "sign" in action or "login" in action or "session" in action:
            form = f
            break
    if not form:
        for f in forms:
            if f.find("input", {"type": "password"}):
                form = f
                break
    if not form:
        raise RuntimeError(
            f"Could not find login form. Got {r.status_code} {r.url} "
            f"with {len(forms)} forms; saved body to data/cm_login_debug.html"
        )
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

    # Call 1: Apply — returns ~35 KB HTML. #accordion contains the location summary
    # card with the overall Required% / All% pair. Per-list breakdown is NOT here.
    summary_params = {
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
    r1 = session.get(f"{BASE}/groups/{group_id}/report/list_completions",
                     params=summary_params, timeout=30)
    r1.raise_for_status()
    soup1 = BeautifulSoup(r1.text, "html.parser")

    overall_req, overall_all, list_count = 0, 0, 0
    accordion = soup1.find(id="accordion")
    if accordion:
        for card in accordion.select("div.card.mb-0"):
            txt = card.get_text("\n", strip=True)
            m = re.search(r"(\d+)%\s*\|\s*(\d+)%", txt)
            if m and "Required" not in txt:
                overall_req, overall_all = int(m.group(1)), int(m.group(2))
                cm = re.search(r"\n(\d+)\n\d+%", txt)
                if cm:
                    list_count = int(cm.group(1))
                break

    # Call 2: drill-down — server responds with text/javascript. Body is a jQuery
    # `$("#location-lists-<id>").html("...escaped HTML...")` snippet. Extract the
    # JS string literal, JSON-decode the escapes, parse the embedded HTML.
    # Critical: must request Accept: text/javascript or server returns the full
    # page HTML instead.
    drill_params = {
        "authenticity_token": csrf,
        "location":        location_id,
        "start_date":      target_date,
        "end_date":        target_date,
        "target_selector": f"#location-lists-{location_id}",
        "report_filters_presenter[date_range]": "custom",
        "report_filters_presenter[start_date]": target_date,
        "report_filters_presenter[end_date]":   target_date,
        "report_filters_presenter[filter_for]": "reports_form",
        "report_filters_presenter[filter_type]": "lists",
        "report_filters_presenter[name]": "",
        "report_filters_presenter[report_type]": "list_completions",
    }
    r2 = session.get(f"{BASE}/groups/{group_id}/report/list_completions",
                     params=drill_params,
                     headers={"X-Requested-With": "XMLHttpRequest",
                              "Accept": "text/javascript, application/javascript"},
                     timeout=30)
    r2.raise_for_status()

    lists: list[dict] = []
    js = r2.text
    i = js.find("html(")
    j = js.find('"', i) if i >= 0 else -1
    k = js.rfind('"')
    if 0 <= j < k:
        escaped = js[j + 1:k]
        # Unescape JS string: handle \/ → /, then standard escapes.
        html = escaped.replace("\\/", "/").encode("utf-8").decode("unicode_escape")
        soup2 = BeautifulSoup(html, "html.parser")
        for card in soup2.select("div.card.mb-0"):
            name_el = card.select_one(".list-name")
            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            anchors = card.select(".daily-percentages a")
            if len(anchors) < 2:
                continue
            try:
                req_pct = int(anchors[0].get_text(strip=True).rstrip("%"))
                all_pct = int(anchors[1].get_text(strip=True).rstrip("%"))
            except ValueError:
                continue
            # Each anchor's href reveals the list_id for that checklist
            list_id_match = re.search(r"list_id=(\d+)", anchors[0].get("href", ""))
            lists.append({
                "name":         name,
                "list_id":      list_id_match.group(1) if list_id_match else None,
                "required_pct": req_pct,
                "all_pct":      all_pct,
            })

    return {
        "date":                 target_date,
        "location_id":          location_id,
        "list_count":           list_count,
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
    # Default filename preserves prior behavior. --out lets same-day preventive
    # sweeps (compliance-sweep agent, date=today) write to a separate file so
    # they never clobber the canonical yesterday-based dashboard feed.
    out_path = out_dir / (args.out or "compliancemate.json")
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
    pr.add_argument("--out", default=None,
                    help="Output filename under data/ (default: compliancemate.json). "
                         "Use e.g. compliancemate_today.json for same-day sweeps so the "
                         "canonical dashboard feed is never overwritten.")
    pr.set_defaults(fn=_cli_list_completions)
    args = p.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
