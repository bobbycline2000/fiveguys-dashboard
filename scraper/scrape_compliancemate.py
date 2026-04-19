"""
ComplianceMate scraper — extracts checklist completion percentages for
Five Guys location 2065.

Navigation path:
  Login → Statistics → List Completion ALL → Date Range: Yesterday → Apply
  → scroll down → extract list names + completion %

Target lists:
  - Named checklists (AM Opening, PM Closing, Shift Change, etc.)
  - Time-based checks: 11am, 1pm, 3pm, 5pm, 7pm, 9pm

Saves results to data/compliancemate.json.
Debug artifacts: data/cm_*.png, data/cm_page_source.html, data/cm_page_text.txt
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime, date
from pathlib import Path

from playwright.async_api import async_playwright, TimeoutError as PWTimeout

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

USERNAME = os.getenv("COMPLIANCEMATE_USERNAME", "")
PASSWORD = os.getenv("COMPLIANCEMATE_PASSWORD", "")
BASE_URL  = "https://fg-beta.compliancemate.com"
DATA_DIR  = Path(__file__).parent.parent / "data"
TODAY_STR = date.today().strftime("%Y-%m-%d")

# Lists we specifically care about — names as they appear on the page
# (case-insensitive partial match)
TARGET_CHECKLISTS = [
    "am opening", "opening", "am checklist",
    "pm closing", "closing", "pm checklist",
    "shift change", "shift",
    "11am", "11 am", "1pm", "1 pm",
    "3pm", "3 pm", "5pm", "5 pm",
    "7pm", "7 pm", "9pm", "9 pm",
]

EMPTY_DATA = {
    "meta": {
        "date":      TODAY_STR,
        "generated": datetime.now().strftime("%-m/%-d/%Y at %-I:%M %p"),
        "location":  "2065",
        "status":    "no_data",
    },
    "lists": [],   # [{name, pct, completed, total}]
}


# ── helpers ────────────────────────────────────────────────────────────────────

async def try_fill(page, selectors: list, value: str) -> bool:
    for sel in selectors:
        try:
            await page.fill(sel, value, timeout=3000)
            log.info(f"  filled {sel!r}")
            return True
        except Exception:
            continue
    return False


async def try_click(page, selectors: list) -> bool:
    for sel in selectors:
        try:
            await page.click(sel, timeout=4000)
            log.info(f"  clicked {sel!r}")
            return True
        except Exception:
            continue
    return False


def pct(completed, total):
    return round(completed / total * 100) if total else 0


# ── login ──────────────────────────────────────────────────────────────────────

async def do_login(page) -> bool:
    log.info("=== Login ===")
    await page.goto(BASE_URL, timeout=30000, wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)
    await page.screenshot(path=str(DATA_DIR / "cm_01_login.png"))

    filled = await try_fill(page, [
        'input[type="email"]',
        'input[name="email"]',
        'input[id="email"]',
        'input[name="username"]',
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

    submitted = await try_click(page, [
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("Sign in")',
        'button:has-text("Log in")',
        'button:has-text("Login")',
    ])
    if not submitted:
        await page.keyboard.press("Enter")

    await page.wait_for_load_state("networkidle", timeout=15000)
    await page.screenshot(path=str(DATA_DIR / "cm_02_after_login.png"))
    log.info(f"Post-login URL: {page.url}")
    (DATA_DIR / "cm_page_source.html").write_text(await page.content(), encoding="utf-8")

    # Check we're not still on the login page
    if "login" in page.url.lower() or "sign_in" in page.url.lower():
        log.error("Still on login page — credentials may be wrong")
        return False

    # Log all visible links so we can see the nav structure
    links = await page.query_selector_all("a, button")
    log.info(f"=== Found {len(links)} clickable elements after login ===")
    for el in links[:40]:
        try:
            txt = (await el.inner_text()).strip()
            href = await el.get_attribute("href") or ""
            if txt:
                log.info(f"  [{await el.evaluate('el => el.tagName')}] {txt!r} href={href!r}")
        except Exception:
            continue

    return True


# ── navigate to Statistics → List Completion ALL ───────────────────────────────

async def navigate_to_list_completion(page) -> tuple[bool, str]:
    """Navigate directly to List Completion report with Yesterday filter.
    Returns (success, group_id).
    """
    log.info("=== Navigating to List Completion report ===")

    # Extract group ID from post-login URL
    m = re.search(r'/groups/(\d+)/', page.url)
    group_id = m.group(1) if m else "21792"
    log.info(f"  Group ID: {group_id}")

    # Navigate directly with date filter in URL — more reliable than the form
    url = (
        f"{BASE_URL}/groups/{group_id}/report/list_completions"
        f"?report_filters_presenter%5Bdate_range%5D=yesterday"
    )
    log.info(f"  Navigating to: {url}")
    resp = await page.goto(url, timeout=20000, wait_until="networkidle")
    await page.wait_for_timeout(2000)
    await page.screenshot(path=str(DATA_DIR / "cm_03_list_completions.png"))
    log.info(f"  List Completion URL: {page.url}")

    if resp and resp.status >= 400:
        log.error(f"  HTTP {resp.status} — trying fallback form navigation")
        return await _navigate_via_form(page), group_id

    return True, group_id


async def _navigate_via_form(page) -> bool:
    """Fallback: use the Statistics nav link and form."""
    clicked = await try_click(page, [
        'a:has-text("Statistics")',
        '[href*="list_completion" i]',
    ])
    if not clicked:
        return False
    await page.wait_for_load_state("networkidle", timeout=10000)
    await page.wait_for_timeout(1500)
    return True


# ── set date range to Yesterday and apply ─────────────────────────────────────

async def set_yesterday_and_apply(page) -> bool:
    # Date range already set via URL parameter — nothing to do
    log.info("=== Date range set via URL — skipping form interaction ===")
    return True


# ── scroll and extract list completions ───────────────────────────────────────

async def extract_list_completions(page) -> list:
    log.info("=== Extracting list completions ===")

    # Scroll down to load all rows
    for _ in range(5):
        await page.evaluate("window.scrollBy(0, 600)")
        await page.wait_for_timeout(500)

    await page.screenshot(path=str(DATA_DIR / "cm_07_scrolled.png"))

    # Save full page text and source for debugging
    page_text = await page.inner_text("body")
    (DATA_DIR / "cm_page_text.txt").write_text(page_text, encoding="utf-8")
    html_content = await page.content()
    (DATA_DIR / "cm_results_source.html").write_text(html_content, encoding="utf-8")

    # Log first 60 lines of page text so we can see the structure in CI logs
    log.info("=== Page text (first 60 lines) ===")
    for i, line in enumerate(page_text.splitlines()[:60]):
        if line.strip():
            log.info(f"  {i:02d}: {line.strip()[:120]}")

    results = []

    # Strategy 1: table rows
    try:
        rows = await page.query_selector_all("table tr")
        for row in rows:
            cells = await row.query_selector_all("td, th")
            if len(cells) >= 2:
                texts = [await c.inner_text() for c in cells]
                name = texts[0].strip()
                if not name or name.lower() in ("list", "name", "checklist"):
                    continue
                # look for a percentage in the row
                row_text = " ".join(texts)
                m = re.search(r"(\d{1,3})\s*%", row_text)
                if m:
                    results.append({
                        "name": name,
                        "pct":  int(m.group(1)),
                        "raw":  row_text.strip(),
                    })
                else:
                    # look for X/Y completion
                    m2 = re.search(r"(\d+)\s*/\s*(\d+)", row_text)
                    if m2:
                        c, t = int(m2.group(1)), int(m2.group(2))
                        results.append({
                            "name": name,
                            "pct":  pct(c, t),
                            "completed": c,
                            "total": t,
                            "raw":  row_text.strip(),
                        })
        if results:
            log.info(f"Strategy 1 found {len(results)} rows")
    except Exception as e:
        log.warning(f"Table strategy failed: {e}")

    # Strategy 2: scan page text for name + percentage patterns
    if not results:
        try:
            lines = page_text.splitlines()
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                m = re.search(r"(\d{1,3})\s*%", line)
                if m and len(line) > 3:
                    name = re.sub(r"\d{1,3}\s*%.*", "", line).strip(" :-|")
                    if name:
                        results.append({"name": name, "pct": int(m.group(1)), "raw": line})
            if results:
                log.info(f"Strategy 2 found {len(results)} lines")
        except Exception as e:
            log.warning(f"Text strategy failed: {e}")

    log.info(f"Total extracted: {len(results)} list entries")
    for r in results:
        log.info(f"  {r['name']}: {r['pct']}%")

    return results


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
            if not await do_login(page):
                return EMPTY_DATA

            nav_ok, group_id = await navigate_to_list_completion(page)
            if not nav_ok:
                data = dict(EMPTY_DATA)
                data["meta"]["status"] = "nav_failed"
                return data

            await set_yesterday_and_apply(page)
            lists = await extract_list_completions(page)

            status = "ok" if lists else "login_ok_no_data"
            return {
                "meta": {
                    "date":      TODAY_STR,
                    "generated": datetime.now().strftime("%-m/%-d/%Y at %-I:%M %p"),
                    "location":  "2065",
                    "status":    status,
                },
                "lists": lists,
            }

        except Exception as e:
            log.error(f"Scrape failed: {e}")
            await page.screenshot(path=str(DATA_DIR / "cm_error.png"))
            data = dict(EMPTY_DATA)
            data["meta"]["status"] = f"error: {e}"
            return data
        finally:
            await browser.close()


if __name__ == "__main__":
    DATA_DIR.mkdir(exist_ok=True)
    import sys
    data = asyncio.run(scrape())
    out = Path(__file__).parent.parent / "data" / "compliancemate.json"
    out.write_text(json.dumps(data, indent=2))
    log.info(f"Saved {out}  |  status={data['meta']['status']}  |  {len(data['lists'])} lists found")
