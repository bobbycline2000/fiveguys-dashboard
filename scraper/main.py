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


async def _click_sign_in(page) -> bool:
    """Click the Sign In / confirm button on the location picker. Returns True on success."""
    for sel in [
        'button:has-text("Sign In")',
        'a:has-text("Sign In")',
        '.x-btn:has-text("Sign In")',
        '.x-btn-inner:has-text("Sign In")',
        'input[value="Sign In"]',
        'button:has-text("Go")',
        'button:has-text("Select")',
        'button:has-text("OK")',
        'button:has-text("Continue")',
    ]:
        try:
            loc = page.locator(sel)
            if await loc.count():
                await loc.first.click()
                log.info(f"Clicked Sign In via: {sel}")
                await _after_location_click(page)
                return True
        except Exception:
            continue
    log.warning("Sign In button not found")
    return False


async def select_location(page):
    """
    Select KY-2065-Dixie Highway and click Sign In to confirm.

    Version 20.26.04.02 of CrunchTime shows the location pre-filled in the
    combo box. The flow is: location is already shown → click "Sign In".
    Falls back to typing '2065' to filter, then clicking Sign In.
    """
    LOCATION_FULL  = "KY-2065-Dixie Highway"
    LOCATION_SHORT = "KY-2065"

    log.info("Selecting location KY-2065-Dixie Highway…")
    log.info(f"Current URL: {page.url}")

    # ── Wait for ExtJS to render ───────────────────────────────────────────
    log.info("Waiting for location picker to render (up to 60 s)…")
    try:
        await page.wait_for_load_state("networkidle", timeout=60_000)
        log.info("Network idle")
    except PlaywrightTimeout:
        log.warning("Network not idle after 60 s — continuing")

    try:
        await page.wait_for_function(
            "() => document.body.innerText.trim().length > 100",
            timeout=60_000,
            polling=1_000,
        )
        body_len = await page.evaluate("() => document.body.innerText.trim().length")
        log.info(f"Page rendered — {body_len} chars visible")
    except PlaywrightTimeout:
        body_len = await page.evaluate("() => document.body.innerText.trim().length")
        log.warning(f"Page still minimal after 60 s ({body_len} chars) — proceeding")

    # Debug snapshots
    try:
        pg_text = await page.inner_text("body")
        log.info(f"PAGE TEXT ({len(pg_text)} chars):\n---\n{pg_text[:800]}\n---")
        await page.screenshot(path=str(DATA_DIR / "02c_before_location_click.png"))
        (DATA_DIR / "02b_page_source.html").write_text(await page.content(), encoding="utf-8")
        (DATA_DIR / "02b_page_text.txt").write_text(pg_text, encoding="utf-8")
        log.info("Saved 02b debug snapshots")
    except Exception as exc:
        log.warning(f"Debug snapshot failed: {exc}")

    # ── FAST PATH: location already visible → just click Sign In ─────────
    # v20.26.04.02 pre-fills the combo with the user's only location.
    try:
        pg_text = await page.inner_text("body")
        if LOCATION_SHORT in pg_text or LOCATION_FULL in pg_text:
            log.info(f"Location '{LOCATION_SHORT}' already visible — clicking Sign In")
            if await _click_sign_in(page):
                return
    except Exception as exc:
        log.warning(f"Fast path check failed: {exc}")

    # ── METHOD 1: ExtJS programmatic ──────────────────────────────────────
    log.info("Method 1: ExtJS programmatic selection…")
    try:
        result = await page.evaluate("""
            (() => {
                try {
                    if (typeof Ext === 'undefined') return 'Ext not loaded';
                    var combos = Ext.ComponentQuery.query('combo, combobox');
                    for (var i = 0; i < combos.length; i++) {
                        var combo = combos[i];
                        var store = combo.getStore ? combo.getStore() : null;
                        if (!store) continue;
                        var found = null;
                        store.each(function(rec) {
                            var allFields = Object.keys(rec.getData());
                            for (var f of allFields) {
                                if (String(rec.get(f)).includes('2065')) {
                                    found = rec; return false;
                                }
                            }
                        });
                        if (!found && store.getCount() === 1) {
                            found = store.getAt(0);
                        }
                        if (found) {
                            combo.setValue(found);
                            combo.fireEvent('select', combo, [found]);
                            return 'selected: ' + JSON.stringify(found.getData()).substring(0, 100);
                        }
                    }
                    return 'combo count=' + combos.length + ' no match';
                } catch(e) { return 'error: ' + e.message; }
            })()
        """)
        log.info(f"ExtJS method 1 result: {result}")
        if result and result.startswith("selected:"):
            await page.wait_for_timeout(1_000)
            if await _click_sign_in(page):
                return
            await _after_location_click(page)
            return
    except Exception as exc:
        log.warning(f"ExtJS method failed: {exc}")

    # ── METHOD 2: Click input → type "2065" → Sign In ─────────────────────
    log.info("Method 2: click + type to filter…")
    input_clicked = False
    for sel in ["input.x-form-field", "input.x-form-text", 'input[type="text"]',
                ".x-form-trigger", ".x-form-trigger-wrap"]:
        try:
            loc = page.locator(sel)
            if await loc.count():
                await loc.first.click()
                log.info(f"Opened combo via: {sel}")
                input_clicked = True
                await page.wait_for_timeout(1_000)
                break
        except Exception:
            continue

    if input_clicked:
        try:
            await page.keyboard.press("Control+a")
            await page.keyboard.press("Delete")
            await page.keyboard.type("2065", delay=100)
            log.info("Typed '2065' to filter list")
            await page.wait_for_timeout(2_000)
            await page.screenshot(path=str(DATA_DIR / "02d_after_typing.png"))
        except Exception as exc:
            log.warning(f"Typing failed: {exc}")

    for sel in [
        f'.x-boundlist-item:has-text("{LOCATION_SHORT}")',
        f'.x-list-item:has-text("{LOCATION_SHORT}")',
        f'[role="option"]:has-text("{LOCATION_SHORT}")',
        f'li:has-text("{LOCATION_SHORT}")',
        f'div.x-boundlist-item',
    ]:
        try:
            loc = page.locator(sel)
            cnt = await loc.count()
            if not cnt:
                continue
            log.info(f"Found {cnt} list item(s) via: {sel}")
            await loc.first.click()
            log.info("Clicked list item")
            await page.wait_for_timeout(1_000)
            if await _click_sign_in(page):
                return
            await _after_location_click(page)
            return
        except Exception:
            continue

    # After typing, try Sign In (combo may have auto-selected the filtered result)
    log.info("Trying Sign In after typing filter…")
    if await _click_sign_in(page):
        return

    # ── METHOD 3: JS text search click → Sign In ──────────────────────────
    log.info("Method 3: open dropdown, scroll, JS text search…")

    for sel in [".x-form-trigger", "button", ".x-form-arrow-trigger"]:
        try:
            loc = page.locator(sel)
            if await loc.count():
                await loc.first.click()
                await page.wait_for_timeout(1_500)
                log.info(f"Opened dropdown via: {sel}")
                break
        except Exception:
            continue

    try:
        scroll_result = await page.evaluate("""
            (() => {
                var selectors = [
                    '.x-boundlist-list-ct', '.x-list-plain',
                    '.x-boundlist ul', '.x-boundlist'
                ];
                for (var s of selectors) {
                    var el = document.querySelector(s);
                    if (el) { el.scrollTop = 9999; return 'scrolled ' + s; }
                }
                return 'no dropdown list found';
            })()
        """)
        log.info(f"Scroll result: {scroll_result}")
        await page.wait_for_timeout(800)
        await page.screenshot(path=str(DATA_DIR / "02e_after_scroll.png"))
    except Exception as exc:
        log.warning(f"Scroll failed: {exc}")

    try:
        clicked = await page.evaluate(f"""
            (() => {{
                const targets = ['{LOCATION_FULL}', '{LOCATION_SHORT}'];
                for (const target of targets) {{
                    for (const el of document.querySelectorAll(
                            'li, div, span, td, option, [role="option"]')) {{
                        const t = el.textContent.trim();
                        if (t.includes(target) && t.length < 80) {{
                            el.dispatchEvent(new MouseEvent('mousedown', {{bubbles: true}}));
                            el.dispatchEvent(new MouseEvent('mouseup', {{bubbles: true}}));
                            el.dispatchEvent(new MouseEvent('click', {{bubbles: true}}));
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
            await page.wait_for_timeout(1_000)
            if await _click_sign_in(page):
                return
            await _after_location_click(page)
            return
        log.warning("All methods failed to find KY-2065 element")
    except Exception as exc:
        log.warning(f"JS click failed: {exc}")

    # Last resort: Sign In without any selection (location may already be set)
    log.info("Last resort: clicking Sign In without explicit selection")
    if await _click_sign_in(page):
        return

    log.info("Location picker not found — proceeding anyway")
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
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(2_000)
            if "ChooseLocation" not in page.url:
                log.info("Enter key navigated away from ChooseLocation")
        except Exception:
            pass
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

    # Scroll main page
    await page.evaluate("window.scrollBy(0, 800)")
    await page.wait_for_timeout(1_500)
    await page.screenshot(path=str(DATA_DIR / "05_dashboard_mid.png"))

    await page.evaluate("window.scrollBy(0, 800)")
    await page.wait_for_timeout(1_500)
    await page.screenshot(path=str(DATA_DIR / "06_dashboard_bottom.png"))

    # Scroll INSIDE the Performance Metrics section — it has its own scrollbar
    # that must be scrolled to reveal Actual Hours, Discounts, Cash O/S, etc.
    scroll_result = await page.evaluate("""
        (() => {
            const scrolled = [];
            document.querySelectorAll('*').forEach(el => {
                if (el.scrollHeight > el.clientHeight + 10) {
                    const style = window.getComputedStyle(el);
                    if (style.overflow === 'auto' || style.overflow === 'scroll' ||
                        style.overflowY === 'auto' || style.overflowY === 'scroll') {
                        el.scrollTop = 9999;
                        scrolled.push(el.className.substring(0, 60));
                    }
                }
            });
            return scrolled.length ? 'scrolled: ' + scrolled.join(', ') : 'none found';
        })()
    """)
    log.info(f"Internal section scroll: {scroll_result}")
    await page.wait_for_timeout(1_500)
    await page.screenshot(path=str(DATA_DIR / "06b_after_section_scroll.png"))

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
            if "week-t" in h.lower() or "wtd" in h.lower():
                week_col = i

        # CrunchTime week always runs Mon–Sun; col 0 = label, cols 1–7 = Mon–Sun.
        # yest.weekday(): Mon=0 … Sun=6, so +1 gives the correct 1-based column.
        if day_col is None and len(headers) >= 2:
            day_col = yest.weekday() + 1
            log.info(f"  Table {tbl_idx}: date '{RPT_MMDDYYYY}' not in headers; "
                     f"using weekday col {day_col} ({yest.strftime('%A')})")
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

    # CrunchTime week runs Mon–Sun; col 0 = label, cols 1–7 = Mon–Sun.
    # Default to weekday-based index; override if we find the exact date in headers.
    day_col_idx  = yest.weekday() + 1   # Mon=1 … Sun=7
    week_col_idx = -1
    log.info(f"ExtJS default day column: {day_col_idx} ({yest.strftime('%A')})")

    hdr_texts = []
    for hsel in [".x-column-header-text", ".x-column-header"]:
        hdrs = await page.locator(hsel).all()
        if hdrs:
            hdr_texts = [(await h.inner_text()).strip() for h in hdrs]
            log.info(f"Column headers: {hdr_texts}")
            for i, h in enumerate(hdr_texts):
                if RPT_MMDDYYYY in h:
                    day_col_idx = i
                if "week-t" in h.lower() or "wtd" in h.lower():
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
        "Actual to Earned",
    ]

    VALUE_RE = re.compile(r'[\(\$]?[\d,]+\.?\d*\s*%?')

    # CrunchTime table: col 0 = label, cols 1–7 = Mon–Sun, col 8 = Week-to-date.
    # yest.weekday() gives 0=Mon … 6=Sun, so it's the 0-based index into data cols.
    yest_col = yest.weekday()   # 0=Mon … 6=Sun
    log.info(f"Text strategy: yesterday = {yest.strftime('%A')}, data col index {yest_col}")

    metrics: dict[str, dict] = {}

    for i, line in enumerate(lines):
        matched_label = None
        for lbl in KNOWN_LABELS:
            if lbl.lower() in line.lower():
                matched_label = lbl
                break
        if not matched_label:
            continue

        # Collect this line + up to 12 following lines (one value per line pattern)
        # Stop only when the next KNOWN label appears.
        candidate_lines = [line]
        for j in range(i + 1, min(i + 15, len(lines))):
            if any(lbl.lower() in lines[j].lower() for lbl in KNOWN_LABELS):
                break
            candidate_lines.append(lines[j])

        combined = " ".join(candidate_lines)
        values   = VALUE_RE.findall(combined)
        values   = [v.strip() for v in values if v.strip() and len(v.strip()) > 1]

        # Pick yesterday's column; fall back to first value if index out of range
        if yest_col < len(values):
            day_val = values[yest_col]
        else:
            day_val = values[0] if values else ""

        # Week-to-date is typically second-to-last value (after all 7 day columns)
        week_val = values[-2] if len(values) >= 2 else (values[-1] if values else "")

        metrics[matched_label] = {"day": day_val, "week": week_val}
        log.info(f"  Text-parsed {matched_label!r}: day={day_val!r} week={week_val!r} "
                 f"(col {yest_col} of {len(values)} values)")

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
    meta  = d.get("meta", {})
    s     = d.get("sales", {})
    lab   = d.get("labor", {})
    cash  = d.get("cash", {})
    comps = d.get("comps", [])

    rpt_display = meta.get("report_display", RPT_DISPLAY)
    generated   = meta.get("generated",      GEN_DISPLAY)

    vs_ly   = s.get("vs_ly")      or 0.0
    vs_ly_w = s.get("vs_ly_week") or 0.0
    vs_fc   = s.get("vs_forecast") or 0.0
    cos     = cash.get("over_short", 0.0) or 0.0
    lp      = lab.get("pct") or 0.0

    def pn(v):
        return "pos" if (v or 0) >= 0 else "neg"

    def cos_hint():
        return "Balanced" if cos == 0 else ("Over" if cos > 0 else "Short")

    def lp_hint():
        return "On target" if lp < 25 else ("Watch" if lp < 30 else "Over target")

    comps_rows = ""
    for c in comps:
        comps_rows += f"""
          <tr>
            <td>{c['name']}</td>
            <td>{c['day']}</td>
            <td>{c['week']}</td>
          </tr>"""
    if not comps_rows:
        comps_rows = '<tr><td colspan="3">No comps data found</td></tr>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Five Guys KY-2065 | Operations Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Inter', system-ui, sans-serif; background: #d52b1e; min-height: 100vh; color: white; }}
  .topbar {{ background: #0c0c0c; padding: 0 32px; display: flex; justify-content: space-between; align-items: stretch; border-bottom: 1px solid #1c1c1c; position: sticky; top: 0; z-index: 50; }}
  .topbar-brand {{ display: flex; align-items: center; gap: 10px; padding: 11px 0; flex-shrink: 0; margin-right: 28px; }}
  .brand-pip {{ width: 3px; height: 28px; background: #d52b1e; border-radius: 2px; }}
  .brand-name {{ font-size: 0.82em; font-weight: 700; color: #efefef; }}
  .brand-sub {{ font-size: 0.58em; color: #3a3a3a; margin-top: 1px; text-transform: uppercase; letter-spacing: 0.8px; }}
  .topbar-nav {{ display: flex; align-items: stretch; flex: 1; }}
  .nav-tab {{ padding: 0 16px; display: flex; align-items: center; gap: 6px; font-size: 0.7em; font-weight: 500; color: #454545; cursor: pointer; border: none; border-bottom: 2px solid transparent; background: none; font-family: inherit; letter-spacing: 0.2px; transition: color 0.12s; white-space: nowrap; }}
  .nav-tab:hover {{ color: #888; }}
  .nav-tab.active {{ color: #fff; border-bottom-color: #d52b1e; }}
  .nav-dropdown {{ position: relative; display: flex; align-items: stretch; }}
  .dropdown-menu {{ display: none; position: absolute; top: calc(100% + 1px); left: 0; background: #111; border: 1px solid #222; border-radius: 7px; min-width: 170px; z-index: 200; box-shadow: 0 8px 24px rgba(0,0,0,0.5); overflow: hidden; }}
  .nav-dropdown:hover .dropdown-menu {{ display: block; }}
  .dropdown-item {{ display: flex; justify-content: space-between; align-items: center; padding: 9px 14px; font-size: 0.7em; color: #3a3a3a; border-bottom: 1px solid #1a1a1a; cursor: default; }}
  .dropdown-item:last-child {{ border-bottom: none; }}
  .dropdown-item .soon {{ font-size: 0.85em; color: #262626; }}
  .topbar-right {{ display: flex; align-items: center; padding-left: 20px; border-left: 1px solid #1c1c1c; margin-left: 8px; text-align: right; }}
  .date-main {{ font-size: 0.72em; font-weight: 600; color: #777; }}
  .date-gen  {{ font-size: 0.58em; color: #2e2e2e; margin-top: 1px; }}
  .sites-bar {{ background: #0c0c0c; border-bottom: 1px solid #1a1a1a; padding: 7px 32px; display: flex; align-items: center; gap: 5px; flex-wrap: wrap; }}
  .site-btn {{ display: flex; align-items: center; gap: 5px; padding: 5px 12px; border-radius: 5px; border: 1px solid #2a2a2a; background: #141414; color: #555; font-size: 0.65em; font-weight: 500; font-family: inherit; white-space: nowrap; cursor: pointer; transition: border-color 0.12s, color 0.12s, background 0.12s; }}
  .site-btn:hover {{ border-color: #3a3a3a; color: #999; background: #1a1a1a; }}
  .site-btn.active {{ border-color: #d52b1e; color: #fff; background: #1a0a09; }}
  .site-btn i {{ font-size: 0.9em; }}
  #site-viewer {{ display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; z-index: 40; background: #000; flex-direction: column; }}
  #site-viewer.open {{ display: flex; }}
  .site-viewer-bar {{ background: #0c0c0c; border-bottom: 1px solid #1a1a1a; padding: 8px 16px; display: flex; align-items: center; gap: 10px; flex-shrink: 0; }}
  .site-viewer-bar .site-title {{ font-size: 0.72em; font-weight: 600; color: #777; }}
  .site-viewer-bar .site-url {{ font-size: 0.6em; color: #333; margin-left: 4px; }}
  #site-frame {{ flex: 1; border: none; width: 100%; background: #fff; }}
  .back-btn-viewer {{ display: flex; align-items: center; gap: 6px; padding: 5px 12px; border-radius: 5px; border: 1px solid #2a2a2a; background: #141414; color: #d52b1e; font-size: 0.65em; font-weight: 600; font-family: inherit; cursor: pointer; margin-right: 8px; }}
  .back-btn-viewer:hover {{ background: #1e0808; border-color: #d52b1e; }}
  .kpi-bar {{ background: rgba(0,0,0,0.22); border-bottom: 1px solid rgba(0,0,0,0.18); padding: 0 32px; display: flex; overflow-x: auto; }}
  .kpi-item {{ padding: 8px 22px 8px 0; margin-right: 22px; border-right: 1px solid rgba(255,255,255,0.08); flex-shrink: 0; }}
  .kpi-item:last-child {{ border-right: none; margin-right: 0; padding-right: 0; }}
  .kpi-lbl {{ font-size: 0.5em; letter-spacing: 0.9px; text-transform: uppercase; color: rgba(255,255,255,0.32); margin-bottom: 2px; font-weight: 500; }}
  .kpi-val {{ font-size: 0.86em; font-weight: 700; color: rgba(255,255,255,0.88); letter-spacing: -0.3px; }}
  .kpi-val.pos {{ color: #4ade80; }}
  .kpi-val.neg {{ color: #fca5a5; }}
  .page {{ display: none; }}
  .page.active {{ display: block; }}
  .inner {{ max-width: 980px; margin: 0 auto; padding: 20px 32px 32px; }}
  .section {{ margin-bottom: 16px; }}
  .sec-hdr {{ display: flex; align-items: center; gap: 10px; margin-bottom: 9px; padding-bottom: 9px; border-bottom: 1px solid rgba(255,255,255,0.12); }}
  .sec-icon {{ width: 28px; height: 28px; background: rgba(0,0,0,0.25); border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 0.72em; color: rgba(255,255,255,0.75); flex-shrink: 0; }}
  .sec-title {{ font-size: 0.92em; font-weight: 700; color: #ffffff; }}
  .grid {{ display: grid; gap: 5px; }}
  .g3 {{ grid-template-columns: repeat(3, 1fr); }}
  .g4 {{ grid-template-columns: repeat(4, 1fr); }}
  .card {{ background: #090909; border-radius: 6px; padding: 9px 12px 10px; border: 1px solid rgba(255,255,255,0.03); position: relative; overflow: hidden; }}
  .card::before {{ content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; }}
  .c-amber::before {{ background: #d97706; }}
  .c-teal::before  {{ background: #0891b2; }}
  .c-indigo::before {{ background: #4338ca; }}
  .c-green::before {{ background: #15803d; }}
  .c-rose::before  {{ background: #be123c; }}
  .c-sky::before   {{ background: #0369a1; }}
  .lbl {{ font-size: 0.52em; font-weight: 500; letter-spacing: 0.7px; text-transform: uppercase; color: rgba(255,255,255,0.3); margin-bottom: 5px; }}
  .val {{ font-size: 1.08em; font-weight: 700; color: #fff; letter-spacing: -0.5px; line-height: 1; }}
  .val.pos {{ color: #4ade80; }}
  .val.neg {{ color: #fca5a5; }}
  .hint {{ font-size: 0.52em; color: rgba(255,255,255,0.15); margin-top: 2px; }}
  .wtd {{ font-size: 0.55em; margin-top: 7px; padding-top: 6px; border-top: 1px solid rgba(255,255,255,0.05); display: flex; justify-content: space-between; }}
  .wk {{ color: rgba(255,255,255,0.16); font-weight: 600; }}
  .wv {{ color: rgba(255,255,255,0.42); }}
  .wv.pos {{ color: #4ade80; }}
  .wv.neg {{ color: #fca5a5; }}
  .tbl {{ width: 100%; border-collapse: collapse; background: #090909; border-radius: 6px; overflow: hidden; border: 1px solid rgba(255,255,255,0.03); }}
  .tbl th {{ padding: 7px 13px; font-size: 0.52em; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: rgba(255,255,255,0.22); text-align: left; border-bottom: 1px solid rgba(255,255,255,0.04); background: rgba(255,255,255,0.015); }}
  .tbl th:not(:first-child) {{ text-align: right; }}
  .tbl td {{ padding: 8px 13px; border-bottom: 1px solid rgba(255,255,255,0.03); font-size: 0.75em; color: rgba(255,255,255,0.38); }}
  .tbl td:not(:first-child) {{ text-align: right; color: rgba(255,255,255,0.68); font-weight: 500; }}
  .tbl tr:last-child td {{ border-bottom: none; }}
  .tbl tr:hover td {{ background: rgba(255,255,255,0.015); }}
  .links-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 5px; }}
  .link-card {{ background: #090909; border-radius: 6px; padding: 12px 14px; border: 1px solid rgba(255,255,255,0.04); display: flex; align-items: center; gap: 11px; text-decoration: none; transition: background 0.12s; }}
  .link-card:hover {{ background: #111; }}
  .link-icon {{ width: 30px; height: 30px; border-radius: 6px; background: rgba(255,255,255,0.04); display: flex; align-items: center; justify-content: center; font-size: 0.8em; color: rgba(255,255,255,0.5); flex-shrink: 0; }}
  .link-name {{ font-size: 0.76em; font-weight: 600; color: rgba(255,255,255,0.8); margin-bottom: 2px; }}
  .link-desc {{ font-size: 0.6em; color: rgba(255,255,255,0.22); }}
  footer {{ text-align: center; padding: 12px; color: rgba(255,255,255,0.15); font-size: 0.56em; letter-spacing: 0.3px; }}
  @media (max-width: 860px) {{
    .g4 {{ grid-template-columns: repeat(2, 1fr); }}
    .g3 {{ grid-template-columns: repeat(2, 1fr); }}
    .links-grid {{ grid-template-columns: repeat(2, 1fr); }}
    .inner {{ padding: 14px 16px 24px; }}
    .topbar, .kpi-bar, .sites-bar {{ padding-left: 16px; padding-right: 16px; }}
  }}
  @media (max-width: 540px) {{
    .g4, .g3 {{ grid-template-columns: 1fr 1fr; }}
    .links-grid {{ grid-template-columns: 1fr 1fr; }}
    .brand-sub {{ display: none; }}
  }}
</style>
</head>
<body>

<nav class="topbar">
  <div class="topbar-brand">
    <div class="brand-pip"></div>
    <div>
      <div class="brand-name">Five Guys &mdash; KY-2065 Dixie Highway</div>
      <div class="brand-sub">Operations Dashboard</div>
    </div>
  </div>
  <div class="topbar-nav">
    <button class="nav-tab active" onclick="showTab('dashboard',this)">
      <i class="fa-solid fa-chart-simple"></i> Dashboard
    </button>
    <button class="nav-tab" onclick="showTab('links',this)">
      <i class="fa-solid fa-link"></i> Quick Links
    </button>
    <div class="nav-dropdown">
      <button class="nav-tab">More <i class="fa-solid fa-chevron-down" style="font-size:0.75em"></i></button>
      <div class="dropdown-menu">
        <div class="dropdown-item">Weekly Summary <span class="soon">coming soon</span></div>
        <div class="dropdown-item">Labor Schedule <span class="soon">coming soon</span></div>
        <div class="dropdown-item">Food Cost <span class="soon">coming soon</span></div>
        <div class="dropdown-item">Inventory <span class="soon">coming soon</span></div>
      </div>
    </div>
  </div>
  <div class="topbar-right">
    <div>
      <div class="date-main">{rpt_display}</div>
      <div class="date-gen">Generated {generated}</div>
    </div>
  </div>
</nav>

<div class="sites-bar">
  <button class="site-btn" onclick="openSite('https://fiveguysfr77.net-chef.com','Net Chef','fiveguysfr77.net-chef.com',this)">
    <i class="fa-solid fa-chart-bar"></i> Net Chef
  </button>
  <button class="site-btn" onclick="openSite('https://fiveguysfr113-em.net-chef.com','Schedules','fiveguysfr113-em.net-chef.com',this)">
    <i class="fa-solid fa-calendar-days"></i> Schedules
  </button>
  <button class="site-btn" onclick="openSite('https://fiveguysfr77.ct-teamworx.com','TeamWorx','fiveguysfr77.ct-teamworx.com',this)">
    <i class="fa-solid fa-users-clock"></i> TeamWorx
  </button>
  <button class="site-btn" onclick="openSite('https://admin5.parpos.com','Brinks','admin5.parpos.com',this)">
    <i class="fa-solid fa-vault"></i> Brinks
  </button>
  <button class="site-btn" onclick="openSite('https://bread2.fiveguys.com','Bread Ordering','bread2.fiveguys.com',this)">
    <i class="fa-solid fa-bread-slice"></i> Bread Order
  </button>
  <button class="site-btn" onclick="openSite('https://knowledgeforce.com','Secret Shops','knowledgeforce.com',this)">
    <i class="fa-solid fa-user-secret"></i> Secret Shops
  </button>
  <button class="site-btn" onclick="openSite('https://fg-beta.compliancemate.com','Temps &amp; Times','fg-beta.compliancemate.com',this)">
    <i class="fa-solid fa-temperature-half"></i> Temps &amp; Times
  </button>
</div>

<div id="site-viewer">
  <div class="site-viewer-bar">
    <button class="back-btn-viewer" onclick="closeSite()">
      <i class="fa-solid fa-arrow-left"></i> Dashboard
    </button>
    <span class="site-title" id="viewer-title"></span>
    <span class="site-url" id="viewer-url"></span>
  </div>
  <iframe id="site-frame" src=""></iframe>
</div>

<div class="kpi-bar">
  <div class="kpi-item">
    <div class="kpi-lbl">Net Sales</div>
    <div class="kpi-val">{fmt_dollar(s.get('net'))}</div>
  </div>
  <div class="kpi-item">
    <div class="kpi-lbl">vs Last Year</div>
    <div class="kpi-val {pn(vs_ly)}">{fmt_dollar(vs_ly)}</div>
  </div>
  <div class="kpi-item">
    <div class="kpi-lbl">vs Forecast</div>
    <div class="kpi-val {pn(vs_fc)}">{fmt_dollar(vs_fc)}</div>
  </div>
  <div class="kpi-item">
    <div class="kpi-lbl">Labor %</div>
    <div class="kpi-val">{fmt_pct(lp)}</div>
  </div>
  <div class="kpi-item">
    <div class="kpi-lbl">Cash Over/Short</div>
    <div class="kpi-val {pn(cos)}">{fmt_dollar(cos)}</div>
  </div>
</div>

<div class="page active" id="tab-dashboard">
  <div class="inner">

    <div class="section">
      <div class="sec-hdr">
        <div class="sec-icon"><i class="fa-solid fa-chart-line"></i></div>
        <div class="sec-title">Sales Overview</div>
      </div>
      <div class="grid g3">
        <div class="card c-amber">
          <div class="lbl">Actual Net Sales</div>
          <div class="val">{fmt_dollar(s.get('net'))}</div>
          <div class="hint">Yesterday</div>
          <div class="wtd"><span class="wk">WTD</span><span class="wv">{fmt_dollar(s.get('net_week'))}</span></div>
        </div>
        <div class="card c-teal">
          <div class="lbl">Last Year Same Day</div>
          <div class="val">{fmt_dollar(s.get('ly'))}</div>
          <div class="hint">Prior year</div>
          <div class="wtd"><span class="wk">WTD LY</span><span class="wv">{fmt_dollar(s.get('ly_week'))}</span></div>
        </div>
        <div class="card c-indigo">
          <div class="lbl">Forecasted Sales</div>
          <div class="val">{fmt_dollar(s.get('forecast'))}</div>
          <div class="hint">Projected</div>
          <div class="wtd"><span class="wk">WTD</span><span class="wv">{fmt_dollar(s.get('forecast_week'))}</span></div>
        </div>
      </div>
    </div>

    <div class="section">
      <div class="sec-hdr">
        <div class="sec-icon"><i class="fa-solid fa-bullseye"></i></div>
        <div class="sec-title">Performance Metrics</div>
      </div>
      <div class="grid g3">
        <div class="card {'c-green' if vs_ly >= 0 else 'c-rose'}">
          <div class="lbl">vs Last Year</div>
          <div class="val {pn(vs_ly)}">{fmt_dollar(vs_ly)}{trend_arrow(vs_ly)}</div>
          <div class="hint">Net Sales vs Same Day LY</div>
          <div class="wtd"><span class="wk">WTD vs LY</span><span class="wv {pn(vs_ly_w)}">{fmt_dollar(vs_ly_w)}</span></div>
        </div>
        <div class="card {'c-green' if vs_fc >= 0 else 'c-rose'}">
          <div class="lbl">vs Forecast</div>
          <div class="val {pn(vs_fc)}">{fmt_dollar(vs_fc)}{trend_arrow(vs_fc)}</div>
          <div class="hint">Actual vs Projected</div>
          <div class="wtd">&nbsp;</div>
        </div>
        <div class="card {'c-green' if cos == 0 else 'c-rose'}">
          <div class="lbl">Cash Over / Short</div>
          <div class="val {pn(cos)}">{fmt_dollar(cos)}</div>
          <div class="hint">{cos_hint()}</div>
          <div class="wtd">&nbsp;</div>
        </div>
      </div>
    </div>

    <div class="section">
      <div class="sec-hdr">
        <div class="sec-icon"><i class="fa-solid fa-users-clock"></i></div>
        <div class="sec-title">Labor Summary</div>
      </div>
      <div class="grid g4">
        <div class="card c-rose">
          <div class="lbl">Labor Cost</div>
          <div class="val">{fmt_dollar(lab.get('cost'))}</div>
          <div class="hint">Total wages</div>
          <div class="wtd"><span class="wk">WTD</span><span class="wv">{fmt_dollar(lab.get('cost_week'))}</span></div>
        </div>
        <div class="card {'c-green' if lp < 25 else 'c-rose'}">
          <div class="lbl">Labor %</div>
          <div class="val {'pos' if lp < 25 else 'neg'}">{fmt_pct(lp)}</div>
          <div class="hint">{lp_hint()}</div>
          <div class="wtd"><span class="wk">WTD</span><span class="wv">{fmt_pct(lab.get('pct_week'))}</span></div>
        </div>
        <div class="card c-sky">
          <div class="lbl">Scheduled Hours</div>
          <div class="val">{fmt_num(lab.get('sched_hours'))}</div>
          <div class="hint">On schedule</div>
          <div class="wtd"><span class="wk">WTD</span><span class="wv">{fmt_num(lab.get('sched_hours_week'))}</span></div>
        </div>
        <div class="card c-sky">
          <div class="lbl">Actual Hours</div>
          <div class="val">{fmt_num(lab.get('actual_hours'))}</div>
          <div class="hint">Worked</div>
          <div class="wtd"><span class="wk">WTD</span><span class="wv">{fmt_num(lab.get('actual_hours_week'))}</span></div>
        </div>
      </div>
    </div>

    <div class="section">
      <div class="sec-hdr">
        <div class="sec-icon"><i class="fa-solid fa-tag"></i></div>
        <div class="sec-title">Comps &amp; Discounts</div>
      </div>
      <table class="tbl">
        <thead>
          <tr><th>Type</th><th>Yesterday</th><th>Week-to-Date</th></tr>
        </thead>
        <tbody>{comps_rows}</tbody>
      </table>
    </div>

  </div>
</div>

<div class="page" id="tab-links">
  <div class="inner">
    <div class="section">
      <div class="sec-hdr">
        <div class="sec-icon"><i class="fa-solid fa-link"></i></div>
        <div class="sec-title">Quick Links</div>
      </div>
      <div class="links-grid">
        <a class="link-card" href="https://fiveguysfr77.net-chef.com" target="_blank" rel="noopener">
          <div class="link-icon"><i class="fa-solid fa-chart-bar"></i></div>
          <div><div class="link-name">CrunchTime Net Chef</div><div class="link-desc">fiveguysfr77.net-chef.com</div></div>
        </a>
        <a class="link-card" href="https://fiveguysfr113-em.net-chef.com" target="_blank" rel="noopener">
          <div class="link-icon"><i class="fa-solid fa-calendar-days"></i></div>
          <div><div class="link-name">Schedules</div><div class="link-desc">fiveguysfr113-em.net-chef.com</div></div>
        </a>
        <a class="link-card" href="https://fiveguysfr77.ct-teamworx.com" target="_blank" rel="noopener">
          <div class="link-icon"><i class="fa-solid fa-users-clock"></i></div>
          <div><div class="link-name">TeamWorx</div><div class="link-desc">fiveguysfr77.ct-teamworx.com</div></div>
        </a>
        <a class="link-card" href="https://admin5.parpos.com" target="_blank" rel="noopener">
          <div class="link-icon"><i class="fa-solid fa-vault"></i></div>
          <div><div class="link-name">Brinks</div><div class="link-desc">admin5.parpos.com</div></div>
        </a>
        <a class="link-card" href="https://bread2.fiveguys.com" target="_blank" rel="noopener">
          <div class="link-icon"><i class="fa-solid fa-bread-slice"></i></div>
          <div><div class="link-name">Bread Ordering</div><div class="link-desc">bread2.fiveguys.com</div></div>
        </a>
        <a class="link-card" href="https://knowledgeforce.com" target="_blank" rel="noopener">
          <div class="link-icon"><i class="fa-solid fa-user-secret"></i></div>
          <div><div class="link-name">Secret Shops</div><div class="link-desc">knowledgeforce.com</div></div>
        </a>
        <a class="link-card" href="https://fg-beta.compliancemate.com" target="_blank" rel="noopener">
          <div class="link-icon"><i class="fa-solid fa-temperature-half"></i></div>
          <div><div class="link-name">Temps &amp; Times</div><div class="link-desc">fg-beta.compliancemate.com</div></div>
        </a>
      </div>
    </div>
  </div>
</div>

<footer>
  Five Guys KY-2065 Dixie Highway &bull; CrunchTime Net Chef &bull;
  Business Date: {rpt_display} &bull; Generated: {generated}
</footer>

<script>
  function showTab(name, btn) {{
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    document.getElementById('tab-' + name).classList.add('active');
    btn.classList.add('active');
  }}
  function openSite(url, title, label, btn) {{
    document.querySelectorAll('.site-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('viewer-title').textContent = title;
    document.getElementById('viewer-url').textContent = label;
    document.getElementById('site-frame').src = url;
    document.getElementById('site-viewer').classList.add('open');
  }}
  function closeSite() {{
    document.getElementById('site-viewer').classList.remove('open');
    document.getElementById('site-frame').src = '';
    document.querySelectorAll('.site-btn').forEach(b => b.classList.remove('active'));
  }}
</script>

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
