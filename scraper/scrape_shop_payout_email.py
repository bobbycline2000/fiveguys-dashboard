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

# Meal period → (start_hour, end_hour) inclusive — used to filter CT time detail
MEAL_WINDOWS: dict[str, tuple[int, int]] = {
    "breakfast":   (5,  10),
    "lunch":       (11, 14),
    "dinner":      (15, 21),
    "late dinner": (20, 23),
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
    Sidebar nav: Labor → Reports → Consolidated Employee Time Detail.
    Uses ces-selenium-id="menuitem_laborMenu" (reliable) for the Labor icon,
    then text-based search for the sub-menu items.
    Dismisses the Daily News modal that appears post-login.
    Never navigates via index.ct hash URLs (those log out the modern.ct session).
    """
    try:
        # Dismiss Daily News or any other modal dialog that appears post-login
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(500)
        await page.evaluate("""
            () => {
                // Click any visible x-dialogtool (modal close button)
                const closeBtn = document.querySelector('.x-dialogtool, .x-paneltool[data-componentid]');
                if (closeBtn) closeBtn.click();
            }
        """)
        await page.wait_for_timeout(500)

        # Step 1: Click the Labor sidebar icon via its ces-selenium-id
        clicked = await page.evaluate("""
            () => {
                const el = document.querySelector('[ces-selenium-id="menuitem_laborMenu"]');
                if (el) { el.click(); return true; }
                return false;
            }
        """)
        if not clicked:
            # Fallback: text-based search for "Labor"
            clicked = await page.evaluate("""
                () => {
                    const all = [...document.querySelectorAll('*')].filter(el =>
                        el.children.length === 0 &&
                        (el.innerText || '').trim().toLowerCase() === 'labor'
                    );
                    if (all.length) { all[0].click(); return true; }
                    return false;
                }
            """)
        if not clicked:
            log("Could not find Labor sidebar item")
            return False
        log("Clicked Labor sidebar item")
        await page.wait_for_timeout(2_000)

        # Step 2: Click "Reports" from the Labor sub-menu
        clicked = await page.evaluate("""
            () => {
                const all = [...document.querySelectorAll('*')].filter(el =>
                    el.children.length === 0 &&
                    (el.innerText || '').trim().toLowerCase() === 'reports'
                );
                if (all.length) { all[0].click(); return true; }
                return false;
            }
        """)
        if not clicked:
            log("Could not find Reports submenu under Labor")
            return False
        log("Clicked Reports submenu")
        await page.wait_for_timeout(2_000)

        # Save screenshot for debugging before searching for the report link
        try:
            await page.screenshot(path=str(ROOT / "data" / "shop_email_sidebar.png"))
        except Exception:
            pass

        # Step 3: Click Consolidated Employee Time Detail (partial match, shortest text wins)
        clicked = await page.evaluate("""
            () => {
                const all = [...document.querySelectorAll('*')];
                const candidates = all.filter(el => {
                    const txt = (el.innerText || el.textContent || '').trim().toLowerCase();
                    return txt.includes('consolidated') && txt.includes('time') && txt.length < 120;
                });
                if (!candidates.length) return null;
                candidates.sort((a, b) =>
                    (a.innerText || a.textContent || '').length -
                    (b.innerText || b.textContent || '').length
                );
                const target = candidates[0];
                target.click();
                return (target.innerText || target.textContent || '').trim();
            }
        """)
        if not clicked:
            log("Could not find 'Consolidated ... Time ...' report link")
            return False
        log(f"Clicked report link: '{clicked}'")

        await page.wait_for_timeout(2_000)
        return True
    except Exception as e:
        log(f"Sidebar nav error: {e}")
        return False


async def _set_date_and_retrieve(page, shop_date: str) -> bool:
    """
    Set the date range to a single day (start = end = shop_date, M/D/YYYY)
    and click Retrieve. Matches scrape_cogs._set_date_range_and_retrieve.
    """
    try:
        filled = await page.evaluate(f"""
            (d) => {{
                const inputs = [...document.querySelectorAll(
                    'input[type=text], input[type=date], .x-input-el'
                )];
                const dateInputs = inputs.filter(i =>
                    /date/i.test(i.placeholder + i.name + i.id + i.className)
                );
                let startFld = inputs.find(i =>
                    /start/i.test(i.placeholder + i.name + i.id)
                ) || dateInputs[0];
                let endFld = inputs.find(i =>
                    /end/i.test(i.placeholder + i.name + i.id)
                ) || dateInputs[1];
                if (!startFld) return false;
                startFld.value = d;
                startFld.dispatchEvent(new Event('change', {{bubbles: true}}));
                if (endFld) {{
                    endFld.value = d;
                    endFld.dispatchEvent(new Event('change', {{bubbles: true}}));
                }}
                return true;
            }}
        """, shop_date)
        if not filled:
            log("Could not fill date fields on Time Detail report")
            return False

        await page.wait_for_timeout(500)

        clicked = await page.evaluate("""
            () => {
                const btns = [...document.querySelectorAll('.x-button, button, [role=button]')];
                const btn = btns.find(b =>
                    /retrieve|run|go|apply/i.test((b.innerText || b.value || '').trim())
                );
                if (btn) { btn.click(); return true; }
                return false;
            }
        """)
        if not clicked:
            log("Could not find Retrieve button")
            return False

        await page.wait_for_timeout(5_000)
        return True
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
    Read the Consolidated Employee Time Detail page text.
    Returns a list of employee names who were on shift during the meal window.
    Falls back to returning ALL employees found if filtering yields none.
    """
    await page.wait_for_timeout(2_000)
    body = await page.inner_text("body")

    start_h, end_h = _meal_window(meal_period)

    # Heuristic: look for lines that match "LastName, FirstName" or
    # "FirstName LastName" adjacent to a time value.
    # CrunchTime time detail typically lists: Name | Date | In-Time | Out-Time | Hours
    # We extract every name that appears alongside an in-time in the meal window.

    # Pattern 1: "Name\t<date>\t<in-time>\t<out-time>\t<hours>"
    # Pattern 2: table rows with similar structure
    employees_in_window: list[str] = []
    employees_all: list[str] = []

    # Split into logical rows — any line with a time value
    lines = [l.strip() for l in body.splitlines() if l.strip()]
    i = 0
    while i < len(lines):
        line = lines[i]
        # Look for time patterns (HH:MM AM/PM or HH:MM)
        times = re.findall(r"\d{1,2}:\d{2}\s*(?:AM|PM)?", line, re.IGNORECASE)
        if times:
            # Try to find an employee name nearby (within ±2 lines)
            context = " ".join(lines[max(0, i-2): i+3])
            # Name pattern: "Word, Word" or "Word Word" (2+ words, title case)
            name_matches = re.findall(
                r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+|[A-Z][a-z]+,\s*[A-Z][a-z]+)\b",
                context
            )
            for name in name_matches:
                # Check if any of the times fall in the meal window
                in_window = False
                for t in times:
                    h = _parse_time_hour(t)
                    if h is not None and start_h <= h <= end_h:
                        in_window = True
                        break
                clean = name.strip()
                if clean not in employees_all:
                    employees_all.append(clean)
                if in_window and clean not in employees_in_window:
                    employees_in_window.append(clean)
        i += 1

    result = employees_in_window if employees_in_window else employees_all
    log(f"Employees found: {len(result)} in window, {len(employees_all)} total")
    return result


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

        employees = await pull_employees_for_shop(shop)
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
