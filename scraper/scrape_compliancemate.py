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

import sys
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

USERNAME = os.getenv("COMPLIANCEMATE_USERNAME", "")
PASSWORD = os.getenv("COMPLIANCEMATE_PASSWORD", "")
BASE_URL  = "https://fg-beta.compliancemate.com"
DATA_DIR  = Path(__file__).parent.parent / "data"
TODAY_STR = date.today().strftime("%Y-%m-%d")

# Exact list names as they appear on ComplianceMate for location 2065
TARGET_CHECKLISTS = [
    "11am: time and temp",
    "1pm: time and temp",
    "3pm: time and temp",
    "5pm: time and temp",
    "7pm: time and temp",
    "9pm: time and temp",
    "am pre-shift check",
    "pm pre-shift check",
    "shift change",
    "closing checklist",
    "pre open",
    "closing",
]

# Hardcoded IDs for location 2065
GROUP_ID    = "21792"
LOCATION_ID = "18170"

def _fmt(dt, fmt):
    """strftime without leading zeros — works on Windows and Linux."""
    return dt.strftime(fmt.replace("%-", "%#") if sys.platform == "win32" else fmt)

EMPTY_DATA = {
    "meta": {
        "date":      TODAY_STR,
        "generated": _fmt(datetime.now(), "%-m/%-d/%Y at %-I:%M %p"),
        "location":  "2065",
        "status":    "no_data",
    },
    "overall_pct": 0,
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
    """Navigate to List Completion report by interacting with the UI directly.
    URL-based form submission doesn't apply filters — must click through the form.
    Returns (success, group_id).
    """
    log.info("=== Navigating to List Completion report (UI interaction) ===")

    m = re.search(r'/groups/(\d+)/', page.url)
    group_id = m.group(1) if m else GROUP_ID
    log.info(f"  Group ID: {group_id}")

    # Step 1: Navigate to the list completions report page
    report_url = f"{BASE_URL}/groups/{group_id}/report/list_completions"
    log.info(f"  Going to: {report_url}")
    await page.goto(report_url, timeout=30000, wait_until="networkidle")
    await page.wait_for_timeout(2000)
    await page.screenshot(path=str(DATA_DIR / "cm_03_report_page.png"))

    # Step 2: Select "List Completion - All" report type
    try:
        await page.select_option(
            "select#report_filters_presenter_report_type",
            value="all_list_completions",
            timeout=5000
        )
        log.info("  Selected report type: all_list_completions")
    except Exception as e:
        log.warning(f"  Could not set report type: {e}")

    # Step 3: Select "Yesterday" date range
    try:
        await page.select_option(
            "select[name='report_filters_presenter[date_range]']",
            value="yesterday",
            timeout=5000
        )
        log.info("  Selected date range: yesterday")
    except Exception as e:
        log.warning(f"  Could not set date range: {e}")

    await page.screenshot(path=str(DATA_DIR / "cm_04_filters_set.png"))

    # Step 4: Click Apply
    applied = await try_click(page, [
        "input[name='commit'][value='Apply']",
        "button[name='commit']",
        "input[type='submit'][value='Apply']",
        "button:has-text('Apply')",
        ".filter-actions input[type='submit']",
    ])
    if not applied:
        log.warning("  Could not click Apply — trying Enter key")
        await page.keyboard.press("Enter")

    # Step 5: Wait for accordion data cards to appear
    try:
        await page.wait_for_function(
            "document.querySelectorAll('#accordion .card').length > 1",
            timeout=20000
        )
        log.info("  Data cards detected in accordion")
    except Exception:
        log.warning("  No data cards appeared after 20s — may be no data for yesterday")

    await page.wait_for_timeout(2000)
    await page.screenshot(path=str(DATA_DIR / "cm_05_results.png"))
    log.info(f"  Final URL: {page.url}")
    return True, group_id


# ── scroll and extract overall location % ─────────────────────────────────────

async def extract_overall_pct(page) -> tuple[int, str]:
    """Returns (overall_pct, collapse_target_selector) from the top-level accordion card."""
    log.info("=== Extracting overall location % ===")

    for _ in range(3):
        await page.evaluate("window.scrollBy(0, 600)")
        await page.wait_for_timeout(400)

    await page.screenshot(path=str(DATA_DIR / "cm_07_scrolled.png"))

    # Save full page source for debugging
    html_content = await page.content()
    (DATA_DIR / "cm_results_source.html").write_text(html_content, encoding="utf-8")

    overall_pct = 0
    collapse_target = ""

    try:
        cards = await page.query_selector_all("#accordion .card:not(.column-headers)")
        log.info(f"  Found {len(cards)} location cards")
        for card in cards:
            card_text = (await card.inner_text()).strip()
            if not card_text:
                continue
            lines = [l.strip() for l in card_text.splitlines() if l.strip()]
            log.info(f"  Card: {lines[:4]}")

            pcts = re.findall(r"(\d{1,3})\s*%", card_text)
            if pcts:
                overall_pct = int(pcts[0])

            # Grab data-target from expand link
            link = await card.query_selector("a[data-remote='true'][data-toggle='collapse']")
            if link:
                collapse_target = await link.get_attribute("data-target") or ""
    except Exception as e:
        log.warning(f"Overall extraction failed: {e}")

    log.info(f"  Overall: {overall_pct}%  collapse_target={collapse_target!r}")
    return overall_pct, collapse_target


# ── expand accordion and extract individual checklists ─────────────────────────

async def expand_and_extract_lists(page, collapse_target: str) -> list:
    """
    Clicks the AJAX expand link for the location row, waits for Rails UJS to inject
    the individual checklist rows, then extracts them.
    """
    if not collapse_target:
        log.warning("No collapse target — cannot expand accordion")
        return []

    log.info(f"=== Expanding accordion: {collapse_target} ===")

    # Click the expand link to fire the AJAX request
    link = await page.query_selector(
        f"a[data-remote='true'][data-target='{collapse_target}']"
    )
    if not link:
        log.warning(f"  Expand link not found for {collapse_target}")
        return []

    await link.click()
    log.info("  Clicked expand link — waiting for AJAX content")

    # Wait for Rails UJS to inject .card rows directly into the collapse div
    try:
        await page.wait_for_function(
            f"document.querySelectorAll('{collapse_target} .card').length > 0",
            timeout=20000,
        )
        log.info("  Accordion content loaded")
    except Exception as e:
        log.warning(f"  Accordion AJAX timed out: {e}")
        # Content may still have loaded — try to parse anyway before giving up
        log.info("  Attempting to parse whatever loaded despite timeout")
        collapse_el = await page.query_selector(collapse_target)
        if collapse_el:
            debug_html = await collapse_el.inner_html()
            (DATA_DIR / "cm_expanded_debug.html").write_text(debug_html, encoding="utf-8")
            log.info(f"  Saved {len(debug_html)} bytes of partial HTML")
            if len(debug_html.strip()) < 20:
                return []
            # fall through to extraction below

    await page.wait_for_timeout(800)
    await page.screenshot(path=str(DATA_DIR / "cm_08_expanded.png"))

    # Save expanded HTML for debugging
    collapse_el = await page.query_selector(collapse_target)
    if collapse_el:
        expanded_html = await collapse_el.inner_html()
        (DATA_DIR / "cm_expanded_source.html").write_text(expanded_html, encoding="utf-8")
        log.info(f"  Saved expanded HTML ({len(expanded_html)} bytes)")

    # Log expanded text
    expanded_text = await page.inner_text(collapse_target)
    (DATA_DIR / "cm_page_text.txt").write_text(expanded_text, encoding="utf-8")
    log.info("=== Expanded checklist rows (first 50 lines) ===")
    for i, line in enumerate(expanded_text.splitlines()[:50]):
        if line.strip():
            log.info(f"  {i:02d}: {line.strip()[:120]}")

    rows = []

    # Strategy A: .card rows inside expanded area
    try:
        list_cards = await page.query_selector_all(f"{collapse_target} .card")
        log.info(f"  Found {len(list_cards)} .card elements in expanded area")
        for card in list_cards:
            card_text = (await card.inner_text()).strip()
            if not card_text:
                continue
            lines = [l.strip() for l in card_text.splitlines() if l.strip()]
            name = lines[0] if lines else ""
            if not name or len(name) < 2:
                continue
            pcts = re.findall(r"(\d{1,3})\s*%", card_text)
            if pcts:
                rows.append({"name": name, "pct": int(pcts[0]), "raw": card_text[:200]})
            else:
                m2 = re.search(r"(\d+)\s*/\s*(\d+)", card_text)
                if m2:
                    c, t = int(m2.group(1)), int(m2.group(2))
                    rows.append({"name": name, "pct": pct(c, t), "completed": c, "total": t, "raw": card_text[:200]})
        if rows:
            log.info(f"Strategy A (.card) found {len(rows)} rows")
    except Exception as e:
        log.warning(f"Strategy A failed: {e}")

    # Strategy B: table rows inside expanded area
    if not rows:
        try:
            trs = await page.query_selector_all(f"{collapse_target} tr")
            log.info(f"  Found {len(trs)} <tr> elements")
            for tr in trs:
                tr_text = (await tr.inner_text()).strip()
                if not tr_text:
                    continue
                pcts = re.findall(r"(\d{1,3})\s*%", tr_text)
                if pcts:
                    name = re.sub(r"\d{1,3}\s*%.*", "", tr_text).strip(" :-|\t")
                    if name and len(name) > 2:
                        rows.append({"name": name, "pct": int(pcts[0]), "raw": tr_text[:200]})
            if rows:
                log.info(f"Strategy B (table rows) found {len(rows)} rows")
        except Exception as e:
            log.warning(f"Strategy B failed: {e}")

    # Strategy C: text scan of expanded area
    if not rows:
        for line in expanded_text.splitlines():
            line = line.strip()
            if not line:
                continue
            m = re.search(r"(\d{1,3})\s*%", line)
            if m and len(line) > 5:
                name = re.sub(r"\d{1,3}\s*%.*", "", line).strip(" :-|")
                if name and len(name) > 2:
                    rows.append({"name": name, "pct": int(m.group(1)), "raw": line})
        if rows:
            log.info(f"Strategy C (text scan) found {len(rows)} rows")

    log.info(f"Total individual checklists: {len(rows)}")
    for r in rows:
        log.info(f"  {r['name']}: {r['pct']}%")

    return rows


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

            overall_pct, collapse_target = await extract_overall_pct(page)
            lists = await expand_and_extract_lists(page, collapse_target)

            status = "ok" if lists else ("overall_only" if overall_pct else "login_ok_no_data")
            return {
                "meta": {
                    "date":      TODAY_STR,
                    "generated": _fmt(datetime.now(), "%-m/%-d/%Y at %-I:%M %p"),
                    "location":  "2065",
                    "status":    status,
                },
                "overall_pct": overall_pct,
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
    repo_root = Path(__file__).parent.parent
    out = repo_root / "data" / "compliancemate.json"
    out.write_text(json.dumps(data, indent=2))
    log.info(f"Saved {out}  |  status={data['meta']['status']}  |  overall={data['overall_pct']}%  |  {len(data['lists'])} individual checklists")

    # Daily snapshot for the rollup aggregator (data/raw/compliancemate/<store>/<date>/compliance.json)
    store_id = data.get("meta", {}).get("location") or "2065"
    snap_date = data.get("meta", {}).get("date")
    if snap_date:
        snap_dir = repo_root / "data" / "raw" / "compliancemate" / str(store_id) / snap_date
        snap_dir.mkdir(parents=True, exist_ok=True)
        snap_path = snap_dir / "compliance.json"
        snap_path.write_text(json.dumps(data, indent=2))
        log.info(f"Snapshot {snap_path}")
