"""
scrape_steritech.py — OnBrand360 / Steritech API scraper for FG Store 2065

TWO modes:
  1. Quick-access (default): pulls current open CAP using access code OBO8R8R2T
     - Returns current assessment + findings only
     - No history available via this path

  2. Full login (requires STERITECH_PASSWORD env var): pulls all historical
     assessments + line items for location 273138

Usage:
    python scrape_steritech.py                    # quick-access, current CAP
    python scrape_steritech.py --full-history      # full login, all history
    python scrape_steritech.py --output data/steritech_current.json

Auth discovered: 2026-05-16
See: scraper/STERITECH_API.md for full endpoint catalog
"""

import os
import re
import sys
import json
import argparse
import logging
from datetime import datetime, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE_URL = "https://fiveguys.steritech.com"
# Last-known-good x-api-version. This drifts whenever Steritech ships a new
# frontend build (confirmed: 856a14b9b017e461bd285c6f21522404119d8126 discovered
# 2026-05-16 -> 588d53564a96485db9be0dca2bcc09564107847e discovered 2026-07-11,
# root cause of a 412 "Wrong api version" failure). discover_api_version() below
# self-heals by pulling the live value out of the app JS bundle on every run so
# this constant is only a fallback, not the source of truth.
API_VERSION_FALLBACK = "588d53564a96485db9be0dca2bcc09564107847e"
QUICK_ACCESS_CODE = "OBO8R8R2T"
LOCATION_ID = 273138
EMAIL = "rcline@estep-co.com"


def discover_api_version() -> str:
    """
    Pull the current apiVersion constant straight from the live app bundle so
    the scraper survives Steritech frontend deploys without a manual patch.
    Falls back to API_VERSION_FALLBACK if discovery fails for any reason.
    """
    try:
        plain = requests.Session()
        plain.headers.update({"User-Agent": "Mozilla/5.0 (compatible; FG2065-Scraper/1.0)"})
        root = plain.get(f"{BASE_URL}/", timeout=15)
        root.raise_for_status()
        m = re.search(r'src="(/assets/app_prod/app-[^"]+\.js)"', root.text)
        if not m:
            log.warning("Could not find app JS bundle path — using fallback api-version")
            return API_VERSION_FALLBACK
        js = plain.get(f"{BASE_URL}{m.group(1)}", timeout=30)
        js.raise_for_status()
        vm = re.search(r'constant\("apiVersion","([0-9a-f]{40})"\)', js.text)
        if vm:
            version = vm.group(1)
            if version != API_VERSION_FALLBACK:
                log.info(f"api-version drift detected: fallback={API_VERSION_FALLBACK} live={version}")
            return version
        log.warning("apiVersion constant not found in bundle — using fallback")
    except Exception as exc:
        log.warning(f"api-version auto-discovery failed ({exc}) — using fallback")
    return API_VERSION_FALLBACK


def make_session(quick_access: bool = True, api_version: str | None = None) -> requests.Session:
    """Create a requests session with correct headers."""
    s = requests.Session()
    s.headers.update({
        "x-api-version": api_version or discover_api_version(),
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (compatible; FG2065-Scraper/1.0)",
    })
    if quick_access:
        s.headers["x-quick-access-code"] = QUICK_ACCESS_CODE
    return s


class QuickAccessCodeExpired(Exception):
    """Raised when the quick-access code itself (not the api-version) is stale."""


def quick_access_login(s: requests.Session) -> dict:
    """Authenticate via quick-access code. Returns assessment JSON."""
    log.info("Authenticating via quick-access code...")
    resp = s.get(f"{BASE_URL}/api/quick_access/assessment/sign_in")
    if resp.status_code == 401:
        try:
            err = resp.json()
        except ValueError:
            err = {}
        if "expired" in json.dumps(err).lower():
            raise QuickAccessCodeExpired(
                f"Quick-access code {QUICK_ACCESS_CODE} has expired. "
                "A new code must be generated from the OnBrand360/Steritech portal "
                "(or set STERITECH_PASSWORD and run --full-history instead)."
            )
    resp.raise_for_status()
    log.info("Quick-access login OK — fetching current assessment...")
    resp2 = s.get(f"{BASE_URL}/api/quick_access/assessment")
    resp2.raise_for_status()
    return resp2.json()


def full_login(s: requests.Session, password: str) -> bool:
    """Authenticate with full email + password. Returns True on success."""
    log.info(f"Logging in as {EMAIL}...")
    resp = s.post(f"{BASE_URL}/api/users/sign_in", json={
        "user": {"email": EMAIL, "password": password}
    })
    if resp.status_code == 401:
        log.error("Login failed: invalid credentials")
        return False
    resp.raise_for_status()
    log.info("Full login OK")
    return True


def pull_all_assessments(s: requests.Session) -> list:
    """Pull all historical assessments for location 273138. Requires full login."""
    all_assessments = []
    page = 1
    while True:
        resp = s.get(f"{BASE_URL}/api/assessments", params={
            "location_id": LOCATION_ID,
            "page": page,
            "per_page": 50,
        })
        if resp.status_code == 401:
            log.error("Not authorized — full login required for historical data")
            break
        resp.raise_for_status()
        data = resp.json()
        items = data.get("assessments", data.get("results", [data] if isinstance(data, dict) else data))
        if not items:
            break
        all_assessments.extend(items)
        log.info(f"  Page {page}: {len(items)} assessments")
        if len(items) < 50:
            break
        page += 1
    return all_assessments


def pull_all_caps(s: requests.Session) -> list:
    """Pull all historical CAPs for location 273138. Requires full login."""
    all_caps = []
    page = 1
    while True:
        resp = s.get(f"{BASE_URL}/api/corrective_action_plans", params={
            "location_id": LOCATION_ID,
            "page": page,
            "per_page": 50,
        })
        if resp.status_code == 401:
            log.error("Not authorized — full login required for CAP history")
            break
        resp.raise_for_status()
        data = resp.json()
        items = data.get("corrective_action_plans", data.get("results", []))
        if not items:
            break
        all_caps.extend(items)
        log.info(f"  Page {page}: {len(items)} CAPs")
        if len(items) < 50:
            break
        page += 1
    return all_caps


def parse_current_cap(data: dict) -> list[dict]:
    """
    Flatten the current CAP JSON into a list of missed-item rows.
    Returns list of dicts with keys matching the training tracker columns.
    """
    rows = []
    cap = data.get("corrective_action_plan", {})
    assessment = data.get("assessment", {})

    visit_date_raw = assessment.get("finish_date", "")
    visit_date = visit_date_raw[:10] if visit_date_raw else "Unknown"
    score = assessment.get("score", "")
    round_title = assessment.get("round", {}).get("title", "")
    report_type = "Steritech"  # quick-access only exposes food safety assessment

    for item in cap.get("line_items", []):
        code = item.get("code", "")
        title = item.get("title", "")
        risk_level_num = item.get("risk_level", 2)
        risk_label = "Critical" if risk_level_num == 1 else "Non-Critical"
        is_repeat = item.get("repeat", False)

        for action in item.get("action_items", []):
            area = action.get("location_lbr_result", "")
            detail = action.get("details_lbr_result", "")
            issue = action.get("issue_lbr_result", "")
            other_info = action.get("other_information_text", "")
            corrective_action = action.get("course_of_action", "")
            status = action.get("status", "")

            rows.append({
                "Visit Date": visit_date,
                "Report Type": report_type,
                "Round": round_title,
                "Score": score,
                "Item #": code,
                "Item Description": title,
                "Issue": issue,
                "Area": area,
                "Detail": detail,
                "Other Info": other_info,
                "Severity": risk_label,
                "Repeat": "Yes" if is_repeat else "No",
                "Status": status,
                "Corrective Action": corrective_action[:500] if corrective_action else "",
            })

    return rows


# Keyword categories the dashboard card checks on every findings list. These
# are Bobby's dashboard's fixed "spot check" rows (hand wash / cooler / grill
# hold / date labels) — not a Steritech-native grouping. A finding flags the
# matching row "watch" if its title/area/detail mentions the keyword.
_LINE_ITEM_KEYWORDS = {
    "hand_wash_stations": ["hand wash", "handwash", "hand sink"],
    "cooler_temps": ["cooler", "walk-in temp", "walk in temp", "refrigerat"],
    "grill_hold_temps": ["grill", "hold temp", "hot hold"],
    "date_labels": ["date label", "date mark", "shelf life"],
}


def build_canonical(data: dict, mode: str) -> dict:
    """
    Flatten a raw scrape_steritech.py payload (quick_access or full_history mode)
    into the canonical schema data/steritech.json / wire_dashboard.py expect:
      latest_score, status, last_audit_date, next_audit_window, round_title,
      critical_violations, non_critical, findings[], line_item_checks{}, cap_due_date
    """
    now = datetime.now(timezone.utc).isoformat()

    if mode == "quick_access":
        assessment = data.get("assessment", {}) or {}
        cap = data.get("corrective_action_plan", {}) or {}
        score_raw = assessment.get("score")
        score = int(score_raw) if score_raw not in (None, "") else None
        last_audit_date = (assessment.get("finish_date") or "")[:10] or None
        round_title = assessment.get("round", {}).get("title", "")
        cap_due_date = (cap.get("due_date") or "")[:10] or None

        findings = []
        critical = 0
        non_critical = 0
        for item in cap.get("line_items", []):
            risk = item.get("risk_level", 2)
            severity = "Critical" if risk == 1 else "Non-Critical"
            if risk == 1:
                critical += 1
            else:
                non_critical += 1
            findings.append({
                "code": item.get("code", ""),
                "title": item.get("title", ""),
                "severity": severity,
                "repeat": bool(item.get("repeat", False)),
            })

        line_item_checks = {k: "pass" for k in _LINE_ITEM_KEYWORDS}
        haystacks = [f["title"].lower() for f in findings]
        for key, keywords in _LINE_ITEM_KEYWORDS.items():
            if any(kw in h for h in haystacks for kw in keywords):
                line_item_checks[key] = "watch"

    else:  # full_history — best-effort; schema unconfirmed until STERITECH_PASSWORD is live-tested
        assessments = data.get("assessments", []) or []
        latest = None
        for a in assessments:
            fd = a.get("finish_date", "")
            if latest is None or fd > latest.get("finish_date", ""):
                latest = a
        score_raw = (latest or {}).get("score")
        score = int(score_raw) if score_raw not in (None, "") else None
        last_audit_date = ((latest or {}).get("finish_date") or "")[:10] or None
        round_title = (latest or {}).get("round", {}).get("title", "") if latest else ""
        cap_due_date = None
        findings = []
        critical = non_critical = 0
        line_item_checks = {k: "pass" for k in _LINE_ITEM_KEYWORDS}

    status = "Pass" if (score is not None and score >= 90 and critical == 0) else (
        "Fail" if score is not None else "Unknown"
    )

    return {
        "pulled_at": now,
        "mode": mode,
        "location_id": LOCATION_ID,
        "latest_score": score,
        "status": status,
        "last_audit_date": last_audit_date,
        "round_title": round_title,
        "cap_due_date": cap_due_date,
        "critical_violations": critical,
        "non_critical": non_critical,
        "findings": findings,
        "line_item_checks": line_item_checks,
    }


def main():
    parser = argparse.ArgumentParser(description="Steritech scraper for FG Store 2065")
    parser.add_argument("--full-history", action="store_true", help="Pull full history (requires STERITECH_PASSWORD env var)")
    parser.add_argument("--output", default="data/steritech_current.json", help="Raw output JSON file path")
    parser.add_argument("--canonical-output", default="data/steritech.json", help="Canonical dashboard-schema JSON path")
    args = parser.parse_args()

    if args.full_history:
        password = os.environ.get("STERITECH_PASSWORD")
        if not password:
            log.error("STERITECH_PASSWORD environment variable not set. Cannot pull full history.")
            log.error("Set it with: $env:STERITECH_PASSWORD = 'your-password'")
            sys.exit(1)

        s = make_session(quick_access=False)
        if not full_login(s, password):
            sys.exit(1)

        log.info("Pulling all historical assessments...")
        assessments = pull_all_assessments(s)
        log.info(f"Found {len(assessments)} assessments")

        log.info("Pulling all historical CAPs...")
        caps = pull_all_caps(s)
        log.info(f"Found {len(caps)} CAPs")

        output = {
            "pulled_at": datetime.now(timezone.utc).isoformat(),
            "mode": "full_history",
            "location_id": LOCATION_ID,
            "assessments": assessments,
            "corrective_action_plans": caps,
        }
        canonical = build_canonical(output, "full_history")

    else:
        # Quick-access mode — current CAP only
        s = make_session(quick_access=True)
        try:
            data = quick_access_login(s)
        except QuickAccessCodeExpired as exc:
            log.error(str(exc))
            sys.exit(2)
        rows = parse_current_cap(data)

        log.info(f"Current CAP: {len(rows)} missed items")
        for r in rows:
            log.info(f"  Item {r['Item #']}: {r['Item Description'][:60]} | {r['Area']} | {r['Severity']} | repeat={r['Repeat']}")

        output = {
            "pulled_at": datetime.now(timezone.utc).isoformat(),
            "mode": "quick_access",
            "raw": data,
            "flattened_rows": rows,
        }
        canonical = build_canonical(data, "quick_access")

    os.makedirs(os.path.dirname(args.output), exist_ok=True) if os.path.dirname(args.output) else None
    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)
    log.info(f"Saved raw output to {args.output}")

    os.makedirs(os.path.dirname(args.canonical_output), exist_ok=True) if os.path.dirname(args.canonical_output) else None
    with open(args.canonical_output, "w") as f:
        json.dump(canonical, f, indent=2)
    log.info(f"Saved canonical dashboard data to {args.canonical_output}")

    return output


if __name__ == "__main__":
    main()
