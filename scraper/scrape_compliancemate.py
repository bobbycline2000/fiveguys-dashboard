"""
ComplianceMate scraper — extracts temperature readings and checklist
completion for Five Guys location 2065.

Saves results to data/compliancemate.json.
Debug artifacts: data/cm_*.png, data/cm_page_source.html
"""

import asyncio
import json
import logging
import os
import re
import sys
from datetime import datetime, date
from pathlib import Path

from playwright.async_api import async_playwright, TimeoutError as PWTimeout

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

USERNAME = os.getenv("COMPLIANCEMATE_USERNAME", "")
PASSWORD = os.getenv("COMPLIANCEMATE_PASSWORD", "")
BASE_URL  = "https://fg-beta.compliancemate.com"
DATA_DIR  = Path(__file__).parent.parent / "data"
TODAY     = date.today()
TODAY_STR = TODAY.strftime("%Y-%m-%d")

EMPTY_DATA = {
    "meta": {
        "date": TODAY_STR,
        "generated": datetime.now().strftime("%-m/%-d/%Y at %-I:%M %p"),
        "location": "2065",
        "status": "no_data",
    },
    "temperatures": [],
    "checklists": {
        "am":           {"name": "AM Opening",   "completed": 0, "total": 0, "pct": 0, "status": "pending"},
        "pm":           {"name": "PM Closing",   "completed": 0, "total": 0, "pct": 0, "status": "pending"},
        "shift_change": {"name": "Shift Change", "completed": 0, "total": 0, "pct": 0, "status": "pending"},
    },
}


# ── helpers ────────────────────────────────────────────────────────────────────

async def try_fill(page, selectors: list[str], value: str) -> bool:
    for sel in selectors:
        try:
            await page.fill(sel, value, timeout=3000)
            log.info(f"  filled {sel!r}")
            return True
        except Exception:
            continue
    return False


async def try_click(page, selectors: list[str]) -> bool:
    for sel in selectors:
        try:
            await page.click(sel, timeout=3000)
            log.info(f"  clicked {sel!r}")
            return True
        except Exception:
            continue
    return False


def pct(completed, total):
    return round(completed / total * 100) if total else 0


def checklist_status(p):
    if p == 0:
        return "pending"
    if p >= 100:
        return "complete"
    return "incomplete"


# ── login ──────────────────────────────────────────────────────────────────────

async def do_login(page) -> bool:
    log.info("=== Login ===")
    await page.goto(BASE_URL, timeout=30000, wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)
    await page.screenshot(path=str(DATA_DIR / "cm_01_login_page.png"))

    filled = await try_fill(page, [
        'input[type="email"]',
        'input[name="email"]',
        'input[id="email"]',
        'input[name="username"]',
        'input[id="username"]',
        'input[placeholder*="email" i]',
        'input[name="user[email]"]',
    ], USERNAME)

    if not filled:
        log.error("Could not find email/username field")
        (DATA_DIR / "cm_page_source.html").write_text(await page.content(), encoding="utf-8")
        return False

    await try_fill(page, [
        'input[type="password"]',
        'input[name="password"]',
        'input[id="password"]',
        'input[name="user[password]"]',
    ], PASSWORD)

    # submit
    submitted = await try_click(page, [
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("Sign in")',
        'button:has-text("Log in")',
        'button:has-text("Login")',
        'a:has-text("Sign in")',
    ])
    if not submitted:
        await page.keyboard.press("Enter")

    await page.wait_for_load_state("networkidle", timeout=15000)
    await page.screenshot(path=str(DATA_DIR / "cm_02_after_login.png"))
    log.info(f"Post-login URL: {page.url}")

    # save source for debugging
    (DATA_DIR / "cm_page_source.html").write_text(await page.content(), encoding="utf-8")
    return True


# ── temperature extraction ─────────────────────────────────────────────────────

async def extract_temperatures(page) -> list[dict]:
    """Try multiple strategies to pull today's temperature readings."""
    temps = []

    # Strategy 1: look for a <table> with temperature data
    try:
        rows = await page.query_selector_all("table tr")
        for row in rows:
            cells = await row.query_selector_all("td")
            if len(cells) >= 2:
                texts = [await c.inner_text() for c in cells]
                joined = " ".join(texts)
                if re.search(r"\d+(\.\d+)?°?[FC]", joined, re.I) or re.search(r"\d+(\.\d+)?\s*(deg|°)", joined, re.I):
                    entry = {
                        "item":   texts[0].strip() if len(texts) > 0 else "—",
                        "reading": texts[1].strip() if len(texts) > 1 else "—",
                        "time":   texts[2].strip() if len(texts) > 2 else "—",
                        "status": "pass",
                    }
                    # check for fail indicators
                    full = joined.lower()
                    if any(w in full for w in ["fail", "out of range", "exceeded", "high", "low alert"]):
                        entry["status"] = "fail"
                    temps.append(entry)
        if temps:
            log.info(f"Strategy 1 found {len(temps)} temperature rows")
            return temps
    except Exception as e:
        log.warning(f"Temperature strategy 1 failed: {e}")

    # Strategy 2: scan page text for temperature patterns
    try:
        body_text = await page.inner_text("body")
        lines = body_text.splitlines()
        for line in lines:
            if re.search(r"\d+(\.\d+)?°?[FC]", line) and len(line.strip()) > 3:
                temps.append({"item": line.strip(), "reading": "—", "time": "—", "status": "unknown"})
        if temps:
            log.info(f"Strategy 2 found {len(temps)} temperature lines")
            return temps[:20]
    except Exception as e:
        log.warning(f"Temperature strategy 2 failed: {e}")

    log.warning("No temperature data found")
    return []


# ── checklist extraction ───────────────────────────────────────────────────────

async def extract_checklists(page) -> dict:
    checklists = {
        "am":           {"name": "AM Opening",   "completed": 0, "total": 0, "pct": 0, "status": "pending"},
        "pm":           {"name": "PM Closing",   "completed": 0, "total": 0, "pct": 0, "status": "pending"},
        "shift_change": {"name": "Shift Change", "completed": 0, "total": 0, "pct": 0, "status": "pending"},
    }

    try:
        body_text = (await page.inner_text("body")).lower()

        # look for percentage patterns near AM/PM/shift keywords
        patterns = [
            (r"am\s+opening[^\n]*?(\d+)\s*/\s*(\d+)", "am"),
            (r"opening[^\n]*?(\d+)\s*/\s*(\d+)",       "am"),
            (r"am[^\n]*?(\d{1,3})%",                   "am"),
            (r"pm\s+closing[^\n]*?(\d+)\s*/\s*(\d+)",  "pm"),
            (r"closing[^\n]*?(\d+)\s*/\s*(\d+)",       "pm"),
            (r"pm[^\n]*?(\d{1,3})%",                   "pm"),
            (r"shift\s+change[^\n]*?(\d+)\s*/\s*(\d+)", "shift_change"),
            (r"shift[^\n]*?(\d+)\s*/\s*(\d+)",          "shift_change"),
        ]

        for pattern, key in patterns:
            m = re.search(pattern, body_text)
            if m:
                groups = m.groups()
                if len(groups) == 2:
                    completed, total = int(groups[0]), int(groups[1])
                    p = pct(completed, total)
                elif len(groups) == 1:
                    p, completed, total = int(groups[0]), 0, 0
                else:
                    continue
                if checklists[key]["pct"] == 0:
                    checklists[key].update({
                        "completed": completed,
                        "total": total,
                        "pct": p,
                        "status": checklist_status(p),
                    })
                    log.info(f"  {key}: {completed}/{total} ({p}%)")

    except Exception as e:
        log.warning(f"Checklist extraction failed: {e}")

    return checklists


# ── navigate to today's report ─────────────────────────────────────────────────

async def navigate_to_today(page) -> bool:
    """Try to navigate to location 2065's daily report for today."""
    log.info("=== Navigating to today's data ===")

    # try common URL patterns for ComplianceMate
    candidate_paths = [
        "/dashboard",
        "/reports",
        "/daily",
        "/logs",
        f"/locations/2065",
        f"/reports?location=2065",
        f"/daily_report?date={TODAY_STR}",
    ]

    for path in candidate_paths:
        try:
            url = BASE_URL + path
            resp = await page.goto(url, timeout=10000, wait_until="domcontentloaded")
            if resp and resp.status < 400:
                log.info(f"Reached {url}")
                await page.wait_for_timeout(2000)
                await page.screenshot(path=str(DATA_DIR / "cm_03_data_page.png"))
                return True
        except Exception:
            continue

    # fall back — just use whatever page we're on after login
    log.warning("Could not navigate to specific report; using post-login page")
    await page.screenshot(path=str(DATA_DIR / "cm_03_data_page.png"))
    return False


# ── main scrape ────────────────────────────────────────────────────────────────

async def scrape() -> dict:
    if not USERNAME or not PASSWORD:
        log.error("Set COMPLIANCEMATE_USERNAME and COMPLIANCEMATE_PASSWORD env vars")
        return EMPTY_DATA

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        try:
            ok = await do_login(page)
            if not ok:
                return EMPTY_DATA

            await navigate_to_today(page)

            # save full page text for debugging
            page_text = await page.inner_text("body")
            (DATA_DIR / "cm_page_text.txt").write_text(page_text, encoding="utf-8")

            temps      = await extract_temperatures(page)
            checklists = await extract_checklists(page)

            status = "ok" if (temps or any(v["pct"] > 0 for v in checklists.values())) else "login_ok_no_data"

            return {
                "meta": {
                    "date":      TODAY_STR,
                    "generated": datetime.now().strftime("%-m/%-d/%Y at %-I:%M %p"),
                    "location":  "2065",
                    "status":    status,
                },
                "temperatures": temps,
                "checklists":   checklists,
            }

        except Exception as e:
            log.error(f"Scrape failed: {e}")
            await page.screenshot(path=str(DATA_DIR / "cm_error.png"))
            return EMPTY_DATA
        finally:
            await browser.close()


if __name__ == "__main__":
    DATA_DIR.mkdir(exist_ok=True)
    data = asyncio.run(scrape())
    out = Path(__file__).parent.parent / "data" / "compliancemate.json"
    out.write_text(json.dumps(data, indent=2))
    log.info(f"Saved {out}")
    log.info(f"Status: {data['meta']['status']}")
    log.info(f"Temperatures: {len(data['temperatures'])}")
    log.info(f"Checklists: AM={data['checklists']['am']['pct']}%  PM={data['checklists']['pm']['pct']}%  Shift={data['checklists']['shift_change']['pct']}%")
