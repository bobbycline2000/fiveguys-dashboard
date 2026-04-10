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

    # Find username field
    for sel in [
        'input[name*="user" i]', 'input[id*="user" i]',
        'input[name*="login" i]', 'input[id*="login" i]',
        'input[type="text"]',
    ]:
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

    # Submit
    for sel in [
        'button[type="submit"]', 'input[type="submit"]',
        'button:has-text("Log")', 'button:has-text("Sign")',
        '#btnLogin', '.btn-login',
    ]:
        if await page.locator(sel).count():
            await page.locator(sel).first.click()
            break
    else:
        await page.keyboard.press("Enter")

    try:
        await page.wait_for_load_state("networkidle", timeout=20_000)
    except PlaywrightTimeout:
        pass

    await page.screenshot(path=str(DATA_DIR / "02_after_login.png"))
    log.info(f"Post-login URL: {page.url}")

    if any(kw in page.url.lower() for kw in ["login", "signin", "logon"]):
        log.error("Still on login page — check credentials (see 02_after_login.png)")
        return False

    log.info("Login successful")
    return True


async def select_location(page):
    """
    CrunchTime asks you to pick a store after login.
    Always choose location 2065.
    """
    log.info("Checking for location selector…")

    # Give the page a moment to show the location picker
    await page.wait_for_timeout(2_000)

    location_id = "2065"

    # Try dropdown/select element first
    for sel in [
        f'option[value="{location_id}"]',
        f'option:has-text("{location_id}")',
        f'li:has-text("{location_id}")',
        f'a:has-text("{location_id}")',
        f'[data-id="{location_id}"]',
    ]:
        loc = page.locator(sel)
        if await loc.count():
            # If it's an <option>, select its parent <select>
            tag = await loc.first.evaluate("el => el.tagName.toLowerCase()")
            if tag == "option":
                parent = loc.first.locator("xpath=..")
                await parent.select_option(value=location_id)
            else:
                await loc.first.click()
            log.info(f"Selected location {location_id} via {sel}")
            try:
                await page.wait_for_load_state("networkidle", timeout=10_000)
            except PlaywrightTimeout:
                pass
            await page.screenshot(path=str(DATA_DIR / "03_location_selected.png"))
            return

    # Try typing into a search/filter box
    for sel in ['input[placeholder*="store" i]', 'input[placeholder*="location" i]',
                'input[placeholder*="search" i]']:
        if await page.locator(sel).count():
            await page.fill(sel, location_id)
            await page.wait_for_timeout(500)
            # Click the matching result
            result = page.locator(f'li:has-text("{location_id}"), td:has-text("{location_id}")')
            if await result.count():
                await result.first.click()
                log.info(f"Typed and selected location {location_id}")
                try:
                    await page.wait_for_load_state("networkidle", timeout=10_000)
                except PlaywrightTimeout:
                    pass
                return

    log.info("No location picker found — already on correct location or auto-selected")


async def extract_performance_metrics(page) -> dict:
    """
    Parse the Performance Metrics table.
    The table is long — scroll down in steps to ensure all rows are rendered
    before extracting.  Screenshots are saved at each scroll position.
    """
    log.info("Waiting for Performance Metrics table…")

    try:
        await page.wait_for_selector("table", timeout=15_000)
    except PlaywrightTimeout:
        log.warning("No table found within 15s")

    # ── Scroll down in steps to trigger any lazy-loaded rows ──────────────
    await page.screenshot(path=str(DATA_DIR / "04_dashboard_top.png"))
    log.info("Screenshot: top of dashboard")

    await page.evaluate("window.scrollBy(0, 800)")
    await page.wait_for_timeout(1_000)
    await page.screenshot(path=str(DATA_DIR / "05_dashboard_mid.png"))
    log.info("Screenshot: middle of dashboard (scroll 1)")

    await page.evaluate("window.scrollBy(0, 800)")
    await page.wait_for_timeout(1_000)
    await page.screenshot(path=str(DATA_DIR / "06_dashboard_bottom.png"))
    log.info("Screenshot: bottom of dashboard (scroll 2)")

    # Scroll back to top so the full DOM is stable
    await page.evaluate("window.scrollTo(0, 0)")
    await page.wait_for_timeout(500)

    tables = await page.locator("table").all()
    log.info(f"Found {len(tables)} table(s) on page")

    metrics: dict[str, dict] = {}   # label → {day, week, period}

    for tbl_idx, tbl in enumerate(tables):
        rows = await tbl.locator("tr").all()
        if not rows:
            continue

        # ── Find header row and locate yesterday's column ──────────────────
        header_cells = await rows[0].locator("td, th").all()
        headers = [(await c.inner_text()).strip() for c in header_cells]
        log.info(f"Table {tbl_idx} headers: {headers}")

        day_col  = None
        week_col = None
        for i, h in enumerate(headers):
            if RPT_MMDDYYYY in h:
                day_col = i
            # Week-to-date is usually the second-to-last or contains "Week"
            if "week" in h.lower() or "wtd" in h.lower():
                week_col = i

        if day_col is None:
            log.info(f"Table {tbl_idx}: no column for {RPT_MMDDYYYY}, skipping")
            continue

        log.info(f"Table {tbl_idx}: day_col={day_col}, week_col={week_col}")

        # ── Extract each metric row ────────────────────────────────────────
        for row in rows[1:]:
            cells = await row.locator("td, th").all()
            if len(cells) <= day_col:
                continue
            label = (await cells[0].inner_text()).strip()
            day_val  = (await cells[day_col].inner_text()).strip() if day_col < len(cells) else ""
            week_val = (await cells[week_col].inner_text()).strip() if week_col and week_col < len(cells) else ""
            if label:
                metrics[label] = {"day": day_val, "week": week_val}
                log.info(f"  {label!r:40s} day={day_val!r:15s} week={week_val!r}")

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
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        ctx = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
        )
        page = await ctx.new_page()

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
