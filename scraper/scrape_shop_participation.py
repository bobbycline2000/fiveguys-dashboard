#!/usr/bin/env python3
"""
Pull CrunchTime Consolidated Employee Time Detail (CETD) for every secret
shop in shops.json and persist a per-shop employee participation list.

STRICT on-clock rule (rewritten 2026-09-24 after a live 3-month audit,
Bobby's directive): "employee must be on the clock AT THAT TIME on the
shop." KnowledgeForce does NOT expose a numeric visit timestamp anywhere in
the shop payload -- confirmed by exhaustively searching every comment/
narrative field and the page header/metadata for every shop in the audit
window. The only time signal is the "Time In" question -- a 2.5-3hr bucket
(e.g. "4 pm-6:59 pm"), not an instant.

Because we cannot pin an exact instant, an employee is included as
CONFIRMED only when ONE of these holds:
  1. A single punch interval FULLY covers the visit_window bucket
     (timeIn <= win_s AND timeOut >= win_e) -- they were on the clock for
     the entire bucket, so certainly on the clock at the true (unknown)
     visit instant, wherever it fell.
  2. They are the person named in the shop's "Cashier" free-text answer
     (Q64 on the KnowledgeForce survey) AND their punch record shows any
     overlap with the bucket at all (proof they were clocked in, not
     entirely absent that day). The Cashier answer is a first-hand,
     shopper-supplied identification of who served them -- stronger
     evidence than any time-overlap inference.
Everyone else who merely overlaps the bucket (without full coverage and
without being the named cashier) is a ONLY a candidate -- NOT included in
by_shop, NOT silently dropped either: written to shop_verification.json
with their punch intervals so a human can review. Every shop is flagged
verification_status="UNVERIFIED-EXACT-TIME" because KF never gives an
exact instant; exact_time/exact_time_source are populated only if a future
KF payload change ever exposes one.

Incremental: skips shops already present in participation.json.

Usage:
  CRUNCHTIME_USERNAME=BOBBY.CLINE CRUNCHTIME_PASSWORD=xxx \\
  KNOWLEDGEFORCE_USERNAME=fg2065@estep-co.com KNOWLEDGEFORCE_PASSWORD=xxx \\
      python scraper/scrape_shop_participation.py --store 2065 [--all]

Output: data/raw/marketforce/<store>/participation.json
  {
    "by_shop": { "<job_id>": ["FirstName", ...], ... },   # CONFIRMED only
    "updated": "<ISO timestamp>"
  }
Also writes/merges data/raw/marketforce/<store>/shop_verification.json with
the full audit trail (bucket, cashier, confirmed vs candidate, punch times).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import urllib.parse as up
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = ROOT / "data" / "raw" / "marketforce"
DEBUG_LOG = ROOT / "data" / "debug-log.txt"

ET = timezone(timedelta(hours=-4))

sys.path.insert(0, str(Path(__file__).parent))
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from main import NETCHEF_BASE, USERNAME, PASSWORD, do_login, select_location
from scrape_shop_payout_email import (
    _navigate_to_time_detail,
    _set_date_and_retrieve,
)

import requests

KF_BASE = "https://www.knowledgeforce.com"
KF_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 KnowledgeForceAPIClient/1.0"

# ── Roster (matches build_shop_tracker) ────────────────────────────────────
ROSTER = [
    "Alen", "Anthony", "Ash", "Autumn", "Bobby", "Bri", "Christopher", "Cortez",
    "DJuan", "Dakayla", "Damon", "Divan", "Emanuela", "Francisco", "Grace",
    "Heather", "Jada", "Javeh", "Jeremiah", "Kable", "Kaisha", "Kasey", "Kayla",
    "Kenzie", "Lidy", "Madelynn", "Madison", "Maylin", "Mike", "Mykenize",
    "Nathan", "Nyatiek", "Richard", "Rusul", "Ryan", "Samuel", "Serina", "Vicki",
    "Zach",
]
# Robert → Bobby: CrunchTime stores Bobby as "Cline, Robert" but roster uses "Bobby".
NICK = {"Michael": "Mike", "Mickey": "Mike", "Ashton": "Ash", "Ashley": "Ash",
        "Brianna": "Bri", "Robert": "Bobby", "Ailen": "Alen", "Zack": "Zach",
        "DaKayla": "Dakayla"}

# Default windows by meal_period when visit_window is absent.
# These must stay in sync with MEAL_WINDOWS in scrape_shop_payout_email.py.
# Dinner = 15:00-22:00 covers 3pm-open Shift Lead through close crew.
# Lunch  = 11:00-15:00 covers lunch rush through mid-afternoon.
# Using float hours for overlap math (e.g. 15.5 = 3:30 PM).
DEFAULT_WIN = {
    "breakfast":   (5.0,  11.0),
    "lunch":       (11.0, 15.0),
    "dinner":      (15.0, 22.0),
    "late dinner": (19.0, 23.0),
}
# Roster-key casing differences between the CETD-literal first name and the
# roster_key used by build_shop_tracker.py's CREW/MANAGERS arrays.
ROSTER_KEY_OVERRIDE = {"zack": "Zach", "dakayla": "Dakayla", "brianna": "Bri",
                        "ailen": "Alen", "robert": "Bobby"}


def _load_name_map() -> dict:
    p = ROOT / "data" / "employee_name_map.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


NAME_MAP = _load_name_map()
NAME_MAP_LOWER = {k.lower(): v for k, v in NAME_MAP.items() if "UNRESOLVED" not in v}
KEY_BY_LOWER = {k.lower(): k for k in NAME_MAP if "UNRESOLVED" not in NAME_MAP.get(k, "")}


def resolve_full_name(first: str | None) -> str | None:
    if not first:
        return None
    lo = first.lower()
    if lo in NAME_MAP_LOWER:
        return NAME_MAP_LOWER[lo]
    for k, v in NAME_MAP_LOWER.items():
        if k.startswith(lo) or lo.startswith(k):
            return v
    return None


def to_roster_key(first: str | None) -> str | None:
    """First name (as extracted from CETD) -> roster_key used by
    build_shop_tracker.py's CREW/MANAGERS arrays."""
    if not first:
        return None
    lo = first.lower()
    if lo in ROSTER_KEY_OVERRIDE:
        return ROSTER_KEY_OVERRIDE[lo]
    if lo in KEY_BY_LOWER:
        return KEY_BY_LOWER[lo]
    if lo in ROSTER:
        return first
    return None


def kf_login(s: "requests.Session") -> bool:
    user = os.environ.get("KNOWLEDGEFORCE_USERNAME", "")
    pw = os.environ.get("KNOWLEDGEFORCE_PASSWORD", "")
    if not user or not pw:
        return False
    r = s.get(KF_BASE + "/", timeout=30)
    m = re.search(r'name="_csrf"[^>]*value="([^"]+)"', r.text)
    if not m:
        return False
    csrf = m.group(1)
    payload = {"_csrf": csrf, "Login[username]": user, "Login[password]": pw}
    r = s.post(KF_BASE + "/", data=payload, timeout=30, allow_redirects=True)
    return "/reporting/reports/dashboard" in r.url


def fetch_cashier_name(s: "requests.Session", shop: dict) -> str | None:
    """
    Fetch the shop's Q64 'Cashier:' free-text answer via the same assignment
    view page used for visit_window (scrape_visit_time.py). Returns the raw
    text (e.g. 'Elizabeth B') or None if the question wasn't answered /
    page structure doesn't match. Never guesses -- returns None on any
    ambiguity.
    """
    jid = shop.get("job_id")
    period2 = shop.get("period2")
    if not jid or not period2:
        return None
    dataset = json.dumps({"jid": int(jid), "period2": [int(period2)]})
    url = KF_BASE + "/reporting/assignment/view?dataset=" + up.quote(dataset)
    try:
        r = s.get(url, timeout=30)
        r.raise_for_status()
    except Exception:
        return None
    idx = r.text.find("64. Cashier")
    if idx < 0:
        return None
    chunk = r.text[idx:idx + 800]
    chunk = chunk.replace("’", "'")
    m = re.search(r'Comments:\|?"\s*([^"]*?)\s*"', re.sub(r"<[^>]+>", "|", chunk))
    return m.group(1).strip() if m and m.group(1).strip() else None


def _cashier_first_name(raw: str | None) -> str | None:
    if not raw:
        return None
    raw = raw.replace("’", "'")
    first = re.split(r"[\s.]", raw.strip())[0]
    first = re.sub(r"'s$", "", first, flags=re.I).strip("'")
    return first or None


def log(msg: str) -> None:
    print(f"[shop-participation] {msg}".encode("ascii", "replace").decode("ascii"), flush=True)


def append_debug_log(msg: str) -> None:
    now = datetime.now(tz=ET).strftime("%Y-%m-%d %H:%M:%S")
    DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
    with DEBUG_LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{now}] shop-participation: {msg}\n")


def find_latest_shops_json(store_id: str) -> Path | None:
    store_dir = DATA_ROOT / store_id
    if not store_dir.exists():
        return None
    for d in sorted((x for x in store_dir.iterdir() if x.is_dir()), reverse=True):
        p = d / "shops.json"
        if p.exists():
            return p
    return None


def load_existing(store_id: str) -> dict:
    p = DATA_ROOT / store_id / "participation.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"by_shop": {}, "updated": None}


def save_participation(store_id: str, data: dict) -> Path:
    p = DATA_ROOT / store_id / "participation.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    data["updated"] = datetime.now(tz=ET).isoformat(timespec="seconds")
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return p


def first_name(emp_str: str) -> str | None:
    m = re.match(r"^([^,]+),\s+([^\s-]+)", emp_str)
    return m.group(2) if m else None


def match_to_roster(first: str | None) -> str | None:
    if not first:
        return None
    if first in ROSTER:
        return first
    if first in NICK:
        return NICK[first]
    lo = first.lower()
    for r in ROSTER:
        if r.lower() == lo or lo.startswith(r.lower()):
            return r
    return None


def parse_hour(t: str) -> float | None:
    if not t:
        return None
    m = re.match(r"(\d+):(\d+)", t)
    return int(m.group(1)) + int(m.group(2)) / 60.0 if m else None


def shop_window(shop: dict) -> tuple[float, float]:
    vw = shop.get("visit_window")
    if vw and len(vw) == 2:
        return float(vw[0]), float(vw[1])
    meal = (shop.get("meal_period") or "").lower()
    for k, v in DEFAULT_WIN.items():
        if k in meal:
            return v
    return (0.0, 23.99)


async def extract_records(page) -> list[dict]:
    """Pull CETD grid store records via JS."""
    return await page.evaluate(r"""
        () => {
            const grid = Ext.ComponentQuery.query('consolidatedemployeetimedetail-summarygrid')[0];
            if (!grid) return [];
            return grid.getStore().getRange().map(r => ({
                employee: r.get('employeeName'),
                timeIn: r.get('timeIn'),
                timeOut: r.get('timeOut'),
                hours: r.get('totalTime'),
                rowType: r.get('rowType')
            }));
        }
    """)


async def clear_grid(page) -> None:
    await page.evaluate("""
        () => {
            const g = Ext.ComponentQuery.query('consolidatedemployeetimedetail-summarygrid')[0];
            if (g) g.getStore().removeAll();
        }
    """)


def filter_to_roster(records: list[dict], window: tuple[float, float],
                      cashier_raw: str | None) -> tuple[list[str], list[dict], dict]:
    """
    Returns (confirmed_roster_keys, candidate_list, cashier_info).

    confirmed = full-bucket-coverage people UNION the named Cashier (if
    resolvable and clocked in with any overlap). candidate_list = everyone
    else with partial overlap only, each with their raw punch intervals, so
    nobody is silently dropped even though they aren't auto-credited.
    See module docstring for the full rule (rewritten 2026-09-24).
    """
    win_s, win_e = window
    by_emp: dict[str, list[dict]] = {}
    for r in records:
        if r.get("rowType") != "regular":
            continue
        if not r.get("timeIn") or r["timeIn"] == "00:00":
            continue
        by_emp.setdefault(r["employee"], []).append(r)

    full: dict[str, list[list[float]]] = {}
    partial: dict[str, list[list[float]]] = {}
    for emp_str, shifts in by_emp.items():
        intervals = []
        covers = False
        for s in shifts:
            t_in = parse_hour(s.get("timeIn"))
            t_out = parse_hour(s.get("timeOut"))
            if t_in is None or t_out is None or t_out < t_in:
                continue
            intervals.append([t_in, t_out])
            if t_in <= win_s and t_out >= win_e:
                covers = True
        if not intervals:
            continue
        overlaps = any(min(iv[1], win_e) > max(iv[0], win_s) for iv in intervals)
        if covers:
            full[emp_str] = intervals
        elif overlaps:
            partial[emp_str] = intervals

    confirmed: dict[str, str] = {}  # roster_key -> raw emp_str (for logging)
    for emp_str in full:
        rk = to_roster_key(first_name(emp_str))
        if rk:
            confirmed[rk] = emp_str

    cashier_first = _cashier_first_name(cashier_raw)
    cashier_full_name = resolve_full_name(cashier_first)
    cashier_confirmed = False
    cashier_rk = None
    if cashier_full_name:
        cashier_token = cashier_full_name.split()[0].lower()
        for emp_str in list(full.keys()) + list(partial.keys()):
            efirst = first_name(emp_str) or ""
            if efirst.lower() == (cashier_first or "").lower() or \
               (resolve_full_name(efirst) or "").split()[0].lower() == cashier_token:
                rk = to_roster_key(efirst)
                if rk:
                    confirmed[rk] = emp_str
                    cashier_rk = rk
                    cashier_confirmed = True
                break

    candidates = []
    for emp_str, intervals in partial.items():
        rk = to_roster_key(first_name(emp_str))
        if rk and rk in confirmed:
            continue
        candidates.append({"employee": emp_str, "intervals": intervals})

    cashier_info = {
        "cashier_raw": cashier_raw,
        "cashier_resolved": cashier_full_name,
        "cashier_confirmed_on_clock": cashier_confirmed,
    }
    return sorted(confirmed.keys()), candidates, cashier_info


def load_verification(store_id: str) -> dict:
    p = DATA_ROOT / store_id / "shop_verification.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_verification(store_id: str, data: dict) -> Path:
    p = DATA_ROOT / store_id / "shop_verification.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return p


VERIFICATION_NOTE = (
    "KnowledgeForce does not expose a numeric visit timestamp anywhere in the "
    "shop payload (confirmed by full-text search across all comment/narrative "
    "fields and the page header) -- only a 2.5-3hr Time-In bucket. The "
    "'Cashier' free-text answer (Q64) names who was working the register at "
    "the moment of the visit and is treated as a direct on-clock confirmation "
    "when that person's CrunchTime punch overlaps the bucket at all. Everyone "
    "else who merely overlaps the bucket (without full coverage or being the "
    "named cashier) is listed as an unverified candidate, not silently "
    "dropped and not auto-credited."
)


async def run(store_id: str, do_all: bool) -> int:
    shops_path = find_latest_shops_json(store_id)
    if not shops_path:
        log(f"No shops.json for store {store_id}")
        return 1

    data = json.loads(shops_path.read_text(encoding="utf-8"))
    shops = data.get("shops", [])

    existing = load_existing(store_id)
    by_shop = existing.get("by_shop", {})
    verification = load_verification(store_id)

    targets = [s for s in shops if do_all or s["job_id"] not in by_shop]
    log(f"{len(shops)} shops total; {len(targets)} need participation pull")

    if not targets:
        save_participation(store_id, {"by_shop": by_shop})
        return 0

    if not USERNAME or not PASSWORD:
        log("CRUNCHTIME_USERNAME / CRUNCHTIME_PASSWORD required")
        return 1

    kf_session = requests.Session()
    kf_session.headers.update({"User-Agent": KF_UA})
    kf_ok = kf_login(kf_session)
    if not kf_ok:
        log("WARNING: KnowledgeForce login failed -- cashier cross-check will be skipped "
            "for this run (confirmed list will be full-coverage only, candidates still recorded)")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1600, "height": 1000})
        page = await ctx.new_page()
        try:
            await page.goto(NETCHEF_BASE, wait_until="domcontentloaded", timeout=30_000)
            if not await do_login(page):
                log("Login failed")
                return 1
            await select_location(page)
            await page.wait_for_timeout(5_000)

            if not await _navigate_to_time_detail(page):
                log("Could not navigate to CETD")
                return 1

            for shop in targets:
                job_id = shop["job_id"]
                d = date.fromisoformat(shop["date"])
                ct_date = f"{d.month}/{d.day}/{d.year}"
                log(f"  shop {job_id} ({shop['date']} {shop.get('meal_period')}) → {ct_date}")
                await clear_grid(page)
                ok = await _set_date_and_retrieve(page, ct_date)
                if not ok:
                    log(f"    retrieve failed; skipping")
                    continue
                await page.wait_for_timeout(1500)
                records = await extract_records(page)
                window = shop_window(shop)

                cashier_raw = fetch_cashier_name(kf_session, shop) if kf_ok else None
                names, candidates, cashier_info = filter_to_roster(records, window, cashier_raw)
                by_shop[job_id] = names
                verification[job_id] = {
                    "date": shop.get("date"), "meal_period": shop.get("meal_period"),
                    "score": shop.get("score"),
                    "visit_window_bucket": None,  # raw bucket text not re-fetched here; see shops.json visit_window
                    "visit_window_hours": list(window),
                    "verification_status": "UNVERIFIED-EXACT-TIME",
                    "exact_time": None, "exact_time_source": None,
                    "verification_note": VERIFICATION_NOTE,
                    **cashier_info,
                    "confirmed_on_clock": names,
                    "unverified_candidates": candidates,
                }
                log(f"    window {window[0]:.1f}-{window[1]:.1f}: {len(names)} confirmed: {names} "
                    f"| cashier={cashier_info['cashier_resolved']} "
                    f"confirmed={cashier_info['cashier_confirmed_on_clock']} "
                    f"| {len(candidates)} unverified candidate(s)")
                if not names and float(shop.get("score", 0)) == 100.0:
                    msg = f"ZERO_NAMES_100PCT_SHOP job_id={job_id} ({shop.get('date')} {shop.get('meal_period')})"
                    log(f"    WARNING: {msg}")
                    append_debug_log(msg)

        finally:
            await browser.close()

    out = save_participation(store_id, {"by_shop": by_shop})
    save_verification(store_id, verification)
    log(f"Wrote {out} ({len(by_shop)} shops)")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", default=os.environ.get("STORE_ID", "2065"))
    parser.add_argument("--all", action="store_true",
                        help="Re-pull participation for shops already cached")
    args = parser.parse_args()
    sys.exit(asyncio.run(run(args.store, args.all)))
