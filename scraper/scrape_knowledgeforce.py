#!/usr/bin/env python3
"""
KnowledgeForce (Marketforce) Secret Shop Scraper
=================================================
Pulls all secret shops for KY-2065 from knowledgeforce.com, extracts
per-shop Service/Quality/Cleanliness/CSAT, computes Week/Month/Quarter
rolling averages, and writes shops.json — same schema wire_dashboard.py
already reads.

Trigger model: event-driven, NOT daily cron.
The outlook-daily-pull-7am skill detects a new Marketforce shop email
(Thu/Fri) and runs this script.

Usage:
  KNOWLEDGEFORCE_USERNAME=fg2065@estep-co.com KNOWLEDGEFORCE_PASSWORD=xxx \\
      python scraper/scrape_knowledgeforce.py --store 2065

Output:
  data/raw/marketforce/<store>/<today>/shops.json

Schema (matches existing 2026-04-23 file):
  {
    "meta": {"generated", "location", "status", "shops_total"},
    "latest": { ... single-shop dict ... },
    "averages": {"week": {...}, "month": {...}, "quarter": {...}},
    "shops": [ ... full-history list ... ]
  }

Discovery notes: scraper/KNOWLEDGEFORCE_DISCOVERY.md
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = ROOT / "data" / "raw" / "marketforce"

ET = timezone(timedelta(hours=-4))

LOGIN_URL = "https://www.knowledgeforce.com/"
LIST_URL  = "https://www.knowledgeforce.com/reporting/reports/report?id=fgmysteryshop"
SHOP_URL_TPL = (
    "https://www.knowledgeforce.com/reporting/assignment/view"
    "?dataset={dataset}"
)


def log(msg: str) -> None:
    print(f"[knowledgeforce] {msg}", flush=True)


def login(page, username: str, password: str) -> bool:
    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30_000)
    # Username + password are simple inputs; LOG IN is a green button
    try:
        page.fill('input[name="username"], input[type="text"]:visible', username, timeout=10_000)
        page.fill('input[name="password"], input[type="password"]:visible', password, timeout=10_000)
        page.click('button:has-text("LOG IN"), input[type="submit"]', timeout=10_000)
        page.wait_for_load_state("networkidle", timeout=20_000)
    except PlaywrightTimeout:
        log("Login form interaction timed out")
        return False

    # Verify by checking we're past the login wall
    if "/login" in page.url.lower() or "username" in page.content().lower()[:5000]:
        log("Login appears to have failed — still on login page")
        return False
    return True


def select_all_periods(page) -> None:
    """
    On the Secret Shop dashboard, select every Year checkbox so the
    Individual Shops table shows all available shops (not just the
    most recent period).
    """
    # Let any post-login redirect chain finish before navigating away
    page.wait_for_timeout(2_500)
    # Retry once on ERR_ABORTED (post-login redirect race)
    for attempt in range(2):
        try:
            page.goto(LIST_URL, wait_until="domcontentloaded", timeout=30_000)
            page.wait_for_load_state("networkidle", timeout=20_000)
            break
        except PlaywrightTimeout:
            if attempt == 1:
                raise
            log(f"goto retry (attempt {attempt + 1})")
            page.wait_for_timeout(2_000)
        except Exception as e:
            if "ERR_ABORTED" in str(e) and attempt == 0:
                log("ERR_ABORTED on first goto — waiting and retrying")
                page.wait_for_timeout(3_000)
                continue
            raise
    # Click "Select All" inside the Year filter group, then re-run
    try:
        page.click('text="Select All"', timeout=5_000)
        page.wait_for_timeout(2_000)
        # Trigger filter apply if present
        for label in ("Apply", "Run", "Filter", "Submit"):
            btn = page.locator(f'button:has-text("{label}")').first
            if btn.count() and btn.is_visible():
                btn.click()
                break
        page.wait_for_load_state("networkidle", timeout=15_000)
    except PlaywrightTimeout:
        log("Could not click Select All — proceeding with default filter")


def read_individual_shops_table(page) -> list[dict]:
    """
    Read the Individual Shops DataTable. Returns list of dicts with
    job_id, location_id, location, date (raw MM/DD/YYYY), meal_period,
    score, and the href dataset (jid/period2/scheme) needed for the
    drilldown.
    """
    rows = page.evaluate("""
        () => {
            const tables = [...document.querySelectorAll('table')];
            // Find the table with these exact headers
            const target = tables.find(t => {
                const hs = [...t.querySelectorAll('thead th')].map(h => (h.innerText||'').trim());
                return hs.includes('Job #') && hs.includes('Score') && hs.includes('Meal Period');
            });
            if (!target) return [];
            return [...target.querySelectorAll('tbody tr')].map(r => {
                const cells = [...r.querySelectorAll('td')].map(c => (c.innerText||'').trim());
                const link = r.querySelector('a[href]');
                return {
                    cells,
                    href: link ? link.getAttribute('href') : null
                };
            });
        }
    """)
    out = []
    for row in rows:
        cells = row.get("cells") or []
        if len(cells) < 6:
            continue
        href = row.get("href") or ""
        m = re.search(r"dataset=([^&]+)", href)
        dataset_raw = ""
        if m:
            from urllib.parse import unquote
            dataset_raw = unquote(m.group(1))
        try:
            dataset_obj = json.loads(dataset_raw) if dataset_raw else {}
        except Exception:
            dataset_obj = {}
        out.append({
            "job_id":      cells[0],
            "location_id": cells[1],
            "location":    cells[2],
            "date_raw":    cells[3],   # "04/17/2026"
            "meal_period": cells[4],
            "score":       float(cells[5]) if cells[5] else None,
            "jid":         dataset_obj.get("jid"),
            "period2":     (dataset_obj.get("period2") or [None])[0],
            "scheme":      (dataset_obj.get("scheme") or [None])[0],
            "href":        href,
        })
    return out


def fetch_shop_sqc(page, href: str) -> dict:
    """
    Navigate to a single shop's detail page and extract
    Service / Quality / Cleanliness / Customer Satisfaction / Score.
    """
    full = "https://www.knowledgeforce.com" + href if href.startswith("/") else href
    page.goto(full, wait_until="domcontentloaded", timeout=30_000)
    # Allow Highcharts + lazy content to render
    page.wait_for_timeout(2_500)
    txt = page.evaluate("() => document.body.innerText")
    out = {}
    for label, key in [
        ("Score", "score"),
        ("Service", "service"),
        ("Quality", "quality"),
        ("Cleanliness", "cleanliness"),
        ("Customer Satisfaction", "customer_satisfaction"),
    ]:
        m = re.search(rf"\b{re.escape(label)}\b[\s\n]+(\d{{1,3}}(?:\.\d+)?)", txt)
        out[key] = float(m.group(1)) if m else None
    return out


def parse_us_date(s: str) -> date | None:
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def compute_averages(shops: list[dict]) -> dict:
    """Week / Month / Quarter rolling averages of score."""
    today = datetime.now(tz=ET).date()
    week_cutoff    = today - timedelta(days=7)
    month_cutoff   = today - timedelta(days=30)
    quarter_cutoff = today - timedelta(days=90)

    def avg(window_cutoff):
        scored = [s for s in shops if s.get("score") is not None
                  and s.get("_date") is not None and s["_date"] >= window_cutoff]
        if not scored:
            return {"score": None, "n": 0}
        return {
            "score": round(sum(s["score"] for s in scored) / len(scored), 2),
            "n":     len(scored),
        }

    return {
        "week":    avg(week_cutoff),
        "month":   avg(month_cutoff),
        "quarter": avg(quarter_cutoff),
    }


def build_payload(store_id: str, rows: list[dict]) -> dict:
    """
    Convert the scraped rows into the shops.json schema that
    wire_dashboard.py already consumes.
    """
    shops = []
    for r in rows:
        d = parse_us_date(r["date_raw"])
        shops.append({
            "job_id":                r["job_id"],
            "date":                  d.strftime("%Y-%m-%d") if d else r["date_raw"],
            "meal_period":           r["meal_period"],
            "score":                 r.get("score"),
            "period2":               r.get("period2"),
            "service":               r.get("service"),
            "quality":               r.get("quality"),
            "cleanliness":           r.get("cleanliness"),
            "customer_satisfaction": r.get("customer_satisfaction"),
            "_date":                 d,
        })
    # Sort newest first
    shops.sort(key=lambda s: s["_date"] or date.min, reverse=True)
    averages = compute_averages(shops)

    latest = None
    if shops:
        l = shops[0]
        latest = {
            "job_id":                l["job_id"],
            "date":                  l["date"],
            "meal_period":           l["meal_period"],
            "score":                 l["score"],
            "period2":               l["period2"],
            "service":               l["service"],
            "quality":               l["quality"],
            "cleanliness":           l["cleanliness"],
            "customer_satisfaction": l["customer_satisfaction"],
        }

    # Strip the internal _date field before serialising
    for s in shops:
        s.pop("_date", None)

    now = datetime.now(tz=ET)
    return {
        "meta": {
            "generated":   now.strftime("%Y-%m-%d %H:%M"),
            "location":    store_id,
            "status":      "ok" if shops else "empty",
            "shops_total": len(shops),
        },
        "latest":   latest,
        "averages": averages,
        "shops":    shops,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", default=os.environ.get("STORE_ID", "2065"))
    parser.add_argument("--headless", default="1", help="0 to watch the browser")
    args = parser.parse_args()

    user = os.environ.get("KNOWLEDGEFORCE_USERNAME", "")
    pw   = os.environ.get("KNOWLEDGEFORCE_PASSWORD", "")
    if not user or not pw:
        log("KNOWLEDGEFORCE_USERNAME / KNOWLEDGEFORCE_PASSWORD env vars required")
        return 3

    headless = args.headless != "0"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()

        if not login(page, user, pw):
            browser.close()
            return 3

        log("Login OK; loading Secret Shop Dashboard")
        select_all_periods(page)

        log("Reading Individual Shops table")
        rows = read_individual_shops_table(page)
        log(f"Found {len(rows)} shops")

        if not rows:
            log("Zero shops returned — filter may not have widened correctly")
            browser.close()
            return 2

        # Drilldown each shop for SQC values
        for i, r in enumerate(rows, 1):
            if not r.get("href"):
                continue
            log(f"  [{i}/{len(rows)}] drilldown {r['job_id']} ({r['date_raw']})")
            try:
                sqc = fetch_shop_sqc(page, r["href"])
                r.update(sqc)
            except Exception as e:
                log(f"    drilldown failed: {e}")

        browser.close()

    payload = build_payload(args.store, rows)

    today_str = datetime.now(tz=ET).date().isoformat()
    out_dir   = DATA_ROOT / args.store / today_str
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path  = out_dir / "shops.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    log(f"Wrote {out_path}")
    log(
        f"Latest: job {payload['latest']['job_id']} "
        f"({payload['latest']['date']}, {payload['latest']['meal_period']}, "
        f"{payload['latest']['score']}%) "
        f"| Q-avg {payload['averages']['quarter']['score']}% "
        f"({payload['averages']['quarter']['n']} shops)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
