#!/usr/bin/env python3
"""
Five Guys KY-2065 — Daily Dashboard Automation
Scrapes CrunchTime Net Chef (fiveguysfr77.net-chef.com) and
regenerates dashboard.html which Netlify auto-deploys.

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
LOCATION_ID  = "2065"
USERNAME     = os.environ.get("CRUNCHTIME_USERNAME", "")
PASSWORD     = os.environ.get("CRUNCHTIME_PASSWORD", "")

ROOT     = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# Eastern time (UTC-4 summer / UTC-5 winter — adjust as needed)
ET     = timezone(timedelta(hours=-4))
now_et = datetime.now(tz=ET)
yest   = now_et - timedelta(days=1)

RPT_DATE    = yest.strftime("%Y-%m-%d")            # 2026-04-06
RPT_MMDDYY  = yest.strftime("%m/%d/%Y")            # 04/06/2026
RPT_DISPLAY = yest.strftime("%A, %B %-d, %Y")      # Monday, April 6, 2026
GEN_DISPLAY = now_et.strftime("%-m/%-d/%Y at %-I:%M %p")  # 4/7/2026 at 8:01 AM

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


# ─── Parsing helpers ──────────────────────────────────────────────────────────
def parse_amount(text: str) -> float | None:
    if not text:
        return None
    cleaned = re.sub(r"[^\d.]", "", text.replace(",", ""))
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def parse_pct(text: str) -> float | None:
    if not text:
        return None
    m = re.search(r"([\d.]+)\s*%", text)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


def fmt_dollar(v: float | None) -> str:
    return f"${v:,.2f}" if v is not None else "—"


def fmt_pct(v: float | None, decimals: int = 2) -> str:
    return f"{v:.{decimals}f}%" if v is not None else "—"


def fmt_num(v: float | None, decimals: int = 0) -> str:
    if v is None:
        return "—"
    return f"{v:,.{decimals}f}"


# ─── Scraper ──────────────────────────────────────────────────────────────────
async def do_login(page) -> bool:
    log.info("Loading login page…")
    try:
        await page.goto(NETCHEF_BASE, wait_until="domcontentloaded", timeout=30_000)
    except Exception as e:
        log.error(f"Login page failed to load: {e}")
        return False

    await page.screenshot(path=str(DATA_DIR / "01_login.png"))
    log.info(f"Login URL: {page.url}")

    # Username
    username_sel = None
    for sel in [
        'input[name*="user" i]', 'input[id*="user" i]',
        'input[name*="login" i]', 'input[id*="login" i]',
        'input[type="text"]:first-of-type',
    ]:
        if await page.locator(sel).count():
            username_sel = sel
            break
    if not username_sel:
        log.error("Cannot find username field — see 01_login.png")
        return False
    await page.fill(username_sel, USERNAME)

    # Password
    for sel in ['input[type="password"]', 'input[name*="pass" i]', 'input[id*="pass" i]']:
        if await page.locator(sel).count():
            await page.fill(sel, PASSWORD)
            break
    else:
        log.error("Cannot find password field")
        return False

    # Submit
    submitted = False
    for sel in [
        'button[type="submit"]', 'input[type="submit"]',
        'button:has-text("Log")', 'button:has-text("Sign")',
        '#btnLogin', '.btn-login', 'a:has-text("Login")',
    ]:
        if await page.locator(sel).count():
            await page.locator(sel).first.click()
            submitted = True
            break
    if not submitted:
        await page.keyboard.press("Enter")

    try:
        await page.wait_for_load_state("networkidle", timeout=20_000)
    except PlaywrightTimeout:
        pass

    await page.screenshot(path=str(DATA_DIR / "02_after_login.png"))
    log.info(f"Post-login URL: {page.url}")

    # Detect failed login
    if any(kw in page.url.lower() for kw in ["login", "signin", "logon"]):
        err = await page.locator('[class*="error" i], [class*="alert" i]').first.inner_text() \
              if await page.locator('[class*="error" i], [class*="alert" i]').count() else "unknown"
        log.error(f"Still on login page after submit. Error: {err}")
        return False

    log.info("Login successful")
    return True


async def navigate_to_daily_report(page) -> bool:
    """Navigate to the daily summary / manager report for location 2065."""
    log.info("Navigating to daily report…")

    # Try clicking nav links first (most reliable)
    nav_candidates = [
        "Daily Summary", "Daily Report", "Manager Report",
        "Daily Manager", "Sales Report", "Reports",
    ]
    for text in nav_candidates:
        loc = page.locator(f'a:has-text("{text}"), button:has-text("{text}"), li:has-text("{text}") a')
        if await loc.count():
            await loc.first.click()
            try:
                await page.wait_for_load_state("networkidle", timeout=12_000)
            except PlaywrightTimeout:
                pass
            log.info(f"Clicked nav: '{text}'")
            await page.screenshot(path=str(DATA_DIR / "03_report_nav.png"))
            break

    # Try common URL patterns
    url_patterns = [
        f"{NETCHEF_BASE}/NCInterface/asp/NCCalls.asp?page=DailySummary",
        f"{NETCHEF_BASE}/NCInterface/Reports/DailySummary",
        f"{NETCHEF_BASE}/reports/daily-summary",
        f"{NETCHEF_BASE}/reports/daily",
        f"{NETCHEF_BASE}/daily",
    ]
    for url in url_patterns:
        try:
            resp = await page.goto(url, wait_until="domcontentloaded", timeout=10_000)
            if resp and resp.status < 400:
                log.info(f"Loaded report via direct URL: {url}")
                await page.screenshot(path=str(DATA_DIR / "03_report_direct.png"))
                return True
        except Exception:
            continue

    await page.screenshot(path=str(DATA_DIR / "03_current_page.png"))
    log.info("Will attempt data extraction from current page")
    return True


async def set_filters(page):
    """Set location=2065 and date=yesterday if controls exist."""
    # Location dropdown
    for val in [LOCATION_ID, f"KY-{LOCATION_ID}", f"KY{LOCATION_ID}", "2065"]:
        for sel in [
            f'select option[value="{val}"]',
            f'select option:has-text("{val}")',
        ]:
            opt = page.locator(sel)
            if await opt.count():
                parent_select = opt.locator("xpath=..")
                try:
                    await parent_select.select_option(value=val)
                    log.info(f"Set location to {val}")
                except Exception:
                    try:
                        await parent_select.select_option(label=val)
                    except Exception:
                        pass
                break

    # Date input
    for sel in ['input[type="date"]', 'input[name*="date" i]', 'input[id*="date" i]']:
        loc = page.locator(sel)
        if await loc.count():
            await loc.first.fill(RPT_DATE)
            log.info(f"Set date to {RPT_DATE}")
            break

    # Text date input (MM/DD/YYYY format)
    for sel in ['input[name*="bdate" i]', 'input[name*="busdate" i]', 'input[name*="startdate" i]']:
        loc = page.locator(sel)
        if await loc.count():
            await loc.first.fill(RPT_MMDDYY)
            log.info(f"Set text date to {RPT_MMDDYY}")
            break

    # Submit/refresh
    for sel in [
        'button:has-text("Go")', 'button:has-text("Run")',
        'button:has-text("Search")', 'button:has-text("Apply")',
        'button:has-text("Update")', 'input[type="submit"]',
    ]:
        if await page.locator(sel).count():
            await page.locator(sel).first.click()
            try:
                await page.wait_for_load_state("networkidle", timeout=12_000)
            except PlaywrightTimeout:
                pass
            log.info(f"Refreshed with: {sel}")
            break

    await page.screenshot(path=str(DATA_DIR / "04_filtered.png"))


async def extract_data(page) -> dict:
    """Extract all operational data from the page."""
    body_text = await page.inner_text("body")
    log.info(f"Page body text: {len(body_text)} characters")

    # Build key→value map from all table rows
    kv: dict[str, str] = {}
    channel_rows: list[list[str]] = []
    payment_rows: list[list[str]] = []
    discount_rows: list[list[str]] = []

    tables = await page.locator("table").all()
    log.info(f"Tables found: {len(tables)}")

    for tbl in tables:
        rows = await tbl.locator("tr").all()
        for row in rows:
            cells = await row.locator("td, th").all()
            texts = [(await c.inner_text()).strip() for c in cells]
            texts = [t for t in texts if t]  # drop empties
            if not texts:
                continue

            label = texts[0].lower()

            # Key-value pair
            if len(texts) >= 2:
                kv[label] = texts[-1]

            # Categorise rows
            if any(ch in label for ch in [
                "in-store", "five guys", "doordash", "door dash",
                "ubereats", "uber eats", "grubhub", "grub hub",
                "online", "google", "third party", "delivery", "catering",
            ]):
                channel_rows.append(texts)

            if any(p in label for p in [
                "cash", "visa", "mastercard", "master card", "amex",
                "american express", "discover", "debit", "credit card",
                "gift card", "gift cert", "doordash", "ubereats", "grubhub",
            ]):
                payment_rows.append(texts)

            if any(d in label for d in [
                "discount", "promo", "coupon", "marketing", "employee",
                "comp", "void", "refund",
            ]):
                discount_rows.append(texts)

    # Helper: search kv map or fall back to regex on page text
    def find(keys: list[str]) -> str | None:
        for k in keys:
            for kv_key, kv_val in kv.items():
                if k.lower() in kv_key:
                    return kv_val
        # Regex fallback
        for k in keys:
            pattern = rf"(?i){re.escape(k)}[\s\S]{{0,120}}?(\$[\d,]+\.?\d*|\d[\d,]*\.?\d*\s*%)"
            m = re.search(pattern, body_text)
            if m:
                return m.group(1)
        return None

    # ── Sales ──────────────────────────────────────────────────────────────────
    gross      = find(["gross sales", "gross sale", "gross"])
    net        = find(["net sales", "net sale"])
    order_cnt  = find(["order count", "transaction count", "check count", "ticket count"])
    guest_cnt  = find(["guest count", "cover count", "guests"])
    order_avg  = find(["order average", "check average", "ticket average", "avg check"])
    discounts  = find(["total discount", "discount amount", "discounts"])
    refunds    = find(["refund", "void amount", "returns"])
    no_sale    = find(["no sale", "nosale"])

    # ── Labor ──────────────────────────────────────────────────────────────────
    labor_cost = find(["labor cost", "total labor cost", "labor $", "labor dollars"])
    labor_pct  = find(["labor %", "labor percent", "labor pct", "labor cost %"])
    labor_hrs  = find(["labor hours", "total hours", "hours worked"])
    splh       = find(["sales per labor", "splh", "sales/labor", "$/labor hour"])

    # ── Food Cost ──────────────────────────────────────────────────────────────
    fc_theo    = find(["theoretical", "theo %", "theoretical food", "theory"])
    fc_actual  = find(["actual food", "actual cost %", "food cost %", "actual %"])
    fc_var     = find(["variance %", "food variance", "over/under"])
    fc_dollars = find(["food cost $", "cost of goods", "cogs"])

    # ── Cash & Tax ─────────────────────────────────────────────────────────────
    cash_total  = find(["total cash", "cash collected", "cash sales"])
    deposits    = find(["bank deposit", "deposit amount", "deposits"])
    over_short  = find(["over/short", "cash over", "overshort", "cash variance"])
    tax_total   = find(["tax collected", "sales tax", "total tax"])

    # ── Assemble channels ──────────────────────────────────────────────────────
    channels = []
    channel_colors = {
        "in-store": "red", "five guys": "red",
        "doordash": "orange", "door dash": "orange",
        "ubereats": "green", "uber eats": "green",
        "grubhub": "purple", "grub hub": "purple",
        "online": "blue",
        "google": "teal",
    }
    for row in channel_rows:
        if len(row) < 2:
            continue
        label = row[0]
        amounts = [parse_amount(c) for c in row[1:] if parse_amount(c) is not None]
        pcts    = [parse_pct(c)    for c in row[1:] if parse_pct(c)    is not None]
        color_key = next((k for k in channel_colors if k in label.lower()), "blue")
        channels.append({
            "name":  label,
            "sales": amounts[0] if amounts else None,
            "pct":   pcts[0]    if pcts    else None,
            "color": channel_colors[color_key],
        })

    # ── Assemble payments ──────────────────────────────────────────────────────
    payments = []
    for row in payment_rows:
        if len(row) < 2:
            continue
        amounts = [parse_amount(c) for c in row[1:] if parse_amount(c) is not None]
        pcts    = [parse_pct(c)    for c in row[1:] if parse_pct(c)    is not None]
        if amounts:
            payments.append({
                "name":   row[0],
                "amount": amounts[0],
                "pct":    pcts[0] if pcts else None,
            })

    # ── Assemble discounts ─────────────────────────────────────────────────────
    discounts_detail = []
    for row in discount_rows:
        if len(row) < 2:
            continue
        amounts = [parse_amount(c) for c in row[1:] if parse_amount(c) is not None]
        pcts    = [parse_pct(c)    for c in row[1:] if parse_pct(c)    is not None]
        if amounts:
            discounts_detail.append({
                "name":   row[0],
                "amount": amounts[0],
                "pct":    pcts[0] if pcts else None,
            })

    data = {
        "meta": {
            "report_date":    RPT_DATE,
            "report_display": RPT_DISPLAY,
            "generated":      GEN_DISPLAY,
            "location":       LOCATION_ID,
        },
        "sales": {
            "gross":       parse_amount(gross),
            "net":         parse_amount(net),
            "order_count": parse_amount(order_cnt),
            "guest_count": parse_amount(guest_cnt),
            "order_avg":   parse_amount(order_avg),
            "discounts":   parse_amount(discounts),
            "refunds":     parse_amount(refunds),
            "no_sale":     parse_amount(no_sale),
        },
        "labor": {
            "cost":  parse_amount(labor_cost),
            "pct":   parse_pct(labor_pct) or parse_amount(labor_pct),
            "hours": parse_amount(labor_hrs),
            "splh":  parse_amount(splh),
        },
        "food_cost": {
            "theoretical_pct": parse_pct(fc_theo)   or parse_amount(fc_theo),
            "actual_pct":      parse_pct(fc_actual)  or parse_amount(fc_actual),
            "variance_pct":    parse_pct(fc_var)     or parse_amount(fc_var),
            "dollars":         parse_amount(fc_dollars),
        },
        "cash": {
            "total":      parse_amount(cash_total),
            "deposits":   parse_amount(deposits),
            "over_short": parse_amount(over_short) if over_short else 0.0,
            "tax":        parse_amount(tax_total),
        },
        "channels":  channels,
        "payments":  payments,
        "discounts": discounts_detail,
    }

    log.info(f"Sales: {data['sales']}")
    log.info(f"Labor: {data['labor']}")
    log.info(f"Food cost: {data['food_cost']}")
    log.info(f"Channels: {len(channels)} | Payments: {len(payments)} | Discounts: {len(discounts_detail)}")
    return data


async def scrape() -> dict:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        ctx = await browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
        )
        page = await ctx.new_page()

        if not await do_login(page):
            await browser.close()
            raise RuntimeError("Login failed — check credentials and screenshots in data/")

        await navigate_to_daily_report(page)
        await set_filters(page)

        data = await extract_data(page)
        await browser.close()
        return data


# ─── HTML Generator ───────────────────────────────────────────────────────────
def bar_html(pct: float | None, color: str = "") -> str:
    w = min(pct or 0, 100)
    cls = f"bar {color}".strip()
    return f'<div class="bar-wrap"><div class="{cls}" style="width:{w:.2f}%"></div></div>'


def generate_html(d: dict) -> str:
    meta  = d.get("meta", {})
    s     = d.get("sales", {})
    lab   = d.get("labor", {})
    fc    = d.get("food_cost", {})
    cash  = d.get("cash", {})
    chs   = d.get("channels", [])
    pays  = d.get("payments", [])
    discs = d.get("discounts", [])

    rpt_display = meta.get("report_display", RPT_DISPLAY)
    generated   = meta.get("generated", GEN_DISPLAY)

    # ── Channels table rows ────────────────────────────────────────────────────
    ch_rows = ""
    ch_total_sales = sum(c.get("sales") or 0 for c in chs) or s.get("net") or 0
    ch_total_orders = sum(c.get("orders") or 0 for c in chs)
    for ch in chs:
        name   = ch.get("name", "")
        sales  = ch.get("sales")
        pct    = ch.get("pct") or (sales / ch_total_sales * 100 if ch_total_sales and sales else None)
        orders = ch.get("orders")
        color  = ch.get("color", "red")
        bar_color = "" if color == "red" else color
        ch_rows += f"""
        <tr>
          <td><strong>{name}</strong></td>
          <td>{fmt_num(orders) if orders else '—'}</td>
          <td><strong>{fmt_dollar(sales)}</strong></td>
          <td>{fmt_pct(pct)}</td>
          <td>{bar_html(pct, bar_color)}</td>
        </tr>"""

    net_sales = s.get("net") or ch_total_sales or 0
    order_count = s.get("order_count")
    ch_rows += f"""
        <tr style="background:#fdf5f5;font-weight:700;">
          <td><strong>TOTAL</strong></td>
          <td><strong>{fmt_num(order_count)}</strong></td>
          <td><strong>{fmt_dollar(net_sales if net_sales else None)}</strong></td>
          <td><strong>100%</strong></td>
          <td></td>
        </tr>"""

    # ── Payments grid ──────────────────────────────────────────────────────────
    pay_cards = ""
    total_pay = sum(p.get("amount") or 0 for p in pays)
    for p in pays:
        amt = p.get("amount")
        pct = p.get("pct") or (amt / total_pay * 100 if total_pay and amt else None)
        pay_cards += f"""
      <div class="tender-card">
        <div class="t-label">{p.get('name','')}</div>
        <div class="t-value">{fmt_dollar(amt)}</div>
        <div class="t-pct">{fmt_pct(pct)}</div>
      </div>"""
    if not pay_cards:
        pay_cards = '<div style="color:#aaa;padding:16px;">Payment detail not available in Net Chef — check PAR POS</div>'

    # ── Discounts table rows ───────────────────────────────────────────────────
    disc_rows = ""
    disc_total = sum(d2.get("amount") or 0 for d2 in discs)
    for d2 in discs:
        amt = d2.get("amount")
        pct = d2.get("pct") or (amt / disc_total * 100 if disc_total and amt else None)
        disc_rows += f"""
        <tr>
          <td>{d2.get('name','')}</td>
          <td>—</td>
          <td>{fmt_dollar(amt)}</td>
          <td>{fmt_pct(pct)}</td>
          <td>{bar_html(pct)}</td>
        </tr>"""
    if disc_rows:
        disc_rows += f"""
        <tr style="background:#fdf5f5;font-weight:700;">
          <td><strong>TOTAL</strong></td>
          <td>—</td>
          <td><strong>{fmt_dollar(disc_total)}</strong></td>
          <td><strong>100%</strong></td>
          <td></td>
        </tr>"""
    else:
        disc_rows = '<tr><td colspan="5" style="color:#aaa;padding:16px;">No discount detail found</td></tr>'

    # ── Food cost section (only if data present) ──────────────────────────────
    fc_section = ""
    if any(v is not None for v in [fc.get("theoretical_pct"), fc.get("actual_pct"), fc.get("variance_pct")]):
        var_pct  = fc.get("variance_pct")
        var_color = "orange" if var_pct and var_pct > 1 else "green"
        fc_section = f"""
  <!-- SECTION 3: Food Cost (CrunchTime) -->
  <div class="section">
    <div class="section-title">&#127829; Food Cost (CrunchTime Net Chef)</div>
    <div class="card-grid grid-3">
      <div class="card blue">
        <div class="label">Theoretical Cost %</div>
        <div class="value">{fmt_pct(fc.get('theoretical_pct'))}</div>
        <div class="sub">Recipe-based target</div>
      </div>
      <div class="card highlight">
        <div class="label">Actual Cost %</div>
        <div class="value">{fmt_pct(fc.get('actual_pct'))}</div>
        <div class="sub">Based on inventory usage</div>
      </div>
      <div class="card {var_color}">
        <div class="label">Variance</div>
        <div class="value">{fmt_pct(var_pct)}</div>
        <div class="sub">Actual minus theoretical</div>
      </div>
    </div>
  </div>"""

    # ── Labor % color ──────────────────────────────────────────────────────────
    lab_pct = lab.get("pct")
    lab_pct_color = "green" if lab_pct and lab_pct < 25 else ("orange" if lab_pct and lab_pct < 30 else "highlight")

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
  .card.highlight {{ border-left: 4px solid #d52b1e; }}
  .card.green {{ border-left: 4px solid #27ae60; }}
  .card.orange {{ border-left: 4px solid #e67e22; }}
  .card.blue {{ border-left: 4px solid #2980b9; }}
  .channel-table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.07); }}
  .channel-table th {{ background: #d52b1e; color: white; padding: 12px 16px; text-align: left; font-size: 0.85em; text-transform: uppercase; letter-spacing: 0.5px; }}
  .channel-table td {{ padding: 11px 16px; border-bottom: 1px solid #f0f2f5; font-size: 0.95em; }}
  .channel-table tr:last-child td {{ border-bottom: none; }}
  .channel-table tr:hover td {{ background: #fdf5f5; }}
  .bar-wrap {{ background: #f0f2f5; border-radius: 20px; height: 10px; width: 100%; }}
  .bar {{ background: #d52b1e; border-radius: 20px; height: 10px; }}
  .bar.blue {{ background: #2980b9; }}
  .bar.green {{ background: #27ae60; }}
  .bar.orange {{ background: #e67e22; }}
  .bar.purple {{ background: #8e44ad; }}
  .bar.teal {{ background: #16a085; }}
  .tender-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; }}
  .tender-card {{ background: white; border-radius: 10px; padding: 14px 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.07); text-align: center; }}
  .tender-card .t-label {{ font-size: 0.75em; color: #888; text-transform: uppercase; margin-bottom: 6px; }}
  .tender-card .t-value {{ font-size: 1.2em; font-weight: 700; color: #222; }}
  .tender-card .t-pct {{ font-size: 0.78em; color: #d52b1e; margin-top: 3px; }}
  footer {{ text-align: center; padding: 20px; color: #aaa; font-size: 0.8em; margin-top: 10px; }}
  @media (max-width: 900px) {{
    .grid-4 {{ grid-template-columns: repeat(2, 1fr); }}
    .grid-3 {{ grid-template-columns: repeat(2, 1fr); }}
    .tender-grid {{ grid-template-columns: repeat(3, 1fr); }}
  }}
  @media (max-width: 600px) {{
    .grid-4, .grid-3, .grid-2, .tender-grid {{ grid-template-columns: 1fr 1fr; }}
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
    <div>Report generated {generated}</div>
  </div>
</header>

<div class="container">

  <!-- SECTION 1: Sales Overview -->
  <div class="section">
    <div class="section-title">&#128200; Daily Sales Overview</div>
    <div class="card-grid grid-4">
      <div class="card highlight">
        <div class="label">Gross Sales</div>
        <div class="value">{fmt_dollar(s.get('gross'))}</div>
        <div class="sub">Before discounts &amp; refunds</div>
      </div>
      <div class="card highlight">
        <div class="label">Net Sales</div>
        <div class="value">{fmt_dollar(s.get('net'))}</div>
        <div class="sub">After adjustments</div>
      </div>
      <div class="card blue">
        <div class="label">Order Count</div>
        <div class="value">{fmt_num(s.get('order_count'))}</div>
        <div class="sub">Total transactions</div>
      </div>
      <div class="card blue">
        <div class="label">Guest Count</div>
        <div class="value">{fmt_num(s.get('guest_count'))}</div>
        <div class="sub">Total guests served</div>
      </div>
      <div class="card green">
        <div class="label">Order Average</div>
        <div class="value">{fmt_dollar(s.get('order_avg'))}</div>
        <div class="sub">Per transaction</div>
      </div>
      <div class="card orange">
        <div class="label">Discounts</div>
        <div class="value">{fmt_dollar(s.get('discounts'))}</div>
        <div class="sub">Employee + Marketing</div>
      </div>
      <div class="card orange">
        <div class="label">Refunds</div>
        <div class="value">{fmt_dollar(s.get('refunds'))}</div>
        <div class="sub">Total refunded</div>
      </div>
      <div class="card green">
        <div class="label">No Sale Count</div>
        <div class="value">{fmt_num(s.get('no_sale'))}</div>
        <div class="sub">Register opens w/o sale</div>
      </div>
    </div>
  </div>

  <!-- SECTION 2: Labor -->
  <div class="section">
    <div class="section-title">&#128104;&#8205;&#127859; Labor Summary</div>
    <div class="card-grid grid-4">
      <div class="card highlight">
        <div class="label">Labor Cost</div>
        <div class="value">{fmt_dollar(lab.get('cost'))}</div>
        <div class="sub">Total wages</div>
      </div>
      <div class="card {lab_pct_color}">
        <div class="label">Labor Percent</div>
        <div class="value">{fmt_pct(lab.get('pct'))}</div>
        <div class="sub">Of net sales</div>
      </div>
      <div class="card blue">
        <div class="label">Labor Hours</div>
        <div class="value">{fmt_num(lab.get('hours'), 2)}</div>
        <div class="sub">Total hours worked</div>
      </div>
      <div class="card green">
        <div class="label">Sales Per Labor Hour</div>
        <div class="value">{fmt_dollar(lab.get('splh'))}</div>
        <div class="sub">Productivity metric</div>
      </div>
    </div>
  </div>
{fc_section}
  <!-- SECTION 4: Sales by Channel -->
  <div class="section">
    <div class="section-title">&#128241; Sales by Channel</div>
    <table class="channel-table">
      <thead>
        <tr>
          <th>Channel</th>
          <th>Orders</th>
          <th>Sales</th>
          <th>% of Total</th>
          <th>Visual</th>
        </tr>
      </thead>
      <tbody>{ch_rows}
      </tbody>
    </table>
  </div>

  <!-- SECTION 5: Payment Breakdown -->
  <div class="section">
    <div class="section-title">&#128179; Payment Breakdown</div>
    <div class="tender-grid">{pay_cards}
    </div>
  </div>

  <!-- SECTION 6: Cash & Tax Summary -->
  <div class="section">
    <div class="section-title">&#128181; Cash &amp; Tax Summary</div>
    <div class="card-grid grid-4">
      <div class="card green">
        <div class="label">Total Cash</div>
        <div class="value">{fmt_dollar(cash.get('total'))}</div>
        <div class="sub">Expected in drawer</div>
      </div>
      <div class="card green">
        <div class="label">Bank Deposits</div>
        <div class="value">{fmt_dollar(cash.get('deposits'))}</div>
        <div class="sub">Deposited today</div>
      </div>
      <div class="card blue">
        <div class="label">Cash Over/Short</div>
        <div class="value">{fmt_dollar(cash.get('over_short'))}</div>
        <div class="sub">Variance</div>
      </div>
      <div class="card blue">
        <div class="label">Total Tax Collected</div>
        <div class="value">{fmt_dollar(cash.get('tax'))}</div>
        <div class="sub">Food + Drinks</div>
      </div>
    </div>
  </div>

  <!-- SECTION 7: Discounts -->
  <div class="section">
    <div class="section-title">&#127991; Discount Breakdown</div>
    <table class="channel-table">
      <thead>
        <tr>
          <th>Discount Type</th>
          <th>Qty</th>
          <th>Amount</th>
          <th>% of Total</th>
          <th>Visual</th>
        </tr>
      </thead>
      <tbody>{disc_rows}
      </tbody>
    </table>
  </div>

</div>

<footer>
  Five Guys KY-2065 Dixie Highway &bull; Data from CrunchTime Net Chef &bull; Business Date: {rpt_display} &bull; Generated: {generated}
</footer>

</body>
</html>"""


# ─── Main ─────────────────────────────────────────────────────────────────────
async def main():
    if not USERNAME or not PASSWORD:
        log.error("CRUNCHTIME_USERNAME and CRUNCHTIME_PASSWORD must be set")
        sys.exit(1)

    log.info(f"=== Five Guys KY-2065 Dashboard — {RPT_DISPLAY} ===")
    log.info(f"Target: {NETCHEF_BASE}")

    # Attempt scrape
    try:
        data = await scrape()
        log.info("Scrape succeeded")
    except Exception as e:
        log.error(f"Scrape failed: {e}")
        # Fall back to last known data if available
        fallback = DATA_DIR / "latest.json"
        if fallback.exists():
            log.warning("Using cached data from previous run")
            data = json.loads(fallback.read_text())
            data["meta"]["generated"] = GEN_DISPLAY + " (cached)"
        else:
            log.error("No cached data available — cannot generate dashboard")
            sys.exit(1)

    # Save data snapshot
    (DATA_DIR / "latest.json").write_text(
        json.dumps(data, indent=2, default=str)
    )
    log.info("Saved data/latest.json")

    # Generate dashboard
    html = generate_html(data)
    out = ROOT / "dashboard.html"
    out.write_text(html, encoding="utf-8")
    log.info(f"Wrote {out} ({len(html):,} bytes)")

    log.info("Done.")


if __name__ == "__main__":
    asyncio.run(main())
