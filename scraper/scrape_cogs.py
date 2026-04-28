#!/usr/bin/env python3
"""
CrunchTime COGS Variance Scraper — API-based
=============================================
Replaces the fragile Playwright widget-scroll approach.

Step 1 — API call (inside the live Playwright session):
  GET /resource/dashboard/top/actual/vs/theoretical
  Returns top-10 variance items + the week date range.
  No extra login required; runs inside the same session as main.py.

Step 2 — P&L page (Playwright, targeted navigation):
  Navigates to the Actual vs. Theoretical Cost report URL
  (using the startDate/endDate from Step 1) to extract COGS %.

Writes:
  data/raw/crunchtime/<store>/<week_end>/cogs_variance.json
  data/cogs_variance.json  (legacy compat symlink copy)

Env:
  CRUNCHTIME_USERNAME
  CRUNCHTIME_PASSWORD
  STORE_ID  (default "2065")
"""

import os, sys, json, re, asyncio, logging
from datetime import datetime, timedelta, timezone, date
from pathlib import Path

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

sys.path.insert(0, str(Path(__file__).parent))
from main import NETCHEF_BASE, USERNAME, PASSWORD, DATA_DIR, do_login, select_location

STORE_ID = os.environ.get("STORE_ID", "2065")
ET = timezone(timedelta(hours=-4))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("cogs")

COGS_GOAL_PCT = 27.5  # Five Guys standard food cost goal


# ── helpers ──────────────────────────────────────────────────────────────────

def _parse_ct_date(s: str) -> date | None:
    """Parse CrunchTime date strings: 'MM/DD/YYYY HH:MM:SS' or 'YYYY-MM-DD'."""
    for fmt in ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _parse_items(raw_list: list) -> list:
    """
    Convert API listSummary items → internal format.

    API sign convention: variance = theoretical - actual
      negative variance → actual > theoretical → OVER budget
    We store over_dollars = actual - theoretical (positive = over budget).
    """
    items = []
    for entry in raw_list:
        name = entry.get("name", "")
        actual = entry.get("actual", {}).get("value")
        theoretical = entry.get("theoretical", {}).get("value")
        api_variance = entry.get("variance", {}).get("value")
        api_var_pct = entry.get("variancePercentage", {}).get("value")

        if actual is None or theoretical is None:
            continue

        over_dollars = round(actual - theoretical, 2)
        # variance_pct: positive % = under, negative % = over (CrunchTime convention)
        variance_pct = round(api_var_pct * 100, 1) if api_var_pct is not None else None

        items.append({
            "name": name,
            "actual": round(actual, 2),
            "theoretical": round(theoretical, 2),
            "over_dollars": over_dollars,
            "variance_pct": variance_pct,
        })

    # Sort: most over-budget first (highest over_dollars descending)
    items.sort(key=lambda x: x["over_dollars"], reverse=True)
    for i, it in enumerate(items, 1):
        it["rank"] = i

    return items


async def _fetch_variance_api(page) -> dict | None:
    """
    Call the variance API endpoint from within the live Playwright session.
    Uses page.evaluate (JS fetch) so session cookies are carried automatically.
    Tries /ncext/ prefix first (correct path from modern.ct context), then
    falls back to the root-relative path in case the routing changes.
    """
    paths = [
        "/ncext/resource/dashboard/top/actual/vs/theoretical",
        "/resource/dashboard/top/actual/vs/theoretical",
    ]
    for path in paths:
        result = await page.evaluate(f"""
            async () => {{
                try {{
                    const r = await fetch('{path}', {{credentials: 'include'}});
                    if (!r.ok) return {{error: r.status, path: '{path}'}};
                    return await r.json();
                }} catch (e) {{
                    return {{error: String(e), path: '{path}'}};
                }}
            }}
        """)
        if result and "error" not in result:
            log.info(f"Variance API ({path}): got {len(result.get('listSummary', []))} items, "
                     f"dateRange={result.get('dateRange')}")
            return result
        log.warning(f"Variance API path {path}: {result}")
    return None


def _ct_date_str(d: date) -> str:
    """Format date as M/D/YYYY (no leading zeros) for CrunchTime URLs."""
    return f"{d.month}/{d.day}/{d.year}"


def _period_dates(today: date) -> dict:
    """Return start dates for week, month, and QTD periods."""
    # Week: last completed Mon–Sun
    last_sun = today - timedelta(days=(today.weekday() + 1) % 7 + 1)
    week_start = last_sun - timedelta(days=6)

    # Month: first day of current month through yesterday
    month_start = today.replace(day=1)

    # Last month: full calendar month
    last_month_end = today.replace(day=1) - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)

    return {
        "week_start":       week_start,
        "week_end":         last_sun,
        "month_start":      month_start,
        "last_month_start": last_month_start,
        "last_month_end":   last_month_end,
        "through":          today - timedelta(days=1),
    }


async def _navigate_to_pnl(page) -> bool:
    """
    Navigate to Inventory → Reports → Profit and Loss via the sidebar.
    Uses ncext/modern.ct sidebar clicks — NOT index.ct hash URLs (those log out the session).
    Returns True if the report page loaded.
    """
    try:
        # Click "Inventory" in the top-level sidebar
        clicked = await page.evaluate("""
            () => {
                const items = [...document.querySelectorAll('.x-navigationitem, .x-treelist-item, [role="menuitem"], .x-navitem')];
                const inv = items.find(el => (el.innerText || '').trim().toLowerCase() === 'inventory');
                if (inv) { inv.click(); return true; }
                // Broader fallback: any clickable element with text "Inventory"
                const all = [...document.querySelectorAll('*')].filter(
                    el => el.children.length === 0 && (el.innerText || '').trim() === 'Inventory'
                );
                if (all.length) { all[0].click(); return true; }
                return false;
            }
        """)
        if not clicked:
            log.warning("Could not find Inventory sidebar item")
            return False
        await page.wait_for_timeout(1_500)

        # Click "Reports" submenu item under Inventory
        clicked = await page.evaluate("""
            () => {
                const all = [...document.querySelectorAll('*')].filter(
                    el => el.children.length === 0 && (el.innerText || '').trim() === 'Reports'
                );
                if (all.length) { all[0].click(); return true; }
                return false;
            }
        """)
        if not clicked:
            log.warning("Could not find Reports submenu under Inventory")
            return False
        await page.wait_for_timeout(1_500)

        # Click "Profit and Loss" report link
        clicked = await page.evaluate("""
            () => {
                const all = [...document.querySelectorAll('*')].filter(
                    el => (el.innerText || '').trim().toLowerCase().includes('profit and loss')
                        || (el.innerText || '').trim().toLowerCase().includes('profit & loss')
                );
                if (all.length) { all[0].click(); return true; }
                return false;
            }
        """)
        if not clicked:
            log.warning("Could not find 'Profit and Loss' link")
            return False

        await page.wait_for_timeout(3_000)
        return True

    except Exception as e:
        log.warning(f"Sidebar navigation error: {e}")
        return False


async def _set_date_range_and_retrieve(page, start_date: str, end_date: str) -> bool:
    """
    Set the Start Date / End Date fields on the P&L report and click Retrieve.
    Does NOT touch the Period dropdown — Bobby's stores don't use periods.
    start_date / end_date format: M/D/YYYY
    """
    try:
        # Clear and fill Start Date
        filled = await page.evaluate(f"""
            (start, end) => {{
                // Find date input fields by label proximity or placeholder
                const inputs = [...document.querySelectorAll('input[type=text], input[type=date], .x-input-el')];
                let startFld = inputs.find(i =>
                    (i.placeholder || '').toLowerCase().includes('start')
                    || (i.name || '').toLowerCase().includes('start')
                    || (i.id || '').toLowerCase().includes('start')
                );
                let endFld = inputs.find(i =>
                    (i.placeholder || '').toLowerCase().includes('end')
                    || (i.name || '').toLowerCase().includes('end')
                    || (i.id || '').toLowerCase().includes('end')
                );
                // Fallback: first two date-like inputs on page
                const dateInputs = inputs.filter(i => /date/i.test(i.placeholder + i.name + i.id + i.className));
                if (!startFld && dateInputs.length >= 1) startFld = dateInputs[0];
                if (!endFld   && dateInputs.length >= 2) endFld   = dateInputs[1];
                if (!startFld || !endFld) return false;
                startFld.value = start;
                startFld.dispatchEvent(new Event('change', {{bubbles: true}}));
                endFld.value = end;
                endFld.dispatchEvent(new Event('change', {{bubbles: true}}));
                return true;
            }}
        """, start_date, end_date)

        if not filled:
            log.warning("Could not find date fields on P&L report")
            return False

        await page.wait_for_timeout(500)

        # Click Retrieve (or Run, or the CrunchTime blue action button)
        clicked = await page.evaluate("""
            () => {
                const btns = [...document.querySelectorAll('.x-button, button, [role=button]')];
                const retrieve = btns.find(b =>
                    /retrieve|run|go|apply/i.test((b.innerText || b.value || '').trim())
                );
                if (retrieve) { retrieve.click(); return true; }
                return false;
            }
        """)
        if not clicked:
            log.warning("Could not find Retrieve button")
            return False

        await page.wait_for_timeout(5_000)
        return True

    except Exception as e:
        log.warning(f"Date/Retrieve error: {e}")
        return False


async def _extract_cogs_pct(page, start_date: str, end_date: str, label: str = "") -> float | None:
    """
    Navigate to Inventory → Reports → Profit and Loss, set the date range,
    click Retrieve, and extract the COGS % (Food line or Supplies+COGS sum).
    Same report every time — just different date ranges.
    Bobby's stores don't use Periods — date range inputs only.
    """
    log.info(f"P&L report [{label}]: {start_date} → {end_date}")
    try:
        # Navigate to P&L via sidebar (stay in modern.ct — never use index.ct, it logs out)
        if not await _navigate_to_pnl(page):
            log.warning(f"[{label}] Could not navigate to P&L — skipping")
            return None

        if not await _set_date_range_and_retrieve(page, start_date, end_date):
            log.warning(f"[{label}] Could not set date range — skipping")
            return None

        safe_label = label.replace(" ", "_")
        await page.screenshot(path=str(DATA_DIR / f"08_cogs_{safe_label}.png"))
        body_text = await page.inner_text("body")

        # P&L report separates COGS and Supplies; Bobby confirmed COGS % is the food line.
        # Look for "COGS" or "Food" category row with an Actual % column.
        patterns = [
            r"COGS[^\d\n]{0,40}(\d{1,2}(?:\.\d{1,2})?)\s*%",
            r"Food[^\d\n]{0,40}(\d{1,2}(?:\.\d{1,2})?)\s*%",
            r"Cost of Goods[^\d\n]{0,40}(\d{1,2}(?:\.\d{1,2})?)\s*%",
        ]
        for pat in patterns:
            m = re.search(pat, body_text, re.I)
            if m:
                pct = float(m.group(1))
                if 5.0 <= pct <= 60.0:
                    log.info(f"[{label}] COGS % = {pct}%")
                    return pct

        log.warning(f"[{label}] Could not parse COGS % from page text")
        return None

    except PlaywrightTimeout:
        log.warning(f"[{label}] P&L page timed out")
        return None
    except Exception as e:
        log.warning(f"[{label}] Error: {e}")
        return None


# ── main ─────────────────────────────────────────────────────────────────────

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1600, "height": 1000})
        page = await ctx.new_page()

        await page.goto(NETCHEF_BASE, wait_until="domcontentloaded", timeout=30_000)
        if not await do_login(page):
            log.error("Login failed")
            await browser.close()
            sys.exit(1)
        await select_location(page)
        # Extra settle time so NCDashboard widgets finish loading before API call
        await page.wait_for_timeout(5_000)

        # Step 1: Variance items via API (best-effort — failure is non-fatal)
        api_data = await _fetch_variance_api(page)
        if not api_data:
            log.warning("Variance API unavailable — will still attempt P&L COGS extraction")
            items = []
        else:
            items = _parse_items(api_data.get("listSummary", []))

        # Derive week dates from API response or fall back to calendar math
        week_start: date | None = None
        week_end: date | None = None
        if api_data:
            date_range = api_data.get("dateRange", {})
            week_start = _parse_ct_date(date_range.get("startDate", ""))
            week_end   = _parse_ct_date(date_range.get("endDate", ""))

        if not week_start or not week_end:
            today_fb = datetime.now(tz=ET).date()
            last_sun = today_fb - timedelta(days=(today_fb.weekday() + 1) % 7 + 1)
            week_end   = last_sun
            week_start = last_sun - timedelta(days=6)
            log.warning(f"Using computed week dates: {week_start}–{week_end}")

        log.info(f"Week: {week_start} → {week_end}  ({len(items)} variance items)")

        # Step 2: COGS % for week, month, and QTD — same P&L report, different dates
        today = datetime.now(tz=ET).date()
        periods = _period_dates(today)

        # Use API-derived week dates (authoritative); month/QTD use calendar math
        week_s  = _ct_date_str(week_start)
        week_e  = _ct_date_str(week_end)
        month_s = _ct_date_str(periods["month_start"])
        through = _ct_date_str(periods["through"])

        last_mo_s = _ct_date_str(periods["last_month_start"])
        last_mo_e = _ct_date_str(periods["last_month_end"])

        cogs_pct_week     = await _extract_cogs_pct(page, week_s,   week_e,   "week")
        cogs_pct_month    = await _extract_cogs_pct(page, month_s,  through,  "month")
        cogs_pct_last_mo  = await _extract_cogs_pct(page, last_mo_s, last_mo_e, "last_mo")

        await browser.close()

    def _vtg(pct):
        return round(pct - COGS_GOAL_PCT, 1) if pct is not None else None

    now = datetime.now(tz=ET)
    out = {
        "meta": {
            "source": "CrunchTime Net Chef — P&L Actual vs. Theoretical Cost report",
            "category": "Food",
            "store": STORE_ID,
            "week_start":    week_start.strftime("%Y-%m-%d"),
            "week_end":      week_end.strftime("%Y-%m-%d"),
            "month_start":      periods["month_start"].strftime("%Y-%m-%d"),
            "last_month_start": periods["last_month_start"].strftime("%Y-%m-%d"),
            "last_month_end":   periods["last_month_end"].strftime("%Y-%m-%d"),
            "through":          periods["through"].strftime("%Y-%m-%d"),
            "pulled":        now.strftime("%Y-%m-%d %H:%M ET"),
            "method":        "api+playwright",
        },
        "cogs_goal_pct":           COGS_GOAL_PCT,
        "cogs_pct_week":           cogs_pct_week,
        "cogs_pct_month":          cogs_pct_month,
        "cogs_pct_last_month":     cogs_pct_last_mo,
        "variance_to_goal_week":   _vtg(cogs_pct_week),
        "variance_to_goal_month":  _vtg(cogs_pct_month),
        "variance_to_goal_last_mo": _vtg(cogs_pct_last_mo),
        "items":                 items,
        "ranking":               "over_dollars_desc",
    }

    raw_dir = DATA_DIR / "raw" / "crunchtime" / STORE_ID / out["meta"]["week_end"]
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_path = raw_dir / "cogs_variance.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    log.info(f"Wrote {out_path}")

    # Legacy compat copy
    (DATA_DIR / "cogs_variance.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    vtg_week = _vtg(cogs_pct_week)
    top = f" | Top item: {items[0]['name']} +${items[0]['over_dollars']}" if items else ""
    log.info(
        f"Done. Week={cogs_pct_week}% Month={cogs_pct_month}% LastMo={cogs_pct_last_mo}%"
        f" (vtg_week={'N/A' if vtg_week is None else f'{vtg_week:+.1f}% vs {COGS_GOAL_PCT}% goal'})"
        f"{top}"
    )


if __name__ == "__main__":
    if not USERNAME or not PASSWORD:
        log.error("CRUNCHTIME_USERNAME / CRUNCHTIME_PASSWORD env vars required")
        sys.exit(1)
    asyncio.run(run())
