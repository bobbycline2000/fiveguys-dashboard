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
import sys
import json
import argparse
import logging
from datetime import datetime, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE_URL = "https://fiveguys.steritech.com"
API_VERSION = "856a14b9b017e461bd285c6f21522404119d8126"
QUICK_ACCESS_CODE = "OBO8R8R2T"
LOCATION_ID = 273138
EMAIL = "rcline@estep-co.com"


def make_session(quick_access: bool = True) -> requests.Session:
    """Create a requests session with correct headers."""
    s = requests.Session()
    s.headers.update({
        "x-api-version": API_VERSION,
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (compatible; FG2065-Scraper/1.0)",
    })
    if quick_access:
        s.headers["x-quick-access-code"] = QUICK_ACCESS_CODE
    return s


def quick_access_login(s: requests.Session) -> dict:
    """Authenticate via quick-access code. Returns assessment JSON."""
    log.info("Authenticating via quick-access code...")
    resp = s.get(f"{BASE_URL}/api/quick_access/assessment/sign_in")
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


def main():
    parser = argparse.ArgumentParser(description="Steritech scraper for FG Store 2065")
    parser.add_argument("--full-history", action="store_true", help="Pull full history (requires STERITECH_PASSWORD env var)")
    parser.add_argument("--output", default="data/steritech_current.json", help="Output JSON file path")
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

    else:
        # Quick-access mode — current CAP only
        s = make_session(quick_access=True)
        data = quick_access_login(s)
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

    os.makedirs(os.path.dirname(args.output), exist_ok=True) if os.path.dirname(args.output) else None
    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)

    log.info(f"Saved to {args.output}")
    return output


if __name__ == "__main__":
    main()
