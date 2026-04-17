#!/usr/bin/env python3
"""
Five Guys KY-2065 — Daily Dashboard Automation
Scrapes the Performance Metrics table from the CrunchTime Net Chef
manager dashboard (fiveguysfr77.net-chef.com) — all data is on the
first page after login, no navigation required.

GitHub Secrets required:
  CRUNCHTIME_USERNAME  – your Net Chef login
  CRUNCHTIME_PASSWORD  – your Net Chef password

Run manually:
  CRUNCHTIME_USERNAME=you CRUNCHTIME_PASSWORD=pass python scraper/main.py
"""

import os, sys, json, re, asyncio, logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# ─── Config ───────────────────────────────────────────────────────────────────
NETCHEF_BASE = "https://fiveguysfr77.net-chef.com"
USERNAME     = os.environ.get("CRUNCHTIME_USERNAME", "")
PASSWORD     = os.environ.get("CRUNCHTIME_PASSWORD", "")

ROOT     = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# Eastern time (UTC-4 summer / UTC-5 winter)
ET     = timezone(timedelta(hours=-4))
now_et = datetime.now(tz=ET)
yest   = now_et - timedelta(days=1)

RPT_DATE     = yest.strftime("%Y-%m-%d")           # 2026-04-09
RPT_MMDDYYYY = yest.strftime("%m/%d/%Y")           # 04/09/2026
RPT_DISPLAY  = yest.strftime("%A, %B %-d, %Y")     # Thursday, April 9, 2026
GEN_DISPLAY  = now_et.strftime("%-m/%-d/%Y at %-I:%M %p")

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


# ─── Parsing helpers ──────────────────────────────────────────────────────────
def parse_dollar(text: str) -> float | None:
    """'$3,802' or '($198)' → float (negative if parenthesised)"""
    if not text or text.strip() in ("", "—", "-"):
        return None
    t = text.strip()
    negative = t.startswith("(") and t.endswith(")")
    cleaned = re.sub(r"[^\d.]", "", t)
    try:
        v = float(cleaned)
        return -v if negative else v
    except ValueError:
        return None


def parse_pct(text: str) -> float | None:
    """'23.83%' → 23.83"""
    m = re.search(r"-?([\d.]+)\s*%", text)
    if m:
        v = float(m.group(1))
        return -v if text.strip().startswith("(") or "-" in text[:2] else v
    return None


def parse_number(text: str) -> float | None:
    """'18.85' or '(10.04)' → float"""
    if not text or text.strip() in ("", "—", "-"):
        return None
    t = text.strip()
    negative = t.startswith("(") and t.endswith(")")
    cleaned = re.sub(r"[^\d.]", "", t)
    try:
        v = float(cleaned)
        return -v if negative else v
    except ValueError:
        return None


def fmt_dollar(v: float | None) -> str:
    if v is None:
        return "—"
    if v < 0:
        return f"(${abs(v):,.2f})"
    return f"${v:,.2f}"


def fmt_pct(v: float | None, decimals: int = 2) -> str:
    if v is None:
        return "—"
    return f"{v:.{decimals}f}%"


def fmt_num(v: float | None, decimals: int = 2) -> str:
    if v is None:
        return "—"
    return f"{v:,.{decimals}f}"


def color_class(v: float | None, good_if_positive: bool = True) -> str:
    """Return CSS card class based on value sign."""
    if v is None:
        return "blue"
    if good_if_positive:
        return "green" if v >= 0 else "highlight"
    else:
        return "green" if v <= 0 else "highlight"


# ─── Scraper ──────────────────────────────────────────────────────────────────
async def do_login(page) -> bool:
    log.info(f"Loading {NETCHEF_BASE} …")
    try:
        await page.goto(NETCHEF_BASE, wait_until="domcontentloaded", timeout=30_000)
    except Exception as e:
        log.error(f"Failed to load login page: {e}")
        return False

    await page.screenshot(path=str(DATA_DIR / "01_login.png"))

    # Wait for the login form to render — CrunchTime's login page is also
    # ExtJS-driven; the input fields are injected by JavaScript after load.
    USERNAME_SELS = [
        'input[name*="user" i]', 'input[id*="user" i]',
        'input[name*="login" i]', 'input[id*="login" i]',
        'input[type="text"]',
    ]
    log.info("Waiting for login form to render (up to 30 s)…")
    username_sel_found = None
    for sel in USERNAME_SELS:
        try:
            await page.wait_for_selector(sel, timeout=30_000)
            username_sel_found = sel
            log.info(f"Login form ready — found: {sel}")
            break
        except PlaywrightTimeout:
            continue

    if not username_sel_found:
        await page.screenshot(path=str(DATA_DIR / "01_login_failed.png"))
        log.error("Username field not found after 30 s — see 01_login_failed.png")
        return False

    # Find username field
    for sel in USERNAME_SELS:
        if await page.locator(sel).count():
            await page.fill(sel, USERNAME)
            log.info(f"Username filled ({sel})")
            break
    else:
        log.error("Username field not found — see 01_login.png")
        return False

    # Find password field
    for sel in ['input[type="password"]', 'input[name*="pass" i]']:
        if await page.locator(sel).count():
            await page.fill(sel, PASSWORD)
            log.info("Password filled")
            break
    else:
        log.error("Password field not found")
        return False

    # Submit — only click elements that are actually visible
    # (CrunchTime has a hidden input[type="submit"] with class x-hidden-submit
    # that must be skipped; the real trigger is Enter or a visible button)
    submitted = False
    for sel in [
        'button[type="submit"]',
        'button:has-text("Log")', 'button:has-text("Sign")', 'button:has-text("Login")',
        '#btnLogin', '.btn-login', '.login-button',
        'a:has-text("Log In")', 'a:has-text("Login")',
    ]:
        loc = page.locator(sel)
        if await loc.count() and await loc.first.is_visible():
            await loc.first.click()
            log.info(f"Submitted via visible button: {sel}")
            submitted = True
            break

    if not submitted:
        # Fall back to Enter key — works on any standard login form
        await page.keyboard.press("Enter")
        log.info("Submitted via Enter key")

    try:
        await page.wait_for_load_state("networkidle", timeout=45_000)
        log.info("Network idle after login")
    except PlaywrightTimeout:
        log.warning("Network not idle after 45 s — continuing")

    await page.screenshot(path=str(DATA_DIR / "02_after_login.png"))
    log.info(f"Post-login URL: {page.url}")

    if any(kw in page.url.lower() for kw in ["login", "signin", "logon"]):
        log.error("Still on login page — check credentials (see 02_after_login.png)")
        return False

    # Log what the post-login page actually shows
    try:
        post_text = await page.inner_text("body")
        log.info(f"Post-login page text ({len(post_text)} chars):\n---\n{post_text[:600]}\n---")
    except Exception:
        pass

    log.info("Login successful")
    return True


async def select_location(page):
    """
    Select store KY-2065-Dixie Highway from the 'Choose Location / Customer' combo box.

    The picker is an ExtJS combo box: a text input with a dropdown arrow (▼).
    The dropdown list items are formatted as 'KY-XXXX-Location Name'.
    We must: (1) click the input to open the dropdown, (2) optionally type to
    filter, (3) click 'KY-2065-Dixie Highway'.
    """
    LOCATION_FULL  = "KY-2065-Dixie Highway"
    LOCATION_SHORT = "KY-2065"

    log.info("Selecting location KY-2065-Dixie Highway…")
    log.info(f"Current URL: {page.url}")

    # ── Wait for the location picker form to appear ────────────────────────
    log.info("Waiting for location picker to render (up to 60 s)…")
    try:
        await page.wait_for_load_state("networkidle", timeout=60_000)
        log.info("Network idle")
    except PlaywrightTimeout:
        log.warning("Network not idle after 60 s — continuing")

    try:
        await page.wait_for_function(
            "() => document.body.innerText.trim().length > 200",
            timeout=60_000,
            polling=1_000,
        )
        body_len = await page.evaluate("() => document.body.innerText.trim().length")
        log.info(f"Page rendered — {body_len} chars visible")
    except PlaywrightTimeout:
        body_len = await page.evaluate("() => document.body.innerText.trim().length")
        log.warning(f"Page still minimal after 60 s ({body_len} chars) — proceeding anyway")

    # Log and screenshot so we can see what rendered
    try:
        pg_text = await page.inner_text("body")
        log.info(f"PAGE TEXT ({len(pg_text)} chars):\n---\n{pg_text[:800]}\n---")
        await page.screenshot(path=str(DATA_DIR / "02c_before_location_click.png"))
        (DATA_DIR / "02b_page_source.html").write_text(await page.content(), encoding="utf-8")
        (DATA_DIR / "02b_page_text.txt").write_text(pg_text, encoding="utf-8")
        log.info("Saved 02b debug snapshots")
    except Exception as exc:
        log.warning(f"Debug snapshot failed: {exc}")

    # ── Step 1: open the combo box ─────────────────────────────────────────
    # The picker is an ExtJS combo — must click the input/trigger to open it.
    combo_opened = False
    for sel in [
        ".x-form-trigger",           # ExtJS combo dropdown arrow (▼)
        ".x-form-trigger-wrap",      # wrapper around the trigger
        "input.x-form-field",        # ExtJS text field
        'input[type="text"]',        # generic text input
    ]:
        try:
            loc = page.locator(sel)
            if await loc.count():
                await loc.first.click()
                log.info(f"Clicked combo box via: {sel}")
                combo_opened = True
                await page.wait_for_timeout(1_500)
                break
        except Exception:
            continue

    if not combo_opened:
        log.warning("Could not find combo box input to open")

    # ── Step 2: type to filter the list ───────────────────────────────────
    try:
        await page.keyboard.type("2065", delay=80)
        log.info("Typed '2065' to filter dropdown")
        await page.wait_for_timeout(1_500)
        await page.screenshot(path=str(DATA_DIR / "02d_after_typing.png"))
    except Exception as exc:
        log.warning(f"Could not type in combo: {exc}")

    # ── Step 3: click the matching list item ──────────────────────────────
    # After typing, only KY-2065-Dixie Highway should remain visible.
    item_selectors = [
        f'.x-boundlist-item:has-text("{LOCATION_SHORT}")',
        f'.x-list-item:has-text("{LOCATION_SHORT}")',
        f'li:has-text("{LOCATION_FULL}")',
        f'li:has-text("{LOCATION_SHORT}")',
        f'div.x-boundlist-item:has-text("{LOCATION_SHORT}")',
        f'[role="option"]:has-text("{LOCATION_SHORT}")',
        f'option:has-text("{LOCATION_SHORT}")',
        f'option[value*="2065"]',
        f'tr:has-text("{LOCATION_SHORT}")',
        f'td:has-text("{LOCATION_FULL}")',
    ]

    for sel in item_selectors:
        try:
            loc = page.locator(sel)
            cnt = await loc.count()
            if not cnt:
                continue
            log.info(f"Found {cnt} item(s) via: {sel}")
            tag = await loc.first.evaluate("el => el.tagName.toLowerCase()")
            if tag == "option":
                await loc.first.locator("xpath=..").select_option(label=LOCATION_FULL)
                log.info(f"Selected via <select>")
            else:
                await loc.first.click()
                log.info(f"Clicked '{LOCATION_FULL}'")
            await _after_location_click(page)
            return
        except Exception as exc:
            log.debug(f"Item selector '{sel}' raised: {exc}")
            continue

    # ── Step 4: JavaScript fallback (search full page for KY-2065) ────────
    log.info("CSS selectors failed — trying JavaScript text search")
    try:
        clicked = await page.evaluate(f"""
            (() => {{
                const targets = ['{LOCATION_FULL}', '{LOCATION_SHORT}'];
                for (const target of targets) {{
                    for (const el of document.querySelectorAll(
                            'li, div, span, td, option, [role="option"]')) {{
                        const t = el.textContent.trim();
                        if (t.includes(target) && t.length < 80) {{
                            el.click();
                            return t;
                        }}
                    }}
                }}
                return null;
            }})()
        """)
        if clicked:
            log.info(f"JS clicked: '{clicked}'")
            await _after_location_click(page)
            return
        log.warning("JavaScript could not find location element")
    except Exception as exc:
        log.warning(f"JavaScript click failed: {exc}")

    log.info("Location picker not found — assuming already on correct store")
    await page.screenshot(path=str(DATA_DIR / "03_no_picker.png"))


async def _after_location_click(page):
    """Wait for the dashboard to load after clicking a location."""
    try:
        await page.wait_for_function(
            "() => !window.location.href.includes('ChooseLocation')",
            timeout=15_000,
        )
        log.info("URL left ChooseLocation — navigating to dashboard")
    except PlaywrightTimeout:
        log.warning("URL still contains ChooseLocation after 15 s")
    try:
        await page.wait_for_load_state("networkidle", timeout=15_000)
    except PlaywrightTimeout:
        pass
    await page.screenshot(path=str(DATA_DIR / "03_location_selected.png"))
    log.info(f"Post-selection URL: {page.url}")


async def extract_performance_metrics(page) -> dict:
    """
    Extract Performance Metrics from CrunchTime Net Chef.

    CrunchTime is an ExtJS application. Depending on the version it may render
    its data grid as real <table>/<tr>/<td> elements (ExtJS classic) or as
    div-based rows (ExtJS modern). We try three strategies in order:

      1. HTML <table> rows  — fastest when available
      2. ExtJS div-based grid rows (.x-grid-row / .x-grid-cell-inner)
      3. Full page text parsing — slow but works regardless of DOM structure

    Screenshots are taken at three scroll positions so the action log always
    shows what the browser actually saw, even on failure.
    """
    log.info("Extracting Performance Metrics…")
    log.info(f"Current URL: {page.url}")

    # Print what's visible on screen right now
    try:
        current_text = await page.inner_text("body")
        log.info(f"PAGE TEXT AT EXTRACTION START ({len(current_text)} chars):\n---\n{current_text[:800]}\n---")
    except Exception:
        pass

    # ── If still on location picker, try once more ─────────────────────────
    if "ChooseLocation" in page.url:
        log.warning("Still on ChooseLocation — retrying select_location()")
        await select_location(page)
        await page.wait_for_timeout(3_000)

    # ── Wait for dashboard content to appear ──────────────────────────────
    # Give ExtJS up to 30 s per keyword to render the dashboard grid.
    for keyword in ["Actual Net Sales", "Net Sales", "Performance"]:
        try:
            await page.wait_for_selector(f"text={keyword}", timeout=30_000)
            log.info(f"Dashboard content detected: '{keyword}'")
            break
        except PlaywrightTimeout:
            log.info(f"Keyword '{keyword}' not found within 30 s, continuing…")

    # ── Scroll to load all lazy-rendered rows ──────────────────────────────
    await page.screenshot(path=str(DATA_DIR / "04_dashboard_top.png"))

    await page.evaluate("window.scrollBy(0, 800)")
    await page.wait_for_timeout(1_500)
    await page.screenshot(path=str(DATA_DIR / "05_dashboard_mid.png"))

    await page.evaluate("window.scrollBy(0, 800)")
    await page.wait_for_timeout(1_500)
    await page.screenshot(path=str(DATA_DIR / "06_dashboard_bottom.png"))

    await page.evaluate("window.scrollTo(0, 0)")
    await page.wait_for_timeout(500)

    # ── Save full page source for debugging ────────────────────────────────
    try:
        html_content = await page.content()
        (DATA_DIR / "page_source.html").write_text(html_content, encoding="utf-8")
        log.info(f"Saved page_source.html ({len(html_content):,} bytes)")
    except Exception as exc:
        log.warning(f"Could not save page source: {exc}")

    # ──────────────────────────────────────────────────────────────────────
    # STRATEGY 1: Real HTML <table> rows
    # ──────────────────────────────────────────────────────────────────────
    metrics = await _extract_from_tables(page)
    if metrics:
        log.info(f"Strategy 1 (tables) succeeded: {len(metrics)} metrics")
        return metrics

    # ──────────────────────────────────────────────────────────────────────
    # STRATEGY 2: ExtJS div-based grid
    # ──────────────────────────────────────────────────────────────────────
    log.info("Strategy 1 (tables) found nothing — trying ExtJS div grid…")
    metrics = await _extract_from_extjs_divs(page)
    if metrics:
        log.info(f"Strategy 2 (ExtJS divs) succeeded: {len(metrics)} metrics")
        return metrics

    # ──────────────────────────────────────────────────────────────────────
    # STRATEGY 3: Page text parsing
    # ──────────────────────────────────────────────────────────────────────
    log.info("Strategy 2 (ExtJS divs) found nothing — trying text extraction…")
    metrics = await _extract_from_page_text(page)
    if metrics:
        log.info(f"Strategy 3 (text) succeeded: {len(metrics)} metrics")
    else:
        log.warning("All three extraction strategies returned no data")
    return metrics


# ── Extraction helpers ────────────────────────────────────────────────────────

async def _extract_from_tables(page) -> dict:
    """Strategy 1: classic <table>/<tr>/<td> extraction."""
    tables = await page.locator("table").all()
    log.info(f"Found {len(tables)} <table> element(s)")

    metrics: dict[str, dict] = {}

    for tbl_idx, tbl in enumerate(tables):
        rows = await tbl.locator("tr").all()
        if not rows:
            continue

        header_cells = await rows[0].locator("td, th").all()
        headers = [(await c.inner_text()).strip() for c in header_cells]
        log.info(f"  Table {tbl_idx} headers: {headers}")

        day_col = week_col = None
        for i, h in enumerate(headers):
            if RPT_MMDDYYYY in h:
                day_col = i
            if "week" in h.lower() or "wtd" in h.lower():
                week_col = i

        # If exact date not found, default to column 1 (first data column)
        if day_col is None and len(headers) >= 2:
            log.info(f"  Table {tbl_idx}: date '{RPT_MMDDYYYY}' not in headers; using col 1")
            day_col = 1
        if day_col is None:
            continue

        for row in rows[1:]:
            cells = await row.locator("td, th").all()
            if len(cells) <= day_col:
                continue
            label    = (await cells[0].inner_text()).strip()
            day_val  = (await cells[day_col].inner_text()).strip()
            week_val = (await cells[week_col].inner_text()).strip() if week_col and week_col < len(cells) else ""
            if label and any(c.isalpha() for c in label):
                metrics[label] = {"day": day_val, "week": week_val}
                log.info(f"    {label!r:45s} day={day_val!r:15s} week={week_val!r}")

    return metrics


async def _extract_from_extjs_divs(page) -> dict:
    """Strategy 2: ExtJS modern toolkit uses div-based grid rows."""
    # Try to find any kind of row container
    row_sel = None
    for sel in [".x-grid-row", ".x-grid-item", "[class*='x-grid-row']"]:
        if await page.locator(sel).count():
            row_sel = sel
            break

    if not row_sel:
        log.info("No ExtJS div rows found")
        return {}

    rows = await page.locator(row_sel).all()
    log.info(f"Found {len(rows)} ExtJS div row(s) via '{row_sel}'")

    # Determine column structure from header
    day_col_idx  = 1    # default: col 0 = label, col 1 = day value
    week_col_idx = 2

    hdr_texts = []
    for hsel in [".x-column-header-text", ".x-column-header"]:
        hdrs = await page.locator(hsel).all()
        if hdrs:
            hdr_texts = [(await h.inner_text()).strip() for h in hdrs]
            log.info(f"Column headers: {hdr_texts}")
            for i, h in enumerate(hdr_texts):
                if RPT_MMDDYYYY in h:
                    day_col_idx = i
                if "week" in h.lower() or "wtd" in h.lower():
                    week_col_idx = i
            break

    metrics: dict[str, dict] = {}

    for row in rows:
        # ExtJS stores cell text in .x-grid-cell-inner; fall back to td
        for csel in [".x-grid-cell-inner", ".x-grid-cell", "td"]:
            cells = await row.locator(csel).all()
            if cells:
                break
        else:
            continue

        texts = [(await c.inner_text()).strip() for c in cells]
        if not texts or not texts[0]:
            continue

        label    = texts[0]
        day_val  = texts[day_col_idx]  if day_col_idx  < len(texts) else ""
        week_val = texts[week_col_idx] if week_col_idx < len(texts) else ""

        if label and any(c.isalpha() for c in label):
            metrics[label] = {"day": day_val, "week": week_val}
            log.info(f"  {label!r:45s} day={day_val!r:15s} week={week_val!r}")

    return metrics


async def _extract_from_page_text(page) -> dict:
    """
    Strategy 3: grab all visible text, then match known metric labels.

    CrunchTime's grid puts each row on a line:
      'Actual Net Sales   $3,801.80   $18,500.00   ...'
    We find lines containing a known label and parse the first two
    dollar/percent values as day and week figures.
    """
    try:
        full_text = await page.inner_text("body")
    except Exception as exc:
        log.error(f"inner_text() failed: {exc}")
        return {}

    (DATA_DIR / "page_text.txt").write_text(full_text, encoding="utf-8")
    log.info(f"Page text: {len(full_text)} chars, saved to page_text.txt")

    lines = [ln.strip() for ln in full_text.splitlines() if ln.strip()]
    log.info(f"Non-empty lines: {len(lines)}")

    if len(lines) < 5:
        log.warning("Very few lines — dashboard may not have loaded")
        return {}

    KNOWN_LABELS = [
        "Actual Net Sales", "Last Year Same Day", "Forecasted Sales",
        "Net Sales to Last Year", "Actual Labor", "Labor % of Net Sales",
        "Actual Hours", "Scheduled Hours", "Hours Variance",
        "Labor Productivity", "Total Cash Over/Short",
        "Comps and Discounts", "Sales / Guest", "Guest Count",
    ]

    VALUE_RE = re.compile(r'[\(\$]?[\d,]+\.?\d*\s*%?')

    metrics: dict[str, dict] = {}

    for i, line in enumerate(lines):
        matched_label = None
        for lbl in KNOWN_LABELS:
            if lbl.lower() in line.lower():
                matched_label = lbl
                break
        if not matched_label:
            continue

        # Collect values from this line and the next few (until next label)
        candidate_lines = [line]
        for j in range(i + 1, min(i + 5, len(lines))):
            if any(lbl.lower() in lines[j].lower() for lbl in KNOWN_LABELS):
                break
            candidate_lines.append(lines[j])

        combined = " ".join(candidate_lines)
        values   = VALUE_RE.findall(combined)
        # Strip bare numbers that are just "2065" or years — keep $-prefixed or %
        values   = [v.strip() for v in values if v.strip() and len(v.strip()) > 1]

        day_val  = values[0] if len(values) > 0 else ""
        week_val = values[1] if len(values) > 1 else ""

        metrics[matched_label] = {"day": day_val, "week": week_val}
        log.info(f"  Text-parsed {matched_label!r}: day={day_val!r} week={week_val!r}")

    return metrics


def parse_metrics(raw: dict[str, dict]) -> dict:
    """Map raw row labels → structured data dict."""

    def get(keys: list[str], field: str = "day") -> str:
        """Find first matching key (case-insensitive prefix match)."""
        for k in keys:
            for label, vals in raw.items():
                if label.lower().startswith(k.lower()):
                    return vals.get(field, "")
        return ""

    net_sales_d   = get(["Actual Net Sales"])
    net_sales_w   = get(["Actual Net Sales"], "week")
    ly_sales_d    = get(["Last Year Same Day"])
    ly_sales_w    = get(["Last Year Same Day"], "week")
    forecast_d    = get(["Forecasted Sales"])
    forecast_w    = get(["Forecasted Sales"], "week")
    vs_ly_d       = get(["Net Sales to Last Ye"])
    vs_ly_w       = get(["Net Sales to Last Ye"], "week")
    labor_cost_d       = get(["Actual Labor"])
    labor_cost_w       = get(["Actual Labor"], "week")
    labor_hrs_d        = get(["Actual to Earned Ho"])
    labor_pct_d        = get(["Labor % of Net Sales"])
    labor_pct_w        = get(["Labor % of Net Sales"], "week")
    actual_hours_d     = get(["Actual Hours"])
    actual_hours_w     = get(["Actual Hours"], "week")
    scheduled_hours_d  = get(["Scheduled Hours"])
    scheduled_hours_w  = get(["Scheduled Hours"], "week")
    hours_variance_d   = get(["Hours Variance"])
    labor_productivity_d = get(["Labor Productivity"])
    labor_productivity_w = get(["Labor Productivity"], "week")
    cash_os_d          = get(["Total Cash Over/Sh"])
    # Comps rows — there are multiple; collect all
    comps_rows = {
        label: vals for label, vals in raw.items()
        if label.lower().startswith("comps and discoun")
    }
    sales_per_guest_d = get(["Sales / Guest"])
    sales_per_guest_w = get(["Sales / Guest"], "week")

    net_sales   = parse_dollar(net_sales_d)
    labor_cost  = parse_dollar(labor_cost_d)
    labor_pct   = parse_pct(labor_pct_d)
    labor_hrs   = parse_number(labor_hrs_d)   # Actual to Earned Hours
    vs_ly       = parse_dollar(vs_ly_d)
    forecast    = parse_dollar(forecast_d)
    cash_os     = parse_dollar(cash_os_d)

    # Compute derived values
    labor_splh = None
    if net_sales and labor_hrs is not None and labor_hrs != 0:
        # labor_hrs here is actual-to-earned variance; use labor_pct to back-calc if needed
        pass

    # vs forecast
    vs_forecast = None
    if net_sales is not None and forecast is not None:
        vs_forecast = net_sales - forecast

    comps_list = []
    for label, vals in comps_rows.items():
        v = parse_dollar(vals.get("day", "")) or parse_pct(vals.get("day", ""))
        if v is not None:
            comps_list.append({"name": label, "day": vals.get("day", ""), "week": vals.get("week", "")})

    return {
        "meta": {
            "report_date":    RPT_DATE,
            "report_display": RPT_DISPLAY,
            "generated":      GEN_DISPLAY,
        },
        "sales": {
            "net":          net_sales,
            "net_week":     parse_dollar(net_sales_w),
            "ly":           parse_dollar(ly_sales_d),
            "ly_week":      parse_dollar(ly_sales_w),
            "forecast":     forecast,
            "forecast_week":parse_dollar(forecast_w),
            "vs_ly":        vs_ly,
            "vs_ly_week":   parse_dollar(vs_ly_w),
            "vs_forecast":  vs_forecast,
            "per_guest":    parse_dollar(sales_per_guest_d),
            "per_guest_week": parse_dollar(sales_per_guest_w),
        },
        "labor": {
            "cost":              labor_cost,
            "cost_week":         parse_dollar(labor_cost_w),
            "pct":               labor_pct,
            "pct_week":          parse_pct(labor_pct_w),
            "actual_hours":      parse_number(actual_hours_d),
            "actual_hours_week": parse_number(actual_hours_w),
            "sched_hours":       parse_number(scheduled_hours_d),
            "sched_hours_week":  parse_number(scheduled_hours_w),
            "hours_variance":    parse_number(hours_variance_d),
            "productivity":      parse_dollar(labor_productivity_d),
            "productivity_week": parse_dollar(labor_productivity_w),
            "hours_var":         parse_number(labor_hrs_d),  # Actual-to-Earned (kept for compat)
        },
        "cash": {
            "over_short":   cash_os,
        },
        "comps": comps_list,
        "raw": raw,  # keep full raw data in JSON snapshot
    }


async def scrape() -> dict:
    async with async_playwright() as pw:
        # Run headed (non-headless) so ExtJS renders properly.
        # On CI the DISPLAY env var set by xvfb-run provides a virtual screen.
        browser = await pw.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--window-size=1440,900",
            ],
        )
        ctx = await browser.new_context(
            viewport={"width": 1440, "height": 900},
        )
        await ctx.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )
        page = await ctx.new_page()

        # Log any JavaScript errors/warnings from the browser
        def _on_console(msg):
            if msg.type in ("error", "warning"):
                log.warning(f"BROWSER CONSOLE {msg.type.upper()}: {msg.text}")
        def _on_pageerror(exc):
            log.error(f"BROWSER JS ERROR: {exc}")
        page.on("console", _on_console)
        page.on("pageerror", _on_pageerror)

        if not await do_login(page):
            await browser.close()
            raise RuntimeError("Login failed — check credentials and screenshots in data/")

        # Select store 2065 if a location picker appears after login
        await select_location(page)

        # All data is on the first page — scroll to load all rows then extract
        raw = await extract_performance_metrics(page)
        await browser.close()

        if not raw:
            raise RuntimeError(
                f"No Performance Metrics data found for {RPT_MMDDYYYY}. "
                "Check data/03_dashboard.png to see what the page looks like."
            )

        return parse_metrics(raw)


# ─── HTML Generator ───────────────────────────────────────────────────────────
def trend_arrow(v: float | None) -> str:
    if v is None:
        return ""
    return " &#9650;" if v >= 0 else " &#9660;"


def generate_html(d: dict) -> str:
    meta = d.get("meta", {})
    s    = d.get("sales", {})
    lab  = d.get("labor", {})
    cash = d.get("cash", {})
    comps = d.get("comps", [])

    rpt_display = meta.get("report_display", RPT_DISPLAY)
    generated   = meta.get("generated",      GEN_DISPLAY)

    # ── vs LY color ────────────────────────────────────────────────────────────
    vs_ly       = s.get("vs_ly")
    vs_ly_w     = s.get("vs_ly_week")
    vs_fc       = s.get("vs_forecast")
    vs_ly_cls   = color_class(vs_ly)
    vs_ly_w_cls = color_class(vs_ly_w)
    vs_fc_cls   = color_class(vs_fc)

    # ── Labor % color ──────────────────────────────────────────────────────────
    lp = lab.get("pct")
    lab_cls = "green" if lp and lp < 25 else ("orange" if lp and lp < 30 else "highlight")

    # ── Cash over/short color ──────────────────────────────────────────────────
    cos = cash.get("over_short", 0.0)
    cos_cls = "green" if cos == 0 else ("orange" if cos and abs(cos) < 50 else "highlight")

    # ── Comps rows HTML ────────────────────────────────────────────────────────
    comps_rows = ""
    for c in comps:
        comps_rows += f"""
        <tr>
          <td>{c['name']}</td>
          <td style="text-align:right;">{c['day']}</td>
          <td style="text-align:right;">{c['week']}</td>
        </tr>"""
    if not comps_rows:
        comps_rows = '<tr><td colspan="3" style="color:#aaa;padding:12px 16px;">No comps data found</td></tr>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Five Guys KY-2065 Dixie Highway | Daily Dashboard</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f0f2f5; color: #222; }}
  header {{ background: #d52b1e; color: white; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; }}
  header h1 {{ font-size: 1.6em; font-weight: 700; }}
  header .date-info {{ text-align: right; font-size: 0.95em; opacity: 0.9; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 24px 16px; }}
  .section-title {{ font-size: 1.1em; font-weight: 700; color: #d52b1e; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 14px; padding-bottom: 6px; border-bottom: 2px solid #d52b1e; }}
  .section {{ margin-bottom: 28px; }}
  .card-grid {{ display: grid; gap: 14px; }}
  .grid-4 {{ grid-template-columns: repeat(4, 1fr); }}
  .grid-3 {{ grid-template-columns: repeat(3, 1fr); }}
  .grid-2 {{ grid-template-columns: repeat(2, 1fr); }}
  .card {{ background: white; border-radius: 10px; padding: 18px 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.07); }}
  .card .label {{ font-size: 0.78em; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }}
  .card .value {{ font-size: 1.7em; font-weight: 700; color: #222; }}
  .card .sub {{ font-size: 0.82em; color: #aaa; margin-top: 4px; }}
  .card .week-val {{ font-size: 0.88em; color: #555; margin-top: 6px; border-top: 1px solid #f0f2f5; padding-top: 6px; }}
  .card.highlight {{ border-left: 4px solid #d52b1e; }}
  .card.green {{ border-left: 4px solid #27ae60; }}
  .card.orange {{ border-left: 4px solid #e67e22; }}
  .card.blue {{ border-left: 4px solid #2980b9; }}
  .neg {{ color: #d52b1e; }}
  .pos {{ color: #27ae60; }}
  .data-table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.07); }}
  .data-table th {{ background: #d52b1e; color: white; padding: 12px 16px; text-align: left; font-size: 0.85em; text-transform: uppercase; letter-spacing: 0.5px; }}
  .data-table th:not(:first-child) {{ text-align: right; }}
  .data-table td {{ padding: 11px 16px; border-bottom: 1px solid #f0f2f5; font-size: 0.95em; }}
  .data-table td:not(:first-child) {{ text-align: right; }}
  .data-table tr:last-child td {{ border-bottom: none; }}
  .data-table tr:hover td {{ background: #fdf5f5; }}
  footer {{ text-align: center; padding: 20px; color: #aaa; font-size: 0.8em; margin-top: 10px; }}
  @media (max-width: 900px) {{
    .grid-4 {{ grid-template-columns: repeat(2, 1fr); }}
    .grid-3 {{ grid-template-columns: repeat(2, 1fr); }}
  }}
  @media (max-width: 600px) {{
    .grid-4, .grid-3, .grid-2 {{ grid-template-columns: 1fr 1fr; }}
    header {{ flex-direction: column; gap: 8px; }}
  }}
</style>
</head>
<body>

<header>
  <div>
    <h1>&#127354; Five Guys | KY-2065 Dixie Highway</h1>
    <div style="font-size:0.85em;opacity:0.8;margin-top:4px;">Daily Operations Dashboard</div>
  </div>
  <div class="date-info">
    <div style="font-size:1.1em;font-weight:700;">{rpt_display}</div>
    <div>Generated {generated}</div>
  </div>
</header>

<div class="container">

  <!-- SECTION 1: Sales -->
  <div class="section">
    <div class="section-title">&#128200; Sales Overview</div>
    <div class="card-grid grid-4">

      <div class="card highlight">
        <div class="label">Actual Net Sales</div>
        <div class="value">{fmt_dollar(s.get('net'))}</div>
        <div class="sub">Yesterday</div>
        <div class="week-val">WTD: {fmt_dollar(s.get('net_week'))}</div>
      </div>

      <div class="card blue">
        <div class="label">Last Year Same Day</div>
        <div class="value">{fmt_dollar(s.get('ly'))}</div>
        <div class="sub">Prior year comparison</div>
        <div class="week-val">WTD LY: {fmt_dollar(s.get('ly_week'))}</div>
      </div>

      <div class="card blue">
        <div class="label">Forecasted Sales</div>
        <div class="value">{fmt_dollar(s.get('forecast'))}</div>
        <div class="sub">Projected for the day</div>
        <div class="week-val">WTD Forecast: {fmt_dollar(s.get('forecast_week'))}</div>
      </div>

      <div class="card green">
        <div class="label">Sales / Guest</div>
        <div class="value">{fmt_dollar(s.get('per_guest'))}</div>
        <div class="sub">Average per guest</div>
        <div class="week-val">WTD Avg: {fmt_dollar(s.get('per_guest_week'))}</div>
      </div>

    </div>
  </div>

  <!-- SECTION 2: vs Targets -->
  <div class="section">
    <div class="section-title">&#127919; Performance vs Targets</div>
    <div class="card-grid grid-3">

      <div class="card {vs_ly_cls}">
        <div class="label">vs Last Year (Day)</div>
        <div class="value {'neg' if vs_ly and vs_ly < 0 else 'pos'}">{fmt_dollar(vs_ly)}{trend_arrow(vs_ly)}</div>
        <div class="sub">Net Sales vs Same Day LY</div>
        <div class="week-val">WTD vs LY: <span class="{'neg' if vs_ly_w and vs_ly_w < 0 else 'pos'}">{fmt_dollar(vs_ly_w)}</span></div>
      </div>

      <div class="card {vs_fc_cls}">
        <div class="label">vs Forecast (Day)</div>
        <div class="value {'neg' if vs_fc and vs_fc < 0 else 'pos'}">{fmt_dollar(vs_fc)}{trend_arrow(vs_fc)}</div>
        <div class="sub">Actual vs Projected</div>
        <div class="week-val">&nbsp;</div>
      </div>

      <div class="card {cos_cls}">
        <div class="label">Cash Over / Short</div>
        <div class="value {'neg' if cos and cos < 0 else ''}">{fmt_dollar(cos)}</div>
        <div class="sub">{"On target" if cos == 0 else ("Over" if cos and cos > 0 else "Short")}</div>
        <div class="week-val">&nbsp;</div>
      </div>

    </div>
  </div>

  <!-- SECTION 3: Labor -->
  <div class="section">
    <div class="section-title">&#128104;&#8205;&#127859; Labor Summary</div>
    <div class="card-grid grid-4">

      <div class="card highlight">
        <div class="label">Actual Labor $</div>
        <div class="value">{fmt_dollar(lab.get('cost'))}</div>
        <div class="sub">Total wages</div>
        <div class="week-val">WTD: {fmt_dollar(lab.get('cost_week'))}</div>
      </div>

      <div class="card {lab_cls}">
        <div class="label">Labor % of Net Sales</div>
        <div class="value">{fmt_pct(lab.get('pct'))}</div>
        <div class="sub">{"On target" if lp and lp < 25 else "Above target" if lp else "—"}</div>
        <div class="week-val">WTD: {fmt_pct(lab.get('pct_week'))}</div>
      </div>

      <div class="card blue">
        <div class="label">Scheduled Hours</div>
        <div class="value">{fmt_num(lab.get('sched_hours'))}</div>
        <div class="sub">Hours on schedule</div>
        <div class="week-val">WTD: {fmt_num(lab.get('sched_hours_week'))}</div>
      </div>

      <div class="card blue">
        <div class="label">Actual Hours</div>
        <div class="value">{fmt_num(lab.get('actual_hours'))}</div>
        <div class="sub">Hours actually worked</div>
        <div class="week-val">WTD: {fmt_num(lab.get('actual_hours_week'))}</div>
      </div>

      <div class="card {'green' if (lab.get('hours_variance') or 0) >= 0 else 'orange'}">
        <div class="label">Hours Variance</div>
        <div class="value">{fmt_num(lab.get('hours_variance'))}</div>
        <div class="sub">Scheduled minus Actual</div>
        <div class="week-val">&nbsp;</div>
      </div>

      <div class="card green">
        <div class="label">Labor Productivity</div>
        <div class="value">{fmt_dollar(lab.get('productivity'))}</div>
        <div class="sub">Sales per labor hour</div>
        <div class="week-val">WTD: {fmt_dollar(lab.get('productivity_week'))}</div>
      </div>

    </div>
  </div>

  <!-- SECTION 4: Comps & Discounts -->
  <div class="section">
    <div class="section-title">&#127991; Comps &amp; Discounts</div>
    <table class="data-table">
      <thead>
        <tr>
          <th>Type</th>
          <th>Yesterday</th>
          <th>Week-to-Date</th>
        </tr>
      </thead>
      <tbody>{comps_rows}
      </tbody>
    </table>
  </div>

</div>

<footer>
  Five Guys KY-2065 Dixie Highway &bull; Source: CrunchTime Net Chef &bull;
  Business Date: {rpt_display} &bull; Generated: {generated}
</footer>

</body>
</html>"""


# ─── Main ─────────────────────────────────────────────────────────────────────
async def main():
    if not USERNAME or not PASSWORD:
        log.error("Set CRUNCHTIME_USERNAME and CRUNCHTIME_PASSWORD env vars")
        sys.exit(1)

    log.info(f"=== Five Guys KY-2065 Dashboard — {RPT_DISPLAY} ===")
    log.info(f"Looking for column: {RPT_MMDDYYYY}")

    try:
        data = await scrape()
        log.info("Scrape succeeded")
    except Exception as e:
        log.error(f"Scrape failed: {e}")
        fallback = DATA_DIR / "latest.json"
        if fallback.exists():
            log.warning("Using cached data from previous run")
            data = json.loads(fallback.read_text())
            data["meta"]["generated"] = GEN_DISPLAY + " (cached)"
        else:
            log.error("No cached data — cannot generate dashboard")
            sys.exit(1)

    # Save snapshot
    (DATA_DIR / "latest.json").write_text(json.dumps(data, indent=2, default=str))
    log.info("Saved data/latest.json")

    # Generate dashboard
    html = generate_html(data)
    out  = ROOT / "dashboard.html"
    out.write_text(html, encoding="utf-8")
    log.info(f"Wrote {out} ({len(html):,} bytes)")
    log.info("Done.")


if __name__ == "__main__":
    asyncio.run(main())
