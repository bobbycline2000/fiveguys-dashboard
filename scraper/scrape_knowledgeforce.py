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


def _navigate_to_report(page) -> None:
    """Navigate to the Secret Shop report page with retry on ERR_ABORTED."""
    page.wait_for_timeout(2_500)
    for attempt in range(2):
        try:
            page.goto(LIST_URL, wait_until="domcontentloaded", timeout=30_000)
            page.wait_for_load_state("networkidle", timeout=20_000)
            return
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


def _extract_all_period_ids(node) -> list:
    """Recursively collect all leaf IDs from the KnowledgeForce filter tree."""
    ids: list = []

    def walk(n):
        if isinstance(n, dict):
            children = n.get("values") or n.get("children") or n.get("items")
            node_id = n.get("id") or n.get("value") or n.get("key")
            if children:
                for c in children:
                    walk(c)
            elif node_id is not None:
                ids.append(node_id)
            else:
                for v in n.values():
                    if isinstance(v, (dict, list)):
                        walk(v)
        elif isinstance(n, list):
            for item in n:
                walk(item)

    walk(node)
    return ids


def _rows_from_widget_json(widget_json) -> list[dict] | None:
    """
    Parse shop rows from the widget API JSON response.
    KnowledgeForce typically returns DataTables server-side format
    ({"aaData": [...]}) or {"data": [...]}.
    Each row is an array: [job_id, loc_id, location, date, meal_period, score, href?]
    """
    if not isinstance(widget_json, (dict, list)):
        return None

    raw_rows = None
    if isinstance(widget_json, list):
        raw_rows = widget_json
    elif isinstance(widget_json, dict):
        for key in ("aaData", "data", "rows", "results", "records", "shops"):
            if key in widget_json:
                raw_rows = widget_json[key]
                break

    if not raw_rows:
        return None

    out = []
    for row in raw_rows:
        if isinstance(row, (list, tuple)) and len(row) >= 6:
            href = str(row[6]) if len(row) > 6 else ""
            m = re.search(r"dataset=([^&]+)", href)
            dataset_raw = ""
            if m:
                from urllib.parse import unquote
                dataset_raw = unquote(m.group(1))
            try:
                dataset_obj = json.loads(dataset_raw) if dataset_raw else {}
            except Exception:
                dataset_obj = {}
            try:
                score = float(str(row[5]).replace("%", ""))
            except (TypeError, ValueError):
                score = None
            out.append({
                "job_id":      str(row[0]),
                "location_id": str(row[1]),
                "location":    str(row[2]),
                "date_raw":    str(row[3]),
                "meal_period": str(row[4]),
                "score":       score,
                "jid":         dataset_obj.get("jid"),
                "period2":     (dataset_obj.get("period2") or [None])[0],
                "scheme":      (dataset_obj.get("scheme") or [None])[0],
                "href":        href,
            })
        elif isinstance(row, dict):
            score_val = row.get("score") or row.get("Score") or row.get("total_score")
            try:
                score = float(str(score_val).replace("%", ""))
            except (TypeError, ValueError):
                score = None
            out.append({
                "job_id":      str(row.get("job_id") or row.get("job") or row.get("Job #") or ""),
                "location_id": str(row.get("location_id") or row.get("loc_id") or ""),
                "location":    str(row.get("location") or row.get("Location") or ""),
                "date_raw":    str(row.get("date") or row.get("Date") or row.get("shop_date") or ""),
                "meal_period": str(row.get("meal_period") or row.get("Meal Period") or ""),
                "score":       score,
                "jid":         None,
                "period2":     None,
                "scheme":      None,
                "href":        "",
            })

    return out if out else None


def fetch_all_shops_via_api(page) -> list[dict] | None:
    """
    Use KnowledgeForce's JSON APIs directly to get ALL available shops.

    1. Call /reporting/api/filters/903 to get the full period tree.
    2. Build a dataset selecting all periods.
    3. Call /reporting/api/widget/175639 with that dataset.
    4. Parse and return rows.

    Saves raw API responses to data/raw/marketforce/api_debug.json for tuning.
    Returns None if the API approach fails (caller should fall back to DOM).
    """
    import urllib.parse as _up

    api_debug: dict = {}

    # Step 1 — get filter tree
    filter_result = page.evaluate("""
        async () => {
            try {
                const r = await fetch('/reporting/api/filters/903?dataset=%5B%5D', {credentials: 'include'});
                const data = r.ok ? await r.json() : null;
                return {status: r.status, ok: r.ok, data};
            } catch (e) { return {error: String(e)}; }
        }
    """)
    api_debug["filter_api"] = {k: v for k, v in (filter_result or {}).items() if k != "data"}
    log(f"Filter API: status={filter_result.get('status')} ok={filter_result.get('ok')}")

    # Step 2 — build dataset with all period IDs
    dataset_variants: list[tuple[str, str]] = []

    if filter_result.get("ok") and filter_result.get("data"):
        period_ids = _extract_all_period_ids(filter_result["data"])
        api_debug["period_ids_count"] = len(period_ids)
        log(f"Extracted {len(period_ids)} period IDs from filter tree")

        if period_ids:
            # Try a few dataset encoding formats — KnowledgeForce may expect objects or plain IDs
            variants_raw = [
                [{"period2": pid} for pid in period_ids],
                period_ids,
                [{"id": pid} for pid in period_ids],
            ]
            for v in variants_raw:
                dataset_variants.append((_up.quote(json.dumps(v)), f"all-periods({type(v[0]).__name__})"))

    # Always try empty dataset as last resort
    dataset_variants.append(("%5B%5D", "empty"))

    # Step 3 — call widget API with each dataset variant, stop on first success with >0 rows
    for dataset_enc, label in dataset_variants:
        widget_result = page.evaluate(f"""
            async () => {{
                try {{
                    const url = '/reporting/api/widget/175639?isDash=1&reportId=923&dataset={dataset_enc}';
                    const r = await fetch(url, {{credentials: 'include'}});
                    const data = r.ok ? await r.json() : null;
                    return {{status: r.status, ok: r.ok, data}};
                }} catch (e) {{ return {{error: String(e)}}; }}
            }}
        """)
        log(f"Widget API ({label}): status={widget_result.get('status')} ok={widget_result.get('ok')}")
        api_debug[f"widget_{label}"] = {k: v for k, v in (widget_result or {}).items() if k != "data"}

        if widget_result.get("ok") and widget_result.get("data") is not None:
            rows = _rows_from_widget_json(widget_result["data"])
            if rows:
                api_debug[f"widget_{label}_rows"] = len(rows)
                log(f"  → {len(rows)} shops from widget API ({label})")
                _save_api_debug(api_debug)
                return rows
            else:
                api_debug[f"widget_{label}_parse_note"] = "ok but no parseable rows"
                log(f"  → API ok but no parseable rows; data keys: {list(widget_result.get('data', {}).keys()) if isinstance(widget_result.get('data'), dict) else type(widget_result.get('data')).__name__}")

    _save_api_debug(api_debug)
    log("All widget API variants failed — falling back to DOM")
    return None


def _save_api_debug(data: dict) -> None:
    try:
        debug_path = DATA_ROOT.parent.parent / "marketforce" / "api_debug.json"
        debug_path.parent.mkdir(parents=True, exist_ok=True)
        debug_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    except Exception:
        pass


def _expand_dom_filter(page) -> None:
    """
    DOM fallback: try to expand the period filter by clicking 'Select All' links,
    and set the DataTable to show all rows (overrides default 10-row pagination).
    """
    try:
        select_all_count = page.evaluate("""
            () => {
                const links = [...document.querySelectorAll('a, span, button, label')]
                    .filter(el => (el.innerText || '').trim() === 'Select All');
                let clicked = 0;
                for (const l of links) { try { l.click(); clicked += 1; } catch(e) {} }
                return clicked;
            }
        """)
        log(f"Clicked {select_all_count} 'Select All' link(s)")
        page.wait_for_timeout(1_500)

        # Try named filter buttons
        for label in ("Apply", "Run", "Filter", "Submit", "Refresh", "Update"):
            try:
                page.click(f'button:has-text("{label}"), input[value="{label}"]', timeout=2_000)
                log(f"Clicked filter button: {label}")
                break
            except PlaywrightTimeout:
                continue
        page.wait_for_load_state("networkidle", timeout=15_000)
    except Exception as e:
        log(f"DOM filter expand failed ({e})")

    # Override DataTable pagination to show all rows
    dt_result = page.evaluate("""
        () => {
            try {
                if (typeof $ === 'undefined' || !$.fn.DataTable) return 'no-jquery';
                let n = 0;
                $('table').each(function() {
                    if ($.fn.DataTable.isDataTable(this)) {
                        $(this).DataTable().page.len(-1).draw(false);
                        n++;
                    }
                });
                return n + ' tables set to show-all';
            } catch(e) { return String(e); }
        }
    """)
    log(f"DataTable show-all: {dt_result}")
    page.wait_for_timeout(1_500)


def select_all_periods(page) -> None:
    """Navigate to report page and widen the date scope (DOM approach)."""
    _navigate_to_report(page)
    _expand_dom_filter(page)


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


def load_historical_shops(store_id: str) -> list[dict]:
    """
    Return the shops list from the most recent existing shops.json for this
    store so that each run accumulates history rather than starting over.
    The current run's scrape is merged on top of this — new job_ids win,
    historical-only job_ids are kept.
    """
    store_dir = DATA_ROOT / store_id
    if not store_dir.exists():
        return []
    dated_dirs = sorted(
        (d for d in store_dir.iterdir() if d.is_dir()),
        reverse=True,
    )
    for d in dated_dirs:
        candidate = d / "shops.json"
        if candidate.exists():
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
                shops = data.get("shops", [])
                log(f"Loaded {len(shops)} historical shops from {candidate}")
                return shops
            except Exception as e:
                log(f"Could not load {candidate}: {e}")
    return []


def build_payload(store_id: str, rows: list[dict]) -> dict:
    """
    Convert the scraped rows into the shops.json schema that
    wire_dashboard.py already consumes.  Historical shops from the most
    recent prior run are merged in so the quarterly average is always
    computed over the full known history (not just what the CI filter
    returned this run).
    """
    # Map freshly-scraped rows by job_id
    scraped: dict[str, dict] = {}
    for r in rows:
        d = parse_us_date(r["date_raw"])
        scraped[r["job_id"]] = {
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
        }

    # Merge historical shops — fresh scrape wins on overlap
    historical = load_historical_shops(store_id)
    merged: dict[str, dict] = {}
    for h in historical:
        job_id = h.get("job_id")
        if not job_id:
            continue
        d = parse_us_date(h.get("date", "")) if "date_raw" not in h else parse_us_date(h["date_raw"])
        if d is None:
            try:
                d = date.fromisoformat(h.get("date", ""))
            except Exception:
                d = None
        entry = dict(h)
        entry["_date"] = d
        merged[job_id] = entry
    # Fresh-scraped entries overwrite historical
    merged.update(scraped)
    shops = list(merged.values())

    log(f"Total shops after merge: {len(shops)} ({len(scraped)} fresh, {len(merged) - len(scraped)} historical-only)")

    # Sort newest first
    shops.sort(key=lambda s: s.get("_date") or date.min, reverse=True)
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
        _navigate_to_report(page)

        # Strategy 1: call KnowledgeForce's JSON widget API directly (bypasses DOM filter)
        log("Trying widget API approach for full shop history")
        rows = fetch_all_shops_via_api(page)

        if rows is None:
            # Strategy 2: DOM fallback — widen filter checkboxes + DataTable show-all
            log("API approach failed — falling back to DOM table")
            _expand_dom_filter(page)
            rows = read_individual_shops_table(page)
        else:
            log(f"API returned {len(rows)} shops")

        log(f"Total shops from primary source: {len(rows)}")

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
