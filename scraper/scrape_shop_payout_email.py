#!/usr/bin/env python3
"""
Secret Shop 100% Payout Email Drafter
======================================
Runs after scrape_knowledgeforce.py each CI cycle.

1. Reads the latest shops.json for the store.
2. Finds any 100% shops not yet emailed (tracked in data/raw/marketforce/<store>/emailed.json).
3. For each new 100% shop, logs into CrunchTime and pulls the
   Consolidated Employee Time Detail for that shop's date, filtered to
   the employees working during that meal period.
4. Writes a ready-to-send email draft to
   data/drafts/secret-shop-email-<job_id>.md
5. Appends an entry to data/debug-log.txt so the next session surfaces it.
6. Records the job_id in emailed.json so it is not re-drafted on future runs.

Recipients: secretshop@estep-co.com / CC chess@estep-co.com (Crystal Hess)

Meal period → time window mapping (used to filter time detail rows):
  Breakfast   05:00 – 10:59
  Lunch       11:00 – 14:59
  Dinner      15:00 – 21:59   (covers "Dinner" and "Late Dinner")
  Late Dinner 20:00 – 23:59

Usage:
  CRUNCHTIME_USERNAME=BOBBY.CLINE CRUNCHTIME_PASSWORD=xxx \\
      python scraper/scrape_shop_payout_email.py --store 2065
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import asyncio

ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT  = ROOT / "data" / "raw" / "marketforce"
DRAFTS_DIR = ROOT / "data" / "drafts"
DEBUG_LOG  = ROOT / "data" / "debug-log.txt"

ET = timezone(timedelta(hours=-4))

TO_EMAIL  = "secretshop@estep-co.com"
CC_EMAIL  = "chess@estep-co.com"

# Meal period → (start_hour, end_hour) inclusive — used to filter CT time detail.
# MUST stay in sync with DEFAULT_WIN in scrape_shop_participation.py.
MEAL_WINDOWS: dict[str, tuple[int, int]] = {
    "breakfast":   (5,  11),
    "lunch":       (11, 15),
    "dinner":      (15, 22),
    "late dinner": (19, 23),
}

sys.path.insert(0, str(Path(__file__).parent))
from main import NETCHEF_BASE, USERNAME, PASSWORD, DATA_DIR, do_login, select_location


def log(msg: str) -> None:
    print(f"[shop-email] {msg}", flush=True)


# ── shops.json helpers ────────────────────────────────────────────────────────

def find_latest_shops_json(store_id: str) -> Path | None:
    store_dir = DATA_ROOT / store_id
    if not store_dir.exists():
        return None
    for d in sorted((x for x in store_dir.iterdir() if x.is_dir()), reverse=True):
        p = d / "shops.json"
        if p.exists():
            return p
    return None


def load_emailed(store_id: str) -> set[str]:
    p = DATA_ROOT / store_id / "emailed.json"
    if p.exists():
        try:
            return set(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            pass
    return set()


def save_emailed(store_id: str, emailed: set[str]) -> None:
    p = DATA_ROOT / store_id / "emailed.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(sorted(emailed), indent=2), encoding="utf-8")


# ── CrunchTime time detail ────────────────────────────────────────────────────

async def _navigate_to_time_detail(page) -> bool:
    """
    Navigate directly to the Consolidated Employee Time Detail report via URL.
    Confirmed working 2026-04-28 via live DOM inspection.
    URL: /ncext/next.ct#ConsolidatedEmployeeTimeDetail
    """
    try:
        cetd_url = "https://fiveguysfr77.net-chef.com/ncext/next.ct#ConsolidatedEmployeeTimeDetail"
        await page.goto(cetd_url, wait_until="domcontentloaded", timeout=30_000)
        await page.wait_for_selector('[ces-selenium-id="button_retrieveBtn"]', timeout=20_000)
        log("CETD page loaded via direct URL")
        return True
    except Exception as e:
        log(f"CETD navigation error: {e}")
        try:
            await page.screenshot(path=str(ROOT / "data" / "shop_email_page_text.txt".replace(".txt", ".png")))
        except Exception:
            pass
        return False


async def _set_date_and_retrieve(page, shop_date: str) -> bool:
    """
    Set date range (single day) via ExtJS Ext.getCmp() API, select GM30 Dixie Highway
    from the hierarchy combo picker, then click Retrieve.
    shop_date: 'M/D/YYYY' format.
    Confirmed working 2026-04-28 via live DOM inspection in Bobby's browser.
    """
    try:
        parts = shop_date.split("/")
        month, day, year = int(parts[0]), int(parts[1]), int(parts[2])

        # Set start/end dates using ExtJS component API (JS month is 0-indexed)
        raw = await page.evaluate(f"""
            (() => {{
                const startEl = document.querySelector('[ces-selenium-id="cesdatefield_startDate"]');
                const endEl   = document.querySelector('[ces-selenium-id="cesdatefield_endDate"]');
                const startCmp = Ext.getCmp(startEl.id);
                const endCmp   = Ext.getCmp(endEl.id);
                const d = new Date({year}, {month - 1}, {day});
                startCmp.setValue(d);
                endCmp.setValue(d);
                return startCmp.getRawValue();
            }})()
        """)
        log(f"Date fields set to: {raw}")

        # Select GM30 Dixie Highway. Skip if already set.
        already_set = await page.evaluate('''(() => {
            const el = document.querySelector('[ces-selenium-id="cescombogridpicker_hierarchyCombo"]');
            if (!el) return false;
            const cmp = Ext.getCmp(el.id);
            return (cmp.getRawValue() || "").includes("GM30");
        })()''')

        if not already_set:
            # 1) Programmatically expand the picker via ExtJS API
            await page.evaluate('''(() => {
                const el = document.querySelector('[ces-selenium-id="cescombogridpicker_hierarchyCombo"]');
                const cmp = Ext.getCmp(el.id);
                if (!cmp.isExpanded) cmp.expand();
            })()''')

            # 2) Wait for the picker store to populate
            try:
                await page.wait_for_function(
                    '''() => {
                        const el = document.querySelector('[ces-selenium-id="cescombogridpicker_hierarchyCombo"]');
                        if (!el) return false;
                        const cmp = Ext.getCmp(el.id);
                        const p = cmp.getPicker();
                        return p && p.getStore() && p.getStore().getCount() > 0;
                    }''',
                    timeout=15_000,
                )
            except PlaywrightTimeout:
                log("Hierarchy picker store never populated")
                return False

            # 3) Use Playwright locator to click the GM30 row natively.
            # This dispatches mouse events through CDP, which the ExtJS grid
            # registers correctly (raw DOM dispatchEvent does not in headless).
            try:
                gm30_row = page.locator(".x-grid-row", has_text="GM30").first
                await gm30_row.click(timeout=5_000)
            except PlaywrightTimeout:
                # Fallback: select via ExtJS SelectionModel + setValue
                selected = await page.evaluate('''(() => {
                    const el = document.querySelector('[ces-selenium-id="cescombogridpicker_hierarchyCombo"]');
                    const cmp = Ext.getCmp(el.id);
                    const picker = cmp.getPicker();
                    let gm30 = null;
                    picker.getStore().getRange().forEach(r => {
                        if (JSON.stringify(r.data).includes("GM30")) gm30 = r;
                    });
                    if (!gm30) return null;
                    picker.getSelectionModel().select(gm30, false, false);
                    cmp.setValue(gm30);
                    cmp.collapse();
                    return cmp.getRawValue();
                })()''')
                if not selected:
                    log("Could not select GM30 Dixie Highway (both methods failed)")
                    return False

            await page.wait_for_timeout(800)
            final = await page.evaluate('''(() => {
                const el = document.querySelector('[ces-selenium-id="cescombogridpicker_hierarchyCombo"]');
                return Ext.getCmp(el.id).getRawValue();
            })()''')
            if not final or "GM30" not in final:
                log(f"Hierarchy not set after click+fallback: '{final}'")
                return False
            log(f"Selected GM30 Dixie Highway: {final}")
        await page.wait_for_timeout(500)

        # Click Retrieve
        await page.evaluate("""
            document.querySelector('[ces-selenium-id="button_retrieveBtn"]').click();
        """)
        log("Clicked Retrieve")

        # Wait for data to load (display item changes from "No data to display")
        try:
            await page.wait_for_function(
                '() => { const el = document.querySelector(\'[ces-selenium-id="tbtext_displayItem"]\'); '
                "return el && el.innerText && !el.innerText.includes('No data'); }",
                timeout=20_000
            )
            log("Time detail data loaded")
            return True
        except PlaywrightTimeout:
            log("Timed out waiting for time detail data — saving debug snapshot")
            try:
                txt = await page.inner_text("body")
                (ROOT / "data" / "shop_email_after_labor.txt").write_text(txt[:20000], encoding="utf-8")
            except Exception:
                pass
            return False

    except Exception as e:
        log(f"Date/Retrieve error: {e}")
        return False


def _meal_window(meal_period: str) -> tuple[int, int]:
    """Return (start_hour, end_hour) for the given meal period label."""
    key = meal_period.strip().lower()
    for k, v in MEAL_WINDOWS.items():
        if k in key:
            return v
    # Default: cover full day
    return (0, 23)


def _parse_time_hour(time_str: str) -> int | None:
    """Parse '11:30 AM' or '14:00' → integer hour (24h). Returns None on failure."""
    time_str = time_str.strip()
    m = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)?", time_str, re.IGNORECASE)
    if not m:
        return None
    h = int(m.group(1))
    ampm = (m.group(3) or "").upper()
    if ampm == "PM" and h != 12:
        h += 12
    elif ampm == "AM" and h == 12:
        h = 0
    return h


async def _extract_employees(page, meal_period: str) -> list[str]:
    """
    Extract employee names from CETD group headers.
    Group headers have format "LastName, FirstName - E<id>".
    Filters to employees whose Time In falls within the meal period window.
    Falls back to all employees found if meal-window filtering yields none.
    Confirmed working 2026-04-28 via live DOM inspection.
    """
    await page.wait_for_timeout(1_000)

    start_h, end_h = _meal_window(meal_period)

    result = await page.evaluate(f"""
        (() => {{
            const startH = {start_h};
            const endH   = {end_h};

            // Each employee is a group in the grid; group header text = "Last, First - E<id>"
            const groupHds = [...document.querySelectorAll('.x-grid-group-hd')];
            const inWindow  = [];
            const allNames  = [];

            groupHds.forEach(hd => {{
                const text = hd.innerText?.trim() || '';
                const nameMatch = text.match(/^([A-Za-zÀ-ɏ]+(?:['-][A-Za-zÀ-ɏ]+)?,\\s+[A-Za-zÀ-ɏ]+(?:['-][A-Za-zÀ-ɏ]+)*)\\s*-\\s*E\\d+/);
                if (!nameMatch) return;
                const name = nameMatch[1];
                allNames.push(name);

                // Find data rows within this employee's group to check shift times
                // ExtJS renders group rows as siblings after the group header row
                let sibling = hd.closest('tr, .x-grid-row')?.nextElementSibling;
                let workedInWindow = false;
                while (sibling && !sibling.classList.contains('x-grid-group-hd') &&
                       !sibling.querySelector('.x-grid-group-hd')) {{
                    const rowText = sibling.innerText || '';
                    // Time In is the 3rd column: Date | Location | TimeIn | TimeOut ...
                    const timeMatch = rowText.match(/\\d{{2}}\\/\\d{{2}}\\/\\d{{4}}[^\\d]+(\\d{{1,2}}):(\\d{{2}})/);
                    if (timeMatch) {{
                        const h = parseInt(timeMatch[1], 10);
                        if (h >= startH && h <= endH) {{ workedInWindow = true; break; }}
                    }}
                    sibling = sibling.nextElementSibling;
                }}
                if (workedInWindow) inWindow.push(name);
            }});

            return inWindow.length > 0 ? inWindow : allNames;
        }})()
    """)

    log(f"Employees extracted: {len(result)} ({meal_period} window)")
    return result or []


async def pull_employees_for_shop(shop: dict) -> list[str]:
    """
    Login to CrunchTime and pull the Consolidated Employee Time Detail
    for the given shop's date and meal period.
    Returns list of employee name strings.
    """
    shop_date_iso = shop.get("date", "")  # "2026-04-17"
    meal_period   = shop.get("meal_period", "Lunch")

    # Convert ISO date → M/D/YYYY for CrunchTime
    try:
        d = date.fromisoformat(shop_date_iso)
        ct_date = f"{d.month}/{d.day}/{d.year}"
    except Exception:
        log(f"Could not parse shop date: {shop_date_iso}")
        return []

    log(f"Pulling time detail for {ct_date} / {meal_period}")

    employees: list[str] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx     = await browser.new_context(viewport={"width": 1600, "height": 1000})
        page    = await ctx.new_page()

        try:
            await page.goto(NETCHEF_BASE, wait_until="domcontentloaded", timeout=30_000)
            if not await do_login(page):
                log("CrunchTime login failed")
                return []
            await select_location(page)
            await page.wait_for_timeout(5_000)

            if not await _navigate_to_time_detail(page):
                log("Could not navigate to time detail report")
                return []

            if not await _set_date_and_retrieve(page, ct_date):
                log("Could not retrieve time detail for date")
                return []

            employees = await _extract_employees(page, meal_period)

        except Exception as e:
            log(f"Error pulling time detail: {e}")
        finally:
            await browser.close()

    return employees


# ── email draft ───────────────────────────────────────────────────────────────

def build_email_draft(shop: dict, employees: list[str], store_id: str) -> str:
    job_id      = shop.get("job_id", "?")
    shop_date   = shop.get("date", "?")
    meal_period = shop.get("meal_period", "?")
    score       = shop.get("score", 100)

    try:
        d = date.fromisoformat(shop_date)
        friendly_date = d.strftime("%B %-d, %Y")
    except Exception:
        friendly_date = shop_date

    if employees:
        emp_list = "\n".join(f"  - {e}" for e in employees)
    else:
        emp_list = "  (Could not retrieve employee list from CrunchTime — please look up manually)"

    return f"""To: {TO_EMAIL}
CC: {CC_EMAIL}
Subject: Store 2065 — 100% Secret Shop — {friendly_date} ({meal_period})

Hi,

Store 2065 (Dixie Highway) received a perfect 100% score on the secret shop conducted on {friendly_date} during the {meal_period} period (Job #{job_id}).

The following employees were on shift during that time and should receive recognition:

{emp_list}

Please process the payout per the standard 100% shop recognition program.

Thank you,
Bobby Cline
General Manager — Store 2065
"""


def write_draft(shop: dict, employees: list[str], store_id: str) -> Path:
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    job_id = shop.get("job_id", "unknown")
    path   = DRAFTS_DIR / f"secret-shop-email-{job_id}.md"
    path.write_text(build_email_draft(shop, employees, store_id), encoding="utf-8")
    return path


def append_debug_log(msg: str) -> None:
    now = datetime.now(tz=ET).strftime("%Y-%m-%d %H:%M:%S")
    DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
    with DEBUG_LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{now}] shop-email: {msg}\n")


# ── participation fallback ────────────────────────────────────────────────────

def load_participation_names(store_id: str, job_id: str) -> list[str]:
    """Return first-names from participation.json for this job_id, or []."""
    p = DATA_ROOT / store_id / "participation.json"
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data.get("by_shop", {}).get(job_id, [])
    except Exception:
        return []


def invoke_participation_scraper(store_id: str) -> bool:
    """
    Invoke scrape_shop_participation.py via subprocess using the current env
    (which carries CRUNCHTIME_USERNAME / CRUNCHTIME_PASSWORD in CI).
    Returns True if the subprocess exited 0, False otherwise.
    """
    script = Path(__file__).parent / "scrape_shop_participation.py"
    cmd = [sys.executable, str(script), "--store", store_id]
    log(f"Invoking participation scraper: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 min hard cap
            env=os.environ,
        )
        for line in result.stdout.splitlines():
            log(f"  [participation] {line}")
        if result.returncode != 0:
            log(f"  participation scraper exit {result.returncode}: {result.stderr[:400]}")
            return False
        return True
    except subprocess.TimeoutExpired:
        log("  participation scraper timed out after 300s")
        return False
    except Exception as e:
        log(f"  participation scraper error: {e}")
        return False


def resolve_employees(shop: dict, store_id: str, _ct_employees_unused: list[str]) -> list[str]:
    """
    Return the authoritative name list for a shop.

    Single source of truth: participation.json (written by scrape_shop_participation.py).
    This function never re-derives names from CETD independently — doing so produced
    disagreements between the two scripts (fixed 2026-05-14).

    Priority:
      1. participation.json cached entry — if present, use it.
      2. Invoke scrape_shop_participation.py to populate it, then re-read.
      3. If all paths fail → log PARTICIPATION_RETRY_FAILED and return [].
    """
    job_id = shop.get("job_id", "?")

    cached = load_participation_names(store_id, job_id)
    if cached:
        log(f"  Using participation.json ({len(cached)} names) for job {job_id}: {cached}")
        return cached

    log(f"  NO_PARTICIPATION for 100% shop {job_id} — invoking scrape_shop_participation.py")
    ok = invoke_participation_scraper(store_id)
    if ok:
        retried = load_participation_names(store_id, job_id)
        if retried:
            log(f"  Retry succeeded: {retried}")
            return retried
        log(f"  Retry ran but job {job_id} still missing from participation.json")

    msg = f"PARTICIPATION_RETRY_FAILED job={job_id} ({shop.get('date')} {shop.get('meal_period')})"
    log(msg)
    append_debug_log(msg)
    return []


# ── main ─────────────────────────────────────────────────────────────────────

async def run(store_id: str) -> int:
    shops_path = find_latest_shops_json(store_id)
    if not shops_path:
        log("No shops.json found — nothing to do")
        return 0

    data      = json.loads(shops_path.read_text(encoding="utf-8"))
    shops     = data.get("shops", [])
    emailed   = load_emailed(store_id)

    new_100 = [
        s for s in shops
        if s.get("score") == 100.0 and s.get("job_id") not in emailed
    ]

    if not new_100:
        log("No new 100% shops to process")
        return 0

    log(f"Found {len(new_100)} new 100% shop(s) to draft emails for")

    for shop in new_100:
        job_id = shop["job_id"]
        log(f"Processing shop {job_id} ({shop.get('date')} {shop.get('meal_period')})")

        # participation.json is the single source of truth for names.
        # We no longer call pull_employees_for_shop() directly — that path produced
        # names that disagreed with scrape_shop_participation.py due to differing
        # meal-period windows. resolve_employees() reads participation.json first,
        # then invokes scrape_shop_participation.py if the entry is missing.
        employees = resolve_employees(shop, store_id, [])

        draft_path = write_draft(shop, employees, store_id)
        log(f"Draft written: {draft_path}")

        note = (
            f"100% shop {job_id} ({shop.get('date')} {shop.get('meal_period')}) — "
            f"draft email at {draft_path}. "
            f"Send to {TO_EMAIL} CC {CC_EMAIL}. Review before sending."
        )
        append_debug_log(note)
        log(note)

        emailed.add(job_id)

    save_emailed(store_id, emailed)
    log(f"Marked {len(new_100)} shop(s) as emailed in {DATA_ROOT / store_id / 'emailed.json'}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", default=os.environ.get("STORE_ID", "2065"))
    args = parser.parse_args()

    if not USERNAME or not PASSWORD:
        log("CRUNCHTIME_USERNAME / CRUNCHTIME_PASSWORD env vars required")
        sys.exit(1)

    sys.exit(asyncio.run(run(args.store)))
