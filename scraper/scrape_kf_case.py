#!/usr/bin/env python3
"""
KnowledgeForce Case Detail Scraper
====================================
Given a KnowledgeForce case ID, fetches the case management detail page and
returns customer + complaint data as JSON.

Usage:
  python scraper/scrape_kf_case.py <CASE_ID>

Output (stdout, JSON):
  {
    "case_id": "5NFRW2",
    "customer_name": "Rebecca Pelt",
    "phone": "(502) 492-7879",
    "email": "rebeccapelt12@gmail.com",
    "visit_date": "05/13/2026",
    "order_type": "Online Ordering Pick-up",
    "issue_category": "L3 - Accuracy of Order",
    "location_id": "002065",
    "comment": "..."
  }

On failure prints:
  {"error": "<reason>", "case_id": "<id>"}
and exits with code 1.

Notes:
  - The case detail page spreads its data across multiple <table class="ticket-table">
    elements. All are iterated.
  - Phone is stored as raw digits (e.g. "5024927879"); this script formats it as
    "(NXX) NXX-XXXX" before returning.
  - visit_date is returned as "MM/DD/YYYY" extracted from the KF timestamp string.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://www.knowledgeforce.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 KnowledgeForceAPIClient/1.0"

# Normalised ticket-table label → output key mapping.
# KF spreads fields across multiple ticket-table elements; we iterate all of them.
_LABEL_MAP = {
    "customer name":      "customer_name",
    "phone":              "phone",
    "email":              "email",
    "occurred":           "visit_date",
    "customer type":      "order_type",
    "complaint category": "issue_category",
    "location id":        "location_id",
}


def log(msg: str) -> None:
    print(f"[kf-case] {msg}", file=sys.stderr, flush=True)


def _err(case_id: str, reason: str) -> dict:
    return {"error": reason, "case_id": case_id}


def _fmt_phone(raw: str) -> str | None:
    """Format a raw digit string to (NXX) NXX-XXXX.
    KF stores phone as '5024927879' (10 raw digits, no punctuation).
    Returns None if the input doesn't look like a 10-digit US number."""
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return raw or None


def _fmt_date(raw: str) -> str | None:
    """Extract MM/DD/YYYY from a KF timestamp string like 'Wed, May 13 2026 00:00:00'.
    Returns None if not parseable."""
    # Try 'Month DD YYYY' pattern inside the string
    m = re.search(r"(\w{3})\s+(\d{1,2})\s+(\d{4})", raw or "")
    if m:
        month_abbr, day, year = m.group(1), int(m.group(2)), m.group(3)
        _MONTHS = {
            "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
            "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
            "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
        }
        mo = _MONTHS.get(month_abbr[:3].capitalize())
        if mo:
            return f"{mo}/{day:02d}/{year}"
    return raw or None


def login(s: requests.Session, user: str, pw: str) -> bool:
    """Auth flow — identical to scrape_knowledgeforce_api.py:login()."""
    r = s.get(BASE + "/", timeout=30)
    r.raise_for_status()
    m = re.search(r'name="_csrf"[^>]*value="([^"]+)"', r.text)
    if not m:
        log("no _csrf token found on landing page")
        return False
    csrf = m.group(1)
    payload = {
        "_csrf": csrf,
        "Login[username]": user,
        "Login[password]": pw,
    }
    r = s.post(BASE + "/", data=payload, timeout=30, allow_redirects=True)
    r.raise_for_status()
    if "/login" in r.url.lower() or 'name="Login[username]"' in r.text[:5000]:
        log(f"login failed — final URL {r.url}")
        return False
    log(f"login OK — landed on {r.url}")
    return True


def fetch_case(s: requests.Session, case_id: str) -> dict:
    """Fetch and parse a KnowledgeForce case detail page.

    Returns a dict with keys:
      case_id, customer_name, phone, email, visit_date, order_type,
      issue_category, location_id, comment
    Any field not found is None.
    """
    url = f"{BASE}/casemanagement/casemanagement/details?id={case_id}"
    r = s.get(url, timeout=30)
    if not r.ok:
        raise RuntimeError(f"case page HTTP {r.status_code} for case {case_id}")

    soup = BeautifulSoup(r.text, "html.parser")

    result: dict = {
        "case_id":        case_id,
        "customer_name":  None,
        "phone":          None,
        "email":          None,
        "visit_date":     None,
        "order_type":     None,
        "issue_category": None,
        "location_id":    None,
        "comment":        None,
    }

    # KF spreads fields across multiple <table class="ticket-table"> elements.
    # Iterate all of them to collect every mapped field.
    tables = soup.find_all("table", class_="ticket-table")
    if not tables:
        log("no ticket-table found on case page")
    for table in tables:
        for row in table.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if not th or not td:
                continue
            label = th.get_text(strip=True).lower().rstrip(":")
            value = td.get_text(strip=True) or None
            key = _LABEL_MAP.get(label)
            if key and result[key] is None:  # first match wins
                result[key] = value

    # Post-process: format phone, visit_date, and normalize name casing
    if result["phone"]:
        result["phone"] = _fmt_phone(result["phone"])
    if result["visit_date"]:
        result["visit_date"] = _fmt_date(result["visit_date"])
    if result["customer_name"]:
        result["customer_name"] = result["customer_name"].title()

    # Complaint comment
    comment_div = soup.select_one("div.complaint-details-text")
    if comment_div:
        result["comment"] = comment_div.get_text(strip=True) or None
    else:
        log("complaint-details-text div not found")

    return result


def main() -> int:
    if len(sys.argv) < 2:
        out = {"error": "usage: scrape_kf_case.py <CASE_ID>", "case_id": ""}
        print(json.dumps(out))
        return 1

    case_id = sys.argv[1].strip()

    user = os.environ.get("KNOWLEDGEFORCE_USERNAME", "")
    pw = os.environ.get("KNOWLEDGEFORCE_PASSWORD", "")
    if not user or not pw:
        print(json.dumps(_err(case_id, "KNOWLEDGEFORCE_USERNAME / PASSWORD env vars required")))
        return 1

    s = requests.Session()
    s.headers.update({"User-Agent": UA})

    try:
        if not login(s, user, pw):
            print(json.dumps(_err(case_id, "login failed")))
            return 1
    except Exception as exc:
        print(json.dumps(_err(case_id, f"login error: {exc}")))
        return 1

    try:
        result = fetch_case(s, case_id)
    except Exception as exc:
        print(json.dumps(_err(case_id, f"case fetch error: {exc}")))
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    # Auto-load .env if creds not in env
    if not os.environ.get("KNOWLEDGEFORCE_USERNAME"):
        env_path = ROOT / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("KNOWLEDGEFORCE_") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip())
    sys.exit(main())
