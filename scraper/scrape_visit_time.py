#!/usr/bin/env python3
"""
Scrape Marketforce shop visit-time buckets from KnowledgeForce.

For each shop in the latest shops.json that lacks `visit_window`, navigate
to the Question Results page filtered to that shop and extract the
`.04 Time In` bucket (e.g., "4 pm-6:59 pm" → [16.0, 19.0]).

This is the missing piece that lets the Shop Tracker apply the actual
shop visit window (not the broad meal-period label) when computing
employee participation.

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
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = ROOT / "data" / "raw" / "marketforce"

LOGIN_URL = "https://www.knowledgeforce.com/"
TIME_IN_CQID = "494864"  # KnowledgeForce question id for ".04 Time In"
SCHEME = "5304"


def log(msg: str) -> None:
    print(f"[visit-time] {msg}", flush=True)


def login(page, username: str, password: str) -> bool:
    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30_000)
    try:
        page.fill('input[name="username"], input[type="text"]:visible', username, timeout=10_000)
        page.fill('input[name="password"], input[type="password"]:visible', password, timeout=10_000)
        page.click('button:has-text("LOG IN"), input[type="submit"]', timeout=10_000)
        page.wait_for_load_state("networkidle", timeout=20_000)
    except PlaywrightTimeout:
        log("Login timed out")
        return False
    if "/login" in page.url.lower() or "username" in page.content().lower()[:5000]:
        return False
    return True


def find_latest_shops_json(store_id: str) -> Path | None:
    store_dir = DATA_ROOT / store_id
    if not store_dir.exists():
        return None
    for d in sorted((x for x in store_dir.iterdir() if x.is_dir()), reverse=True):
        p = d / "shops.json"
        if p.exists():
            return p
    return None


def parse_bucket(text: str) -> list[float] | None:
    """
    Parse a bucket label like '4 pm-6:59 pm' or '11 am-1:30 pm' into
    [start_hour_decimal, end_hour_decimal]. Round end up to next half hour.
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
        h = int(h); mm = int(mm) if mm else 0
        if ampm.lower() == "pm" and h != 12: h += 12
        if ampm.lower() == "am" and h == 12: h = 0
        return h + mm / 60.0

    start = to_24(sh, sm, sa)
    end = to_24(eh, em, ea)
    # Round end up to next full hour if it's :59
    if abs(end - round(end)) > 0.4:
        end = round(end + 0.5)
    return [start, end]


def fetch_visit_window(page, shop: dict) -> list[float] | None:
    """
    Fetch the visit-time bucket for a single shop.
    Strategy: query the Question Results report filtered to cqid (Time In),
    jid (this shop), period2 (the week). Read the page text and find
    the bucket(s) shown. If exactly one bucket has 100%, use it.
    If multiple, fall back to None and let caller use meal-period default.
    """
    jid = shop.get("job_id")
    period2 = shop.get("period2")
    if not jid or not period2:
        return None

    dataset = json.dumps({
        "level": ["all"],
        "cqid": [TIME_IN_CQID],
        "jid": int(jid),
        "period2": [int(period2)],
        "scheme": [int(SCHEME)],
    }, separators=(",", ":"))

    from urllib.parse import quote
    url = (
        "https://www.knowledgeforce.com/reporting/reports/report?"
        f"id=questionresults&dataset={quote(dataset)}"
    )

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_load_state("networkidle", timeout=15_000)
        page.wait_for_timeout(2_500)
    except PlaywrightTimeout:
        log(f"  navigate timeout for shop {jid}")
        return None

    txt = page.evaluate("() => document.body.innerText")

    # Find buckets that look like time ranges
    bucket_re = re.compile(
        r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm)\s*[-–]\s*\d{1,2}(?::\d{2})?\s*(?:am|pm))\b",
        re.IGNORECASE,
    )
    found = bucket_re.findall(txt)
    unique = list(dict.fromkeys(b.strip() for b in found))

    if not unique:
        log(f"  shop {jid} ({shop.get('date')} {shop.get('meal_period')}): no bucket found")
        return None

    # If exactly one bucket appears in the report, that's the answer
    if len(unique) == 1:
        win = parse_bucket(unique[0])
        log(f"  shop {jid} → '{unique[0]}' → {win}")
        return win

    # Multiple buckets: pick the one whose start matches this shop's meal_period
    meal = (shop.get("meal_period") or "").lower()
    candidates = []
    for b in unique:
        win = parse_bucket(b)
        if not win:
            continue
        s, e = win
        # Lunch buckets start 11–13.5; Dinner 16+; Late Dinner 19+
        if meal == "lunch" and 11 <= s <= 16:
            candidates.append((b, win))
        elif meal == "dinner" and 15 <= s <= 22:
            candidates.append((b, win))
        elif "late dinner" in meal and 19 <= s <= 23:
            candidates.append((b, win))

    if len(candidates) == 1:
        b, win = candidates[0]
        log(f"  shop {jid} ({meal}) → '{b}' → {win}  (matched by meal)")
        return win

    log(f"  shop {jid} ({meal}): {len(unique)} buckets, ambiguous: {unique}")
    return None


def run(store_id: str, do_all: bool) -> int:
    user = os.environ.get("KNOWLEDGEFORCE_USERNAME")
    pw = os.environ.get("KNOWLEDGEFORCE_PASSWORD")
    if not user or not pw:
        log("KNOWLEDGEFORCE_USERNAME / KNOWLEDGEFORCE_PASSWORD required")
        return 1

    shops_path = find_latest_shops_json(store_id)
    if not shops_path:
        log(f"No shops.json found for store {store_id}")
        return 1

    data = json.loads(shops_path.read_text(encoding="utf-8"))
    shops = data.get("shops", [])
    targets = [s for s in shops if do_all or "visit_window" not in s]
    log(f"Found {len(shops)} shops; {len(targets)} need visit_window")

    if not targets:
        log("Nothing to do.")
        return 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = ctx.new_page()

        try:
            if not login(page, user, pw):
                log("Login failed")
                return 1
            log("Logged in to KnowledgeForce")

            for shop in targets:
                win = fetch_visit_window(page, shop)
                if win:
                    shop["visit_window"] = win
                    shop["visit_window_source"] = "knowledgeforce"
                # else: leave it absent, downstream uses meal-period default
        finally:
            browser.close()

    # Write back
    shops_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    filled = sum(1 for s in shops if "visit_window" in s)
    log(f"Wrote {shops_path}; {filled}/{len(shops)} shops have visit_window")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", default=os.environ.get("STORE_ID", "2065"))
    parser.add_argument("--all", action="store_true",
                        help="Re-scrape visit_window even if already present")
    args = parser.parse_args()
    sys.exit(run(args.store, args.all))
