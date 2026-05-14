#!/usr/bin/env python3
"""
Scrape Marketforce shop visit-time buckets from KnowledgeForce.

For each shop in the latest shops.json that lacks `visit_window`, fetch the
assignment detail page for that shop and extract the `.04 Time In` answer
(e.g., "4 pm-6:59 pm" -> [16.0, 19.0]).

Source: GET /reporting/assignment/view?dataset={"jid":<jid>,"period2":[<period2>]}
The page HTML contains a line like:
  "Time In: (Mark one only:) 4 pm-6:59 pm"
Discovered 2026-05-14 via pure requests session (no Playwright required).

Previously used the Question Results report page with Playwright. Replaced
2026-05-14 with this pure-requests approach after confirming the assignment
view page returns the answered "Time In" bucket directly.

Usage:
  KNOWLEDGEFORCE_USERNAME=fg2065@estep-co.com \\
  KNOWLEDGEFORCE_PASSWORD=xxx \\
  python scraper/scrape_visit_time.py --store 2065 [--all]

By default, only fills `visit_window` on shops missing it. Pass --all to
re-scrape every shop.

Output: updates `visit_window` in-place inside the latest shops.json.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse as up
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = ROOT / "data" / "raw" / "marketforce"

BASE = "https://www.knowledgeforce.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 KnowledgeForceAPIClient/1.0"

# KnowledgeForce assignment view URL — contains answered Time In bucket in page HTML.
# Confirmed 2026-05-14: text pattern "Time In: (Mark one only:) <bucket>"
ASSIGNMENT_VIEW = BASE + "/reporting/assignment/view?dataset={dataset}"


def log(msg: str) -> None:
    print(f"[visit-time] {msg}", flush=True)


def login(s: requests.Session, user: str, pw: str) -> bool:
    r = s.get(BASE + "/", timeout=30)
    r.raise_for_status()
    m = re.search(r'name="_csrf"[^>]*value="([^"]+)"', r.text)
    if not m:
        log("no _csrf token on landing page")
        return False
    csrf = m.group(1)
    payload = {"_csrf": csrf, "Login[username]": user, "Login[password]": pw}
    r = s.post(BASE + "/", data=payload, timeout=30, allow_redirects=True)
    r.raise_for_status()
    if "/login" in r.url.lower() or 'name="Login[username]"' in r.text[:5000]:
        log(f"login failed — final URL {r.url}")
        return False
    log(f"login OK — {r.url}")
    return True


def fetch_visit_window_api(s: requests.Session, shop: dict) -> list[float] | None:
    """
    Fetch the visit-time bucket for a single shop via the assignment view page.

    Endpoint: GET /reporting/assignment/view?dataset={"jid":<jid>,"period2":[<period2>]}

    HTML structure (confirmed 2026-05-14):
      "Time In: (Mark one only:) ...</div>
      <div class="question-choices">
        <ul class="fa-ul">
          <li class="question-answer"><i ...></i>4 pm-6:59 pm</li>
        </ul>
      </div>"

    Strategy: find the "Time In" question block, then grab the first
    `question-answer` li text that follows it.

    Returns [start_hour_decimal, end_hour_decimal] or None.
    """
    jid = shop.get("job_id")
    period2 = shop.get("period2")
    if not jid or not period2:
        return None

    dataset = json.dumps({"jid": int(jid), "period2": [int(period2)]})
    url = BASE + "/reporting/assignment/view?dataset=" + up.quote(dataset)
    try:
        r = s.get(url, timeout=30)
        r.raise_for_status()
    except Exception as e:
        log(f"  shop {jid}: request error: {e}")
        return None

    txt = r.text

    # Find "Time In:" in the page, then search for the first question-answer li after it
    idx = txt.find("Time In:")
    if idx < 0:
        log(f"  shop {jid}: 'Time In' label not found in page")
        return None

    # Grab the HTML from after the Time In label through the next 2000 chars
    chunk = txt[idx:idx + 2000]

    # Extract the answer text from <li class="question-answer">...<i ...></i>ANSWER</li>
    m = re.search(
        r'class="question-answer"[^>]*>.*?<i[^>]*></i>([^<]+)</li>',
        chunk,
        re.IGNORECASE | re.DOTALL,
    )
    if not m:
        log(f"  shop {jid}: question-answer li not found after 'Time In'")
        return None

    bucket_raw = m.group(1).strip()
    win = parse_bucket(bucket_raw)
    if win:
        log(f"  shop {jid} ({shop.get('date')} {shop.get('meal_period')}): "
            f"'{bucket_raw}' -> {win}")
    else:
        log(f"  shop {jid}: could not parse bucket '{bucket_raw}'")
    return win


def parse_bucket(text: str) -> list[float] | None:
    """
    Parse a bucket label like '4 pm-6:59 pm' or '11 am-1:30 pm' into
    [start_hour_decimal, end_hour_decimal]. Rounds end :59 up to next hour.
    """
    pattern = (
        r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)\s*[-–]\s*"
        r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)"
    )
    m = re.search(pattern, text, re.IGNORECASE)
    if not m:
        return None
    sh, sm, sa, eh, em, ea = m.groups()

    def to_24(h, mm, ampm):
        h = int(h)
        mm = int(mm) if mm else 0
        if ampm.lower() == "pm" and h != 12:
            h += 12
        if ampm.lower() == "am" and h == 12:
            h = 0
        return h + mm / 60.0

    start = to_24(sh, sm, sa)
    end = to_24(eh, em, ea)
    # Round end :59 up to next hour
    if abs(end - round(end)) > 0.4:
        end = round(end + 0.5)
    return [start, end]


def find_latest_shops_json(store_id: str) -> Path | None:
    store_dir = DATA_ROOT / store_id
    if not store_dir.exists():
        return None
    for d in sorted((x for x in store_dir.iterdir() if x.is_dir()), reverse=True):
        p = d / "shops.json"
        if p.exists():
            return p
    return None


def load_overrides(store_id: str) -> dict[str, list[float]]:
    """
    Auto-populated last-resort cache for shops where the assignment page
    returns no Time In answer (e.g., shop not yet scored, page unavailable).
    This file is NEVER hand-entered — it is written by the pipeline when
    the API path fails. Format: { job_id: [start_hour, end_hour] }.
    """
    p = DATA_ROOT / store_id / "visit_window_overrides.json"
    if not p.exists():
        return {}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return {k: v for k, v in d.items() if not k.startswith("_")}
    except Exception:
        return {}


def save_overrides(store_id: str, overrides: dict) -> None:
    p = DATA_ROOT / store_id / "visit_window_overrides.json"
    comment = (
        "Auto-populated cache: visit_window for shops where KnowledgeForce "
        "assignment view returned no Time In answer. "
        "Written by scrape_visit_time.py. DO NOT hand-edit — "
        "the pipeline populates this from KF data automatically."
    )
    out = {"_comment": comment}
    out.update(overrides)
    p.write_text(json.dumps(out, indent=2), encoding="utf-8")


def run(store_id: str, do_all: bool) -> int:
    user = os.environ.get("KNOWLEDGEFORCE_USERNAME", "")
    pw = os.environ.get("KNOWLEDGEFORCE_PASSWORD", "")
    if not user or not pw:
        log("KNOWLEDGEFORCE_USERNAME / KNOWLEDGEFORCE_PASSWORD required")
        return 1

    shops_path = find_latest_shops_json(store_id)
    if not shops_path:
        log(f"No shops.json found for store {store_id}")
        return 1

    data = json.loads(shops_path.read_text(encoding="utf-8"))
    shops = data.get("shops", [])
    overrides = load_overrides(store_id)

    targets = [s for s in shops if do_all or "visit_window" not in s]
    log(f"Found {len(shops)} shops; {len(targets)} need visit_window")

    if not targets:
        log("Nothing to scrape.")
        return 0

    s = requests.Session()
    s.headers.update({"User-Agent": UA})

    if not login(s, user, pw):
        return 1

    updated_overrides = dict(overrides)

    for shop in targets:
        jid = str(shop.get("job_id"))

        # Try KF assignment view first (primary path)
        win = fetch_visit_window_api(s, shop)
        if win:
            shop["visit_window"] = win
            shop["visit_window_source"] = "knowledgeforce"
            # If we now have the real answer, remove any stale override cache entry
            updated_overrides.pop(jid, None)
        elif jid in overrides:
            # Fall back to cached override (last-resort, auto-populated)
            shop["visit_window"] = overrides[jid]
            shop["visit_window_source"] = "knowledgeforce_cached"
            log(f"  shop {jid}: using cached override {overrides[jid]}")
        else:
            log(f"  shop {jid}: no visit_window found, leaving absent")

    # Persist updated overrides (removes entries where API now returns a live answer)
    save_overrides(store_id, updated_overrides)

    shops_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    filled = sum(1 for s in shops if "visit_window" in s)
    log(f"Wrote {shops_path}; {filled}/{len(shops)} shops have visit_window")
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", default=os.environ.get("STORE_ID", "2065"))
    parser.add_argument("--all", action="store_true",
                        help="Re-scrape visit_window even if already present")
    args = parser.parse_args()
    sys.exit(run(args.store, args.all))
