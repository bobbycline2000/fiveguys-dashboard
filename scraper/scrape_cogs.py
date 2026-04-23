#!/usr/bin/env python3
"""
CrunchTime COGS Variance Scraper
================================
Pulls two things from Net Chef for store 2065:

  1. "Top 10 Actual vs. Theoretical Cost Items" widget (Food category)
     — found at the bottom of the landing dashboard.
  2. Week COGS % from the drilldown inventory page (opened via the
     date-range link in the widget's top-right corner).

Writes: data/cogs_variance.json

Reuses login / location-select from main.py — run this AFTER the main
scraper has left the browser on the dashboard, or stand-alone (it will
log in itself).

Env:
  CRUNCHTIME_USERNAME
  CRUNCHTIME_PASSWORD
  STORE_ID               (default "2065")
"""
import os, sys, json, re, asyncio, logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# Reuse login/location helpers from main scraper
sys.path.insert(0, str(Path(__file__).parent))
from main import (  # noqa: E402
    NETCHEF_BASE, USERNAME, PASSWORD, DATA_DIR,
    do_login, select_location,
)

STORE_ID = os.environ.get("STORE_ID", "2065")
ET = timezone(timedelta(hours=-4))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("cogs")


# ── Parsing ──────────────────────────────────────────────────────────
_MONEY = re.compile(r"\$?([\d,]+(?:\.\d{1,2})?)")

def _money(s):
    m = _MONEY.search(s or "")
    if not m:
        return None
    return float(m.group(1).replace(",", ""))


def parse_variance_rows(text):
    """
    Parse the widget's text block. Expected line pattern per item:
        <rank>.<name> $<actual> $<theoretical> <pct>%
    Example:
        1.Ground Beef $2,812 $2,702 -4%
    The widget also sometimes wraps the name onto multiple lines — we
    rebuild rows by splitting on leading "\n<digit>." markers.
    """
    # Normalize and split into "row blobs" that each start with "N."
    blobs = re.split(r"(?m)^\s*(\d{1,2})\s*\.\s*", text)
    # blobs = ['', '1', 'Ground Beef …', '2', 'Hot Dog …', ...]
    items = []
    for i in range(1, len(blobs) - 1, 2):
        rank = int(blobs[i])
        body = blobs[i + 1]
        # first two money values are actual/theoretical; last % is variance
        money_vals = _MONEY.findall(body)
        pct = re.search(r"(-?\d+(?:\.\d+)?)\s*%", body)
        if len(money_vals) < 2 or not pct:
            continue
        actual = float(money_vals[0].replace(",", ""))
        theo   = float(money_vals[1].replace(",", ""))
        # the name is everything before the first $
        name = re.split(r"\$", body, 1)[0].strip().rstrip(",").strip()
        name = re.sub(r"\s+", " ", name)
        items.append({
            "rank": rank,
            "name": name,
            "actual": round(actual, 2),
            "theoretical": round(theo, 2),
            "over_dollars": round(actual - theo, 2),
            "variance_pct": float(pct.group(1)),
        })
    return items


# ── Scraping ─────────────────────────────────────────────────────────
async def locate_variance_widget(page):
    """Scroll to reveal the widget, then return its text."""
    widget_title = "Top 10 Actual vs. Theoretical Cost Items"
    # Scroll down until widget appears in the DOM
    for _ in range(8):
        found = await page.evaluate(
            "(t) => { const el = [...document.querySelectorAll('*')]"
            ".find(e => e.innerText && e.innerText.trim().startsWith(t));"
            " if (el) el.scrollIntoView({block:'center'}); return !!el; }",
            widget_title,
        )
        if found:
            break
        await page.evaluate("window.scrollBy(0, 600)")
        await page.wait_for_timeout(800)

    await page.wait_for_timeout(1_500)
    await page.screenshot(path=str(DATA_DIR / "07_cogs_widget.png"))

    # Extract the widget's container text (the nearest card/div wrapping the title)
    widget_text = await page.evaluate(
        """(t) => {
            const start = [...document.querySelectorAll('*')]
                .find(e => e.innerText && e.innerText.trim().startsWith(t));
            if (!start) return null;
            // Walk up until we find a container with all 10 items (≥ 3 "$" signs)
            let node = start;
            for (let i = 0; i < 8; i++) {
                node = node.parentElement;
                if (!node) break;
                const txt = node.innerText || "";
                if ((txt.match(/\\$/g) || []).length >= 6) return txt;
            }
            return start.innerText;
        }""",
        widget_title,
    )
    return widget_text


async def scrape_cogs_pct(page):
    """
    Open the drilldown (click the date range in widget corner) and
    extract the COGS % from the inventory/COGS page.
    """
    try:
        # Click the date-range link/button in the widget's top-right corner
        clicked = await page.evaluate("""
            () => {
                const title = [...document.querySelectorAll('*')]
                    .find(e => e.innerText && e.innerText.trim().startsWith('Top 10 Actual vs. Theoretical'));
                if (!title) return false;
                let container = title;
                for (let i=0;i<6;i++){ container = container.parentElement; if(!container) break; }
                if (!container) return false;
                // Find a text matching date-range pattern MM/DD/YYYY - MM/DD/YYYY
                const link = [...container.querySelectorAll('*')]
                    .find(e => /\\d{2}\\/\\d{2}\\/\\d{4}\\s*-\\s*\\d{2}\\/\\d{2}\\/\\d{4}/.test(e.innerText||''));
                if (!link) return false;
                link.click();
                return true;
            }
        """)
        if not clicked:
            log.info("Could not find date-range link to drill down; skipping COGS %")
            return None
        await page.wait_for_timeout(4_000)
        await page.screenshot(path=str(DATA_DIR / "08_cogs_drilldown.png"))
        body = await page.inner_text("body")

        # Look for a "COGS %" or "Cost of Goods" value
        m = re.search(r"(?:COGS|Cost of Goods)[^\d\-]{0,40}(-?\d+(?:\.\d+)?)\s*%", body, re.I)
        if m:
            return float(m.group(1))
        return None
    except Exception as e:
        log.warning(f"COGS % drilldown failed: {e}")
        return None


# ── Main ─────────────────────────────────────────────────────────────
async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1600, "height": 1000})
        page = await ctx.new_page()

        await page.goto(NETCHEF_BASE, wait_until="domcontentloaded", timeout=30_000)
        await do_login(page)
        await select_location(page)
        await page.wait_for_timeout(3_000)

        widget_text = await locate_variance_widget(page)
        if not widget_text:
            log.error("Widget not found on dashboard")
            await browser.close()
            return

        items = parse_variance_rows(widget_text)
        log.info(f"Parsed {len(items)} variance items")

        # Sort by $ over theoretical (descending) — Bobby's preferred ranking
        items_by_dollars = sorted(items, key=lambda x: x["over_dollars"], reverse=True)
        for idx, it in enumerate(items_by_dollars, 1):
            it["rank"] = idx

        cogs_pct = await scrape_cogs_pct(page)
        log.info(f"Week COGS %: {cogs_pct}")

        await browser.close()

    now = datetime.now(tz=ET)
    # Last-week Mon-Sun range
    today = now.date()
    last_sun = today - timedelta(days=(today.weekday() + 1) % 7 + 1)
    last_mon = last_sun - timedelta(days=6)

    out = {
        "meta": {
            "source": "CrunchTime Net Chef — Top 10 Actual vs. Theoretical Cost Items",
            "category": "Food",
            "store": STORE_ID,
            "week_start": last_mon.strftime("%Y-%m-%d"),
            "week_end":   last_sun.strftime("%Y-%m-%d"),
            "pulled":     now.strftime("%Y-%m-%d %H:%M ET"),
            "method":     "playwright",
        },
        "cogs_pct_week": cogs_pct,
        "items": items_by_dollars,
        "ranking": "over_dollars_desc",
    }

    # New canonical path: data/raw/crunchtime/<store>/<week_end>/cogs_variance.json
    raw_dir = DATA_DIR / "raw" / "crunchtime" / STORE_ID / out["meta"]["week_end"]
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_path = raw_dir / "cogs_variance.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    log.info(f"Wrote {out_path}")
    # Compat: also write legacy top-level file for existing readers
    (DATA_DIR / "cogs_variance.json").write_text(json.dumps(out, indent=2), encoding="utf-8")


if __name__ == "__main__":
    if not USERNAME or not PASSWORD:
        log.error("CRUNCHTIME_USERNAME / CRUNCHTIME_PASSWORD env vars required")
        sys.exit(1)
    asyncio.run(run())
