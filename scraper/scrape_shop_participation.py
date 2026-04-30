#!/usr/bin/env python3
"""
Pull CrunchTime Consolidated Employee Time Detail (CETD) for every secret
shop in shops.json and persist a per-shop employee participation list.

Filters employees to those whose clock-in/out window has at least 30 min
of overlap with the shop's visit_window (from scrape_visit_time.py). If
visit_window is missing, falls back to the meal-period default window.

Incremental: skips shops already present in participation.json.

Usage:
  CRUNCHTIME_USERNAME=BOBBY.CLINE CRUNCHTIME_PASSWORD=xxx \\
      python scraper/scrape_shop_participation.py --store 2065 [--all]

Output: data/raw/marketforce/<store>/participation.json
  {
    "by_shop": { "<job_id>": ["FirstName", ...], ... },
    "updated": "<ISO timestamp>"
  }
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = ROOT / "data" / "raw" / "marketforce"

ET = timezone(timedelta(hours=-4))

sys.path.insert(0, str(Path(__file__).parent))
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from main import NETCHEF_BASE, USERNAME, PASSWORD, do_login, select_location
from scrape_shop_payout_email import (
    _navigate_to_time_detail,
    _set_date_and_retrieve,
)

# ── Roster (matches build_shop_tracker) ────────────────────────────────────
ROSTER = [
    "Alen", "Ash", "Autumn", "Bri", "Dakayla", "Divan", "Francisco", "Grace",
    "Jada", "Jeremiah", "Kable", "Kasey", "Kayla", "Kenzie", "Lidy", "Madison",
    "Maylin", "Mike", "Nathan", "Richard", "Samuel", "Vicki", "Zach",
]
NICK = {"Michael": "Mike", "Mickey": "Mike", "Ashton": "Ash", "Ashley": "Ash",
        "Brianna": "Bri"}

# Default windows by meal_period when visit_window is absent
DEFAULT_WIN = {
    "lunch":       (11.0, 16.0),
    "dinner":      (16.0, 19.0),
    "late dinner": (19.0, 22.0),
    "breakfast":   (7.0, 10.0),
}
MIN_OVERLAP_HRS = 0.5


def log(msg: str) -> None:
    print(f"[shop-participation] {msg}", flush=True)


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


def filter_to_roster(records: list[dict], window: tuple[float, float]) -> list[str]:
    win_s, win_e = window
    by_emp: dict[str, list[dict]] = {}
    for r in records:
        if r.get("rowType") != "regular":
            continue
        if not r.get("timeIn") or r["timeIn"] == "00:00":
            continue
        by_emp.setdefault(r["employee"], []).append(r)

    matched: set[str] = set()
    for emp_str, shifts in by_emp.items():
        overlap = 0.0
        for s in shifts:
            t_in = parse_hour(s.get("timeIn"))
            t_out = parse_hour(s.get("timeOut"))
            if t_in is None or t_out is None or t_out < t_in:
                continue
            o_s = max(t_in, win_s)
            o_e = min(t_out, win_e)
            if o_e > o_s:
                overlap += (o_e - o_s)
        if overlap < MIN_OVERLAP_HRS:
            continue
        m = match_to_roster(first_name(emp_str))
        if m:
            matched.add(m)
    return sorted(matched)


async def run(store_id: str, do_all: bool) -> int:
    shops_path = find_latest_shops_json(store_id)
    if not shops_path:
        log(f"No shops.json for store {store_id}")
        return 1

    data = json.loads(shops_path.read_text(encoding="utf-8"))
    shops = data.get("shops", [])

    existing = load_existing(store_id)
    by_shop = existing.get("by_shop", {})

    targets = [s for s in shops if do_all or s["job_id"] not in by_shop]
    log(f"{len(shops)} shops total; {len(targets)} need participation pull")

    if not targets:
        save_participation(store_id, {"by_shop": by_shop})
        return 0

    if not USERNAME or not PASSWORD:
        log("CRUNCHTIME_USERNAME / CRUNCHTIME_PASSWORD required")
        return 1

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
                names = filter_to_roster(records, window)
                by_shop[job_id] = names
                log(f"    window {window[0]:.1f}-{window[1]:.1f}: {len(names)} matched: {names}")

        finally:
            await browser.close()

    out = save_participation(store_id, {"by_shop": by_shop})
    log(f"Wrote {out} ({len(by_shop)} shops)")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", default=os.environ.get("STORE_ID", "2065"))
    parser.add_argument("--all", action="store_true",
                        help="Re-pull participation for shops already cached")
    args = parser.parse_args()
    sys.exit(asyncio.run(run(args.store, args.all)))
