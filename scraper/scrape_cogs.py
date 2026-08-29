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

import requests
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

def _parse_ncdashboard_avt(page_text: str) -> dict | None:
    """
    Parse the 'Top 10 Actual vs. Theoretical Cost Items' widget from NCDashboard
    inner_text(). This widget is always visible after login — no extra navigation.

    Returns {"week_start": date, "week_end": date, "items": [...]} or None.
    """
    marker = "Top 10 Actual vs. Theoretical Cost Items"
    idx = page_text.find(marker)
    if idx < 0:
        return None

    chunk = page_text[idx: idx + 1200]
    lines = [l.strip() for l in chunk.splitlines() if l.strip()]

    # Date range line: "MM/DD/YYYY - MM/DD/YYYY"
    week_start = week_end = None
    date_re = re.compile(r"(\d{2}/\d{2}/\d{4})\s*[-–]\s*(\d{2}/\d{2}/\d{4})")
    for line in lines[:5]:
        m = date_re.search(line)
        if m:
            week_start = datetime.strptime(m.group(1), "%m/%d/%Y").date()
            week_end   = datetime.strptime(m.group(2), "%m/%d/%Y").date()
            break

    # Items: "N.Item Name", "$actual", "$theoretical", "±pct%"
    dollar_re  = re.compile(r"^\$-?[\d,]+$")
    pct_re     = re.compile(r"^-?\d+%$")
    item_re    = re.compile(r"^(\d+)\.\s*(.+)$")

    items = []
    i = 0
    while i < len(lines):
        m = item_re.match(lines[i])
        if m:
            name = m.group(2).strip()
            # Collect up to 3 more lines: actual, theoretical, pct
            vals = []
            j = i + 1
            while j < len(lines) and len(vals) < 3:
                if dollar_re.match(lines[j]) or pct_re.match(lines[j]):
                    vals.append(lines[j])
                elif item_re.match(lines[j]):
                    break
                j += 1

            if len(vals) >= 2:
                def _parse_dollar(s):
                    return float(s.replace("$", "").replace(",", ""))
                actual = _parse_dollar(vals[0])
                theoretical = _parse_dollar(vals[1])
                pct_str = vals[2] if len(vals) >= 3 and pct_re.match(vals[2]) else None
                variance_pct = float(pct_str.rstrip("%")) if pct_str is not None else None
                over_dollars = round(actual - theoretical, 2)
                items.append({
                    "name": name,
                    "actual": actual,
                    "theoretical": theoretical,
                    "over_dollars": over_dollars,
                    "variance_pct": variance_pct,
                })
            i = j
        else:
            i += 1

    if not items:
        return None

    items.sort(key=lambda x: x["over_dollars"], reverse=True)
    for rank, it in enumerate(items, 1):
        it["rank"] = rank

    return {"week_start": week_start, "week_end": week_end, "items": items}


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
    # Proven endpoint + body (re-verified live 2026-08-29): POST returns
    # ingredient-level listSummary (Bun Burger, Shake Mix, Bacon Raw Sliced…)
    # — the real Actual-vs-Theoretical report.
    #
    # ROOT CAUSE (found 2026-08-29): commit ee014947 (2026-05-24) changed this
    # body to {"category": 1}, which 404s on /resource/... and returns an
    # empty listSummary on /ncext/resource/... — despite that commit's own
    # message claiming "proven endpoint... Category 1 = Food". That claim was
    # never actually verified end-to-end; every scheduled pull since 2026-05-24
    # silently fell through to the NCDashboard MENU-item widget fallback below
    # (Cheeseburger, Bacon Cheeseburger… with variance_pct always null), which
    # is the WRONG report — menu items, not ingredients. ~13 weeks of
    # cogs_variance.json item-level data were affected.
    #
    # The correct body is the one documented in
    # _memory/handoffs/2026-05-08-0237-overnight-cogs-analysis.md and
    # re-confirmed live 2026-08-29 (200 OK, 10 ingredient-level items,
    # dateRange 08/17/2026-08/23/2026): {"singleStatus": false, "page": 1,
    # "start": 0, "limit": 25}. Only the non-/ncext/ path works with this body.
    paths = [
        "/resource/dashboard/top/actual/vs/theoretical",
        "/ncext/resource/dashboard/top/actual/vs/theoretical",
    ]
    body = {"singleStatus": False, "page": 1, "start": 0, "limit": 25}
    for path in paths:
        result = await page.evaluate(
            """
            async ([path, body]) => {
                try {
                    const r = await fetch(path, {
                        method: 'POST', credentials: 'include',
                        headers: {'Accept':'application/json','Content-Type':'application/json;charset=UTF-8','X-Requested-With':'XMLHttpRequest'},
                        body: JSON.stringify(body)
                    });
                    if (!r.ok) return {error: r.status, path: path};
                    return await r.json();
                } catch (e) {
                    return {error: String(e), path: path};
                }
            }
            """,
            [path, body],
        )
        if result and "error" not in result and result.get("listSummary"):
            log.info(f"Variance API ({path}): {len(result.get('listSummary', []))} items")
            return result
        log.warning(f"Variance API path {path}: {str(result)[:120]}")
    return None


def _ct_date_str(d: date) -> str:
    """Format date as M/D/YYYY (no leading zeros) for CrunchTime URLs."""
    return f"{d.month}/{d.day}/{d.year}"


def _last_week_mon_sun(today: date) -> tuple[date, date]:
    """Last fully-completed week, Monday–Sunday (Bobby's food-cost window)."""
    this_monday = today - timedelta(days=today.weekday())   # Mon of current week
    last_monday = this_monday - timedelta(days=7)
    last_sunday = last_monday + timedelta(days=6)
    return last_monday, last_sunday


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


GL_URL    = f"{NETCHEF_BASE}/resource/purchasesbygl/location/details"
SALES_URL = f"{NETCHEF_BASE}/resource/sales/sales/registerSales/summary"
COGS_GL_CATEGORIES = {"Food", "Bread", "Shakes", "Beverage"}


async def _extract_cogs_pct_via_gl(ctx, start_date: date, end_date: date, label: str = "") -> float | None:
    """
    PRIMARY path (added 2026-08-03) — compute COGS % via the Purchases-by-GL
    + Register Sales Summary APIs instead of the Playwright P&L page-scrape.

    Root cause fixed here: `_extract_cogs_pct()` below (the P&L DOM navigation)
    returned None for FOUR straight weeks (07/05, 07/12, 07/19, 07/26) — see
    handoffs 2026-07-13 through 2026-07-28-dashboard-blocked-fpct-fgu.md. The
    P&L "Period"-free date-range report is fragile to navigate/parse reliably.

    `/resource/purchasesbygl/location/details` is a proven, pure-cookie-replay
    API (confirmed working 2026-07-06, already production for the DM Weekly
    Synopsis via pull_cogs_supplies.py — see CRUNCHTIME_API.md §1.6b). This
    reuses that same, already-verified math inside the live Playwright session
    (extracts cookies from the browser context — no separate auth needed).

    CAVEAT (same as pull_cogs_supplies.py): purchase/delivery-date basis, not
    the P&L's Beg Inv + Purchases − End Inv COGS-sold basis. Can swing
    +/-2-4 points week-to-week vs the true P&L number on delivery timing;
    month/quarter windows track much closer. This is a real, always-available
    number vs. "No Recent Data" — flagged via meta.cogs_basis on the output.
    """
    try:
        cookies = await ctx.cookies()
        jar = {c["name"]: c["value"] for c in cookies}
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json;charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": NETCHEF_BASE,
            "Referer": f"{NETCHEF_BASE}/ncext/modern.ct",
        }
        start_ct = _ct_date_str(start_date)
        end_ct   = _ct_date_str(end_date)

        gl_body = {
            "extraCriteriaMap": {
                "startDate": start_ct, "endDate": end_ct,
                "locationId": 13969, "hierarchyId": None, "isConsolidated": False,
            },
            "pagingInfo": {"page": 1, "start": 0, "limit": 2000},
        }
        r = requests.post(GL_URL, json=gl_body, cookies=jar, headers=headers, timeout=30)
        r.raise_for_status()
        gdata = r.json()
        gl_rows = gdata if isinstance(gdata, list) else gdata.get("rows", gdata.get("contentMap", {}).get("rows", []))

        # registerSales/summary silently ignores gte/lte — query day-before/after
        # and trim exact dates in Python (confirmed 2026-07-06).
        day_before = (start_date - timedelta(days=1)).strftime("%m/%d/%Y")
        day_after  = (end_date + timedelta(days=1)).strftime("%m/%d/%Y")
        sales_body = {
            "page": 1, "start": 0, "limit": 500,
            "extraFilter": [
                {"type": "date", "value": day_before, "field": "salesDate", "comparison": "gt"},
                {"type": "date", "value": day_after,  "field": "salesDate", "comparison": "lt"},
            ],
        }
        r2 = requests.post(SALES_URL, json=sales_body, cookies=jar, headers=headers, timeout=30)
        r2.raise_for_status()
        sdata = r2.json()
        srows = sdata if isinstance(sdata, list) else sdata.get("rows", sdata.get("contentMap", {}).get("rows", []))

        net_sales, counted = 0.0, 0
        for row in srows:
            sd_str = row.get("salesDate", "")
            try:
                sd = datetime.strptime(sd_str.split(" ")[0], "%m/%d/%Y").date()
            except ValueError:
                continue
            if not (start_date <= sd <= end_date):
                continue
            val = row.get("totTotalNetSales")
            if val is not None:
                try:
                    net_sales += float(val)
                    counted += 1
                except (ValueError, TypeError):
                    pass

        if not counted or net_sales <= 0:
            log.warning(f"[{label}] GL/sales pull returned no usable net sales for {start_ct}-{end_ct}")
            return None

        cogs_dollars = sum(
            float(row.get("amount") or 0)
            for row in gl_rows
            if (row.get("glDescription") or "").strip() in COGS_GL_CATEGORIES
        )
        pct = round(100 * cogs_dollars / net_sales, 1)
        if 5.0 <= pct <= 60.0:
            log.info(f"[{label}] COGS % (GL/purchases basis) = {pct}%  "
                     f"(net_sales=${net_sales:,.2f}, cogs=${cogs_dollars:,.2f})")
            return pct
        log.warning(f"[{label}] GL-derived COGS % out of sane range: {pct}")
        return None
    except Exception as e:
        log.warning(f"[{label}] GL-based COGS pull error: {e}")
        return None


async def _extract_cogs_pct(page, start_date: str, end_date: str, label: str = "") -> float | None:
    """
    DEPRECATED as of 2026-08-03 — no longer called from run(). Kept only as a
    documented fallback if the GL-based path (`_extract_cogs_pct_via_gl` above)
    ever breaks. This DOM-scrape returned None for 4 straight weeks (07/05
    through 07/26) and is the confirmed root cause of the Food Cost % card
    showing "No Recent Data". Do not re-wire this without a real fix to the
    P&L sidebar navigation/parsing — it was never reliable.

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

        # Intercept XHR/fetch requests to find the real variance API path CrunchTime uses.
        # Logs are visible in GitHub Actions — this resolves the 404 mystery on the next run.
        captured_api_calls: list[str] = []

        def _capture_request(request):
            url = request.url.lower()
            if any(kw in url for kw in ("actual", "theoretical", "variance", "cogs", "dashboard/top")):
                captured_api_calls.append(f"{request.method} {request.url}")

        page.on("request", _capture_request)

        # Trigger a page interaction so CrunchTime fires any lazy-loaded widget XHRs
        await page.evaluate("() => window.scrollTo(0, 300)")
        await page.wait_for_timeout(2_000)
        await page.evaluate("() => window.scrollTo(0, 0)")
        await page.wait_for_timeout(1_000)

        page.remove_listener("request", _capture_request)
        if captured_api_calls:
            log.info(f"Intercepted {len(captured_api_calls)} relevant XHR/fetch calls:")
            for c in captured_api_calls:
                log.info(f"  CAPTURED: {c}")
        else:
            log.warning("No matching XHR calls intercepted — Performance dashboard may not fire the variance API on scroll")

        # Step 1: Variance items via the Actual-vs-Theoretical API (PRIMARY).
        # This returns INGREDIENT-level items (Bacon Raw Sliced, Cheese, Potato
        # Idaho…) — the real theoretical food-cost report. The NCDashboard text
        # widget returns MENU items (Cheeseburger…) which are NOT what Bobby wants,
        # so the API is primary and the widget is fallback only. (Fixed 2026-05-24.)
        items = []
        week_start = week_end = None
        item_source = "none"
        api_data = await _fetch_variance_api(page)
        if api_data and api_data.get("listSummary"):
            items = _parse_items(api_data.get("listSummary", []))
            date_range = api_data.get("dateRange", {})
            week_start = _parse_ct_date(date_range.get("startDate", ""))
            week_end   = _parse_ct_date(date_range.get("endDate", ""))
            item_source = "api_ingredient_level"
            log.info(f"AvT API: {len(items)} ingredient-level variance items, "
                     f"range={week_start}–{week_end}")
        else:
            # WARNING: this branch returns MENU items (Cheeseburger, etc.), not
            # ingredients — it is the wrong report for the food-cost drill-down.
            # It only exists as a last-resort fallback. If this fires, the AvT
            # API call above is broken again and needs the same live-verification
            # treatment as the 2026-08-29 fix (see comment in _fetch_variance_api).
            log.warning("AvT API unavailable — falling back to NCDashboard MENU-item widget text (WRONG report, ingredient API is broken)")
            page_text = await page.inner_text("body")
            widget_data = _parse_ncdashboard_avt(page_text)
            if widget_data and widget_data["items"]:
                items = widget_data["items"]
                week_start = widget_data["week_start"]
                week_end   = widget_data["week_end"]
                item_source = "widget_menu_level_FALLBACK"

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

        # Food-cost week = last fully-completed Mon–Sun (Bobby's spec 2026-05-24).
        # The AVT widget's week (week_start/week_end) is CrunchTime's in-progress
        # week — keep it only to label the variance items' window.
        variance_week_start, variance_week_end = week_start, week_end
        fc_start, fc_end = _last_week_mon_sun(today)
        week_start, week_end = fc_start, fc_end
        log.info(f"Food-cost week (Mon–Sun) = {fc_start} → {fc_end}; "
                 f"variance items week = {variance_week_start} → {variance_week_end}")

        cogs_pct_week     = await _extract_cogs_pct_via_gl(ctx, fc_start, fc_end, "week")
        cogs_pct_month    = await _extract_cogs_pct_via_gl(ctx, periods["month_start"], periods["through"], "month")
        cogs_pct_last_mo  = await _extract_cogs_pct_via_gl(ctx, periods["last_month_start"], periods["last_month_end"], "last_mo")

        await browser.close()

    def _vtg(pct):
        return round(pct - COGS_GOAL_PCT, 1) if pct is not None else None

    now = datetime.now(tz=ET)
    out = {
        "meta": {
            "source": "CrunchTime Net Chef — purchasesbygl/location/details + registerSales/summary (GL/purchase basis; see cogs_basis)",
            "cogs_basis": "Purchase/delivery-date basis, NOT P&L COGS-sold basis. Can swing +/-2-4pts week-to-week on delivery timing; month/quarter track closer.",
            "item_source": item_source,
            "category": "Food",
            "store": STORE_ID,
            "week_start":    week_start.strftime("%Y-%m-%d"),
            "week_end":      week_end.strftime("%Y-%m-%d"),
            "variance_week_start": variance_week_start.strftime("%Y-%m-%d") if variance_week_start else None,
            "variance_week_end":   variance_week_end.strftime("%Y-%m-%d") if variance_week_end else None,
            "month_start":      periods["month_start"].strftime("%Y-%m-%d"),
            "last_month_start": periods["last_month_start"].strftime("%Y-%m-%d"),
            "last_month_end":   periods["last_month_end"].strftime("%Y-%m-%d"),
            "through":          periods["through"].strftime("%Y-%m-%d"),
            "pulled":        now.strftime("%Y-%m-%d %H:%M ET"),
            "method":        "api+playwright (GL-based, 2026-08-03)",
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

    # PRESERVE the food cost % from read_cogs_email.py (daily COGS Flash email).
    # read_cogs_email runs BEFORE this script and writes cogs_pct_week (FP%) into
    # cogs_variance.json. The P&L page-scrape above is unreliable and often returns
    # None — when it does, DO NOT clobber the email's good FP%. (Bug fixed 2026-05-24.)
    existing_pf = DATA_DIR / "cogs_variance.json"
    if existing_pf.exists():
        try:
            prev = json.loads(existing_pf.read_text(encoding="utf-8"))
            if out["cogs_pct_week"] is None and prev.get("cogs_pct_week") is not None:
                out["cogs_pct_week"] = prev["cogs_pct_week"]
                out["variance_to_goal_week"] = _vtg(out["cogs_pct_week"])
                log.info(f"Preserved FP% from email source: {out['cogs_pct_week']}%")
            if out["cogs_pct_month"] is None and prev.get("cogs_pct_month") is not None:
                out["cogs_pct_month"] = prev["cogs_pct_month"]
                out["variance_to_goal_month"] = _vtg(out["cogs_pct_month"])
        except Exception:
            pass

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
