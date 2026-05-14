"""
Look up a customer order in Par Brink by name + business date.

Drives admin5.parpos.com/Orders/Search/ with Playwright
(persistent profile — same auth pattern as bulk_pull_brink_history.py).

Usage:
  python scraper/parbrink_customer_order_lookup.py "Rebecca Pelt" 5/13/2026

Output (stdout, JSON):
  Found:    {"found": true, "order_id": "AACDWNNM9QA3", "internal_id": "74367773947929",
             "placed": "2026-05-13 17:18:38", "line_items": [...], "total": "71.46",
             "customer_name": "...", "customer_phone": "...", "customer_email": "..."}
  No match: {"found": false, "reason": "no_match", "search_term": "...", "date": "..."}
  Error:    {"found": false, "reason": "error", "detail": "..."} + exit code 1

Verified selectors (2026-05-14 inspection):
  - URL: /Orders/Search/
  - Date field: #DateRangeModel_Date  (name=DateRangeModel.Date)
  - Location hidden inputs: #LocationsModel_HierarchyControl_LocationValues (default = all locs)
  - Apply button: #getChangesets (submits the outer filter form)
  - Grid callback URL: /Orders/SearchOrdersGridPartial?StartDate=...&EndDate=...
  - Grid pagination: gvOrders.GotoPage(n) (0-indexed) — fires a DevExpress callback
  - Name column filter: gvOrders$DXFREditorcol3 (NAME column, sent in DevExpress callback body)
  - Order links in grid: javascript:ViewOrder('<internal-numeric-id>')
  - Order detail: /Orders/Order/<internal-numeric-id>
  - Grid shows ALL locations (location filter not propagated to grid callbacks)
    → We scan rows for customer name, then confirm order detail page has KY-2065 data

NOTE: headless=True does NOT render DevExpress grid rows (JS state machine doesn't run).
      headless=False is required. This script runs as a local Windows scheduled task,
      not in GitHub Actions CI.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Persistent profile in LOCALAPPDATA so OneDrive does not try to sync browser cache
_localappdata = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".cache")
PROFILE_DIR = Path(_localappdata) / "scg-brink-profile"

ORDER_SEARCH_URL = "https://admin5.parpos.com/Orders/Search/"
ORDER_DETAIL_BASE = "https://admin5.parpos.com/Orders/Order/"
LOGIN_URL = "https://admin5.parpos.com/Public/Login"

# Maximum pages to scan (each has 10 rows; 128 items = 13 pages max for a typical day)
MAX_PAGES = 20


# ---------------------------------------------------------------------------
# Credential loader (mirrors bulk_pull_brink_history.py)
# ---------------------------------------------------------------------------

def _load_env() -> tuple[str, str]:
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    username = os.environ.get("BRINK_USERNAME", "fg2065@estep-co.com")
    password = os.environ.get("BRINK_PASSWORD", "Muscle426$$")
    return username, password


# ---------------------------------------------------------------------------
# Row extractor — reads ViewOrder links from the current grid page
# ---------------------------------------------------------------------------

_GET_ROWS_JS = """
() => {
    const results = [];
    for (const a of document.querySelectorAll('a[href*="ViewOrder"], [onclick*="ViewOrder"]')) {
        const idm = (a.getAttribute('href') || a.getAttribute('onclick') || '')
                    .match(/ViewOrder\\('?(\\d+)'?\\)/);
        if (!idm) continue;
        const row = a.closest('tr');
        const rowText = row ? row.innerText.replace(/\\s+/g, ' ').trim() : '';
        results.push({id: idm[1], rowText: rowText});
    }
    return results;
}
"""


def _get_rows(page) -> list[dict]:
    return page.evaluate(_GET_ROWS_JS)


def _wait_for_rows(page, timeout_s: int = 15) -> list[dict]:
    """Poll until at least one row appears in the grid, or timeout."""
    for _ in range(timeout_s):
        rows = _get_rows(page)
        if rows:
            return rows
        time.sleep(1)
    return []


# ---------------------------------------------------------------------------
# Order detail parser
# ---------------------------------------------------------------------------

def _parse_order_detail(page, internal_id: str) -> dict:
    """Navigate to the order detail page and extract all fields."""
    detail_url = ORDER_DETAIL_BASE + internal_id
    page.goto(detail_url, wait_until="domcontentloaded", timeout=30_000)
    try:
        page.wait_for_load_state("networkidle", timeout=15_000)
    except Exception:
        time.sleep(3)

    text = page.evaluate("() => document.body.innerText")

    # Order confirmation code (e.g. AACDWNNM9QA3) — uppercase alphanumeric 10-14 chars
    order_id = ""
    order_id_m = re.search(r"\b([A-Z0-9]{10,14})\b", text)
    if order_id_m:
        order_id = order_id_m.group(1)

    # Placed datetime  "5/13/2026 5:18:38 PM"
    placed = ""
    placed_m = re.search(
        r"(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}:\d{2}:\d{2}\s*[AP]M)", text
    )
    if placed_m:
        from datetime import datetime as _dt
        try:
            dt = _dt.strptime(
                placed_m.group(1) + " " + placed_m.group(2).strip(),
                "%m/%d/%Y %I:%M:%S %p",
            )
            placed = dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            placed = placed_m.group(0)

    # Total
    total = ""
    total_m = re.search(r"(?i)total[:\s]+\$?([\d,]+\.\d{2})", text)
    if not total_m:
        total_m = re.search(r"\$([\d,]+\.\d{2})\s*$", text, re.MULTILINE)
    if total_m:
        total = total_m.group(1).replace(",", "")

    # Customer fields
    customer_name = ""
    customer_phone = ""
    customer_email = ""
    name_m = re.search(
        r"(?i)(?:customer|name)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", text
    )
    if name_m:
        customer_name = name_m.group(1)
    phone_m = re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
    if phone_m:
        customer_phone = phone_m.group(0)
    email_m = re.search(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", text)
    if email_m:
        customer_email = email_m.group(0)

    # Line items — qty + description + price
    line_items: list[dict] = []
    skip_words = {"subtotal", "total", "tax", "discount", "fee", "tip", "delivery", "order"}
    for m in re.finditer(r"(\d+)\s+([\w][\w\s,&'-]{1,58}?)\s+\$?([\d,]+\.\d{2})", text):
        item_name = m.group(2).strip()
        if any(w in item_name.lower() for w in skip_words):
            continue
        if len(item_name) < 3:
            continue
        line_items.append({
            "qty": int(m.group(1)),
            "item": item_name,
            "price": m.group(3).replace(",", ""),
        })

    # Deduplicate
    seen: set[tuple] = set()
    deduped: list[dict] = []
    for li in line_items:
        key = (li["qty"], li["item"])
        if key not in seen:
            seen.add(key)
            deduped.append(li)

    return {
        "internal_id": internal_id,
        "order_id": order_id,
        "placed": placed,
        "line_items": deduped,
        "total": total,
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "customer_email": customer_email,
    }


# ---------------------------------------------------------------------------
# Main lookup
# ---------------------------------------------------------------------------

def lookup(search_term: str, date_str: str) -> dict:
    """
    Full lookup flow. Returns a dict always containing 'found'.
    Never raises — all errors produce {"found": false, "reason": "error", ...}.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {
            "found": False,
            "reason": "error",
            "detail": (
                "playwright not installed — "
                "run: pip install playwright && playwright install chromium"
            ),
        }

    username, password = _load_env()
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    try:
        with sync_playwright() as pw:
            # headless=False required: DevExpress ASPxGridView JS does not render
            # grid rows in headless mode (DXR.axd callback state machine is browser-bound).
            ctx = pw.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                headless=False,
                viewport={"width": 1400, "height": 900},
                args=["--disable-blink-features=AutomationControlled"],
            )
            page = ctx.pages[0] if ctx.pages else ctx.new_page()

            # ---- Always do a fresh login to avoid stale session cookies ----
            ctx.clear_cookies()
            page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30_000)
            time.sleep(1)
            try:
                page.wait_for_selector(
                    "input[name='Username'], input[name='username']",
                    timeout=15_000,
                    state="visible",
                )
            except Exception as exc:
                ctx.close()
                return {"found": False, "reason": "error", "detail": f"Login page: {exc}"}

            page.locator(
                "input[name='Username'], input[name='username']"
            ).first.fill(username)
            page.locator(
                "input[name='Password'], input[name='password']"
            ).first.fill(password)
            page.locator(
                "button:has-text('Continue'), input[type=submit], #submitLogin"
            ).first.click()
            page.wait_for_load_state("networkidle", timeout=30_000)
            time.sleep(1)

            if "/Public/Login" in page.url:
                ctx.close()
                return {
                    "found": False,
                    "reason": "error",
                    "detail": "Auto-login failed — check credentials in .env",
                }

            # ---- Navigate to Search Orders ----
            page.goto(ORDER_SEARCH_URL, wait_until="networkidle", timeout=30_000)
            time.sleep(4)

            # ---- Set date and submit the outer filter ----
            date_field = page.locator("#DateRangeModel_Date")
            date_field.click()
            date_field.press("Control+a")
            date_field.fill(date_str)
            date_field.press("Tab")
            time.sleep(0.3)

            page.locator("#getChangesets").click()

            # Wait for first page of results
            first_page_rows = _wait_for_rows(page, timeout_s=20)
            if not first_page_rows:
                ctx.close()
                return {
                    "found": False,
                    "reason": "no_match",
                    "search_term": search_term,
                    "date": date_str,
                }

            # ---- Pre-fill the Name column filter before any GotoPage call ----
            # The filter value is included in every subsequent DevExpress callback.
            # Fill with the first name (broader) for initial filter; we'll verify
            # full name match in the row text.
            first_name = search_term.split()[0]
            last_name = search_term.split()[-1] if len(search_term.split()) > 1 else ""
            term_lower = search_term.lower()

            name_filter = page.locator("#gvOrders_DXFREditorcol3_I")
            if name_filter.count():
                name_filter.fill(first_name)
                # Trigger the DevExpress filter callback via its onchange handler
                page.evaluate(
                    "() => typeof ASPx !== 'undefined' && ASPx.EValueChanged && "
                    "ASPx.EValueChanged('gvOrders_DXFREditorcol3')"
                )
                time.sleep(4)
                try:
                    page.wait_for_load_state("networkidle", timeout=10_000)
                except Exception:
                    pass

            # ---- Scan all grid pages for the full name ----
            best_id: str | None = None

            for page_idx in range(MAX_PAGES):
                if page_idx > 0:
                    result = page.evaluate(
                        f"() => typeof gvOrders !== 'undefined' ? "
                        f"(gvOrders.GotoPage({page_idx}), 'ok') : 'missing'"
                    )
                    if result == "missing":
                        break
                    time.sleep(4)
                    try:
                        page.wait_for_load_state("networkidle", timeout=10_000)
                    except Exception:
                        time.sleep(2)

                rows = _wait_for_rows(page, timeout_s=10)
                if not rows:
                    break  # no more pages

                for entry in rows:
                    row_lower = entry["rowText"].lower()
                    if first_name.lower() in row_lower and (
                        not last_name or last_name.lower() in row_lower
                    ):
                        best_id = entry["id"]
                        break
                    # Fallback: partial term match
                    if term_lower in row_lower:
                        best_id = entry["id"]
                        break

                if best_id is not None:
                    break

                # Stop if we've passed a full page with no rows (empty = past last page)
                if len(rows) == 0:
                    break

            if best_id is None:
                ctx.close()
                return {
                    "found": False,
                    "reason": "no_match",
                    "search_term": search_term,
                    "date": date_str,
                }

            # ---- Fetch order detail ----
            detail = _parse_order_detail(page, best_id)
            ctx.close()

            return {"found": True, **detail}

    except Exception as exc:
        return {"found": False, "reason": "error", "detail": str(exc)}


def main() -> None:
    if len(sys.argv) < 3:
        print(
            'Usage: python parbrink_customer_order_lookup.py "<customer name>" <M/D/YYYY>',
            file=sys.stderr,
        )
        sys.exit(1)

    search_term = sys.argv[1]
    date_str = sys.argv[2]

    result = lookup(search_term, date_str)
    print(json.dumps(result, indent=2))
    if not result.get("found") and result.get("reason") == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
