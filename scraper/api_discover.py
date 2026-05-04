#!/usr/bin/env python3
"""
CrunchTime / NetChef internal-API discovery.

Reuses the proven Playwright login flow from main.py, then hooks page.on('response')
to capture every JSON XHR while the user (us, scripted) navigates the dashboard and
adjacent pages. Dumps:
  - data/ct_api_endpoints.json  — {url: {method, status, request_body, response_body_truncated, headers}}
  - data/ct_cookies.json        — session cookies from the browser context (for cURL replay)
  - data/ct_storage_state.json  — full Playwright storage state (cookies + localStorage)

Run: python scraper/api_discover.py
Reads creds from .env (CRUNCHTIME_USERNAME / CRUNCHTIME_PASSWORD) or env vars.
"""

import asyncio, json, os, re, sys
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# Windows cp1252 console — force UTF-8 stdout
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT     = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

NETCHEF_BASE = "https://fiveguysfr77.net-chef.com"

# Load creds from .env if env vars not set
if not os.environ.get("CRUNCHTIME_USERNAME"):
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

USERNAME = os.environ.get("CRUNCHTIME_USERNAME", "")
PASSWORD = os.environ.get("CRUNCHTIME_PASSWORD", "")

if not USERNAME or not PASSWORD:
    print("FATAL: CRUNCHTIME_USERNAME / CRUNCHTIME_PASSWORD not set", file=sys.stderr)
    sys.exit(2)

print(f"Discovery starting — user={USERNAME}, base={NETCHEF_BASE}")

# ─── Capture state ────────────────────────────────────────────────────────────
captured = {}  # url -> entry

def is_interesting(url: str, content_type: str) -> bool:
    """Filter for the endpoints we care about."""
    if not url.startswith(NETCHEF_BASE):
        return False
    if "/resource/" not in url and "/api/" not in url:
        return False
    if not content_type:
        return False
    if "json" not in content_type.lower():
        return False
    return True


async def on_response(response):
    try:
        url = response.url
        ct = response.headers.get("content-type", "")
        if not is_interesting(url, ct):
            return
        # Strip _dc cache-buster query for dedup
        clean_url = re.sub(r"[&?]_dc=\d+", "", url)
        if clean_url in captured:
            return
        try:
            body = await response.text()
        except Exception:
            body = "<could not read body>"
        request = response.request
        try:
            req_body = request.post_data
        except Exception:
            req_body = None
        captured[clean_url] = {
            "method": request.method,
            "status": response.status,
            "content_type": ct,
            "request_body": req_body,
            "response_truncated": body[:1500],
            "response_full_length": len(body),
        }
        print(f"  [{request.method}] {response.status} — {clean_url[:120]}")
    except Exception as exc:
        print(f"  capture error: {exc}", file=sys.stderr)


# ─── Login (lifted from main.py, simplified) ──────────────────────────────────
async def do_login(page):
    print(f"-> goto {NETCHEF_BASE}")
    await page.goto(NETCHEF_BASE, wait_until="domcontentloaded", timeout=30_000)
    await page.wait_for_selector('input[type="text"]', timeout=30_000)
    await page.fill('input[type="text"]', USERNAME)
    await page.fill('input[type="password"]', PASSWORD)
    await page.keyboard.press("Enter")
    print("-> submitted credentials, waiting for navigation")
    try:
        await page.wait_for_load_state("networkidle", timeout=45_000)
    except PlaywrightTimeout:
        pass
    print(f"  post-login URL: {page.url}")
    if "login" in page.url.lower():
        raise RuntimeError("Still on login page — bad creds?")


async def _click_sign_in(page) -> bool:
    for sel in [
        'button:has-text("Sign In")', 'a:has-text("Sign In")',
        '.x-btn:has-text("Sign In")', '.x-btn-inner:has-text("Sign In")',
        'div.x-button:has-text("Sign In")', 'div.x-button',
        'input[value="Sign In"]',
    ]:
        try:
            loc = page.locator(sel)
            if await loc.count() and await loc.first.is_visible():
                await loc.first.click(timeout=3000)
                print(f"  clicked Sign In via {sel}")
                return True
        except Exception:
            continue
    return False


async def select_location(page):
    print("-> selecting KY-2065")
    try:
        await page.wait_for_load_state("networkidle", timeout=30_000)
    except PlaywrightTimeout:
        pass
    try:
        await page.wait_for_function(
            "() => document.body.innerText.trim().length > 100",
            timeout=30_000, polling=1_000,
        )
    except PlaywrightTimeout:
        pass

    await page.screenshot(path=str(DATA_DIR / "api_discover_picker.png"))
    body_len = await page.evaluate("() => document.body.innerText.trim().length")
    print(f"  picker body text length: {body_len}")

    # Method 1: ExtJS programmatic (proven path from main.py)
    print("  trying ExtJS programmatic select")
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
                    if (found) {
                        combo.setValue(found);
                        combo.fireEvent('select', combo, [found]);
                        return 'selected: ' + JSON.stringify(found.getData()).substring(0, 100);
                    }
                }
                return 'combo count=' + combos.length + ' no 2065 match';
            } catch(e) { return 'error: ' + e.message; }
        })()
    """)
    print(f"  ExtJS result: {result}")
    if result and result.startswith("selected:"):
        await page.wait_for_timeout(1000)
        await _click_sign_in(page)

    # Wait for nav off ChooseLocation
    try:
        await page.wait_for_function(
            "() => !window.location.href.includes('ChooseLocation')",
            timeout=20_000,
        )
    except PlaywrightTimeout:
        # Method 2: type filter
        print("  ExtJS path didn't navigate — trying type-filter fallback")
        for sel in ["input.x-form-field", "input.x-form-text", 'input[type="text"]']:
            try:
                loc = page.locator(sel)
                if await loc.count():
                    await loc.first.click()
                    await page.wait_for_timeout(800)
                    await page.keyboard.type("2065", delay=100)
                    await page.wait_for_timeout(2000)
                    break
            except Exception:
                continue
        # Click any visible item that contains 2065
        try:
            await page.evaluate("""
                (() => {
                    for (const el of document.querySelectorAll('li, div, span, td, [role="option"]')) {
                        const t = el.textContent.trim();
                        if (t.includes('2065') && t.length < 80) {
                            el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                            el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                            el.click();
                            return t;
                        }
                    }
                    return null;
                })()
            """)
        except Exception:
            pass
        await page.wait_for_timeout(1000)
        await _click_sign_in(page)

    try:
        await page.wait_for_function(
            "() => !window.location.href.includes('ChooseLocation')",
            timeout=20_000,
        )
    except PlaywrightTimeout:
        print("  WARN: still on ChooseLocation")
    print(f"  post-location URL: {page.url}")


async def warm_up(page):
    """Click around to fire as many XHR endpoints as possible."""
    print("-> warm-up: dashboard -> idle wait")
    try:
        await page.wait_for_load_state("networkidle", timeout=30_000)
    except PlaywrightTimeout:
        pass
    await asyncio.sleep(5)

    # Try clicking through a few sidebar items to surface report endpoints.
    nav_targets = [
        # ExtJS modern sidebar — try by visible text
        'span:has-text("Reports")', 'a:has-text("Reports")',
        'span:has-text("Inventory")', 'a:has-text("Inventory")',
        'span:has-text("Labor")', 'a:has-text("Labor")',
    ]
    seen_clicks = 0
    for sel in nav_targets:
        try:
            loc = page.locator(sel)
            if await loc.count():
                await loc.first.click(timeout=3000)
                print(f"  clicked nav: {sel}")
                seen_clicks += 1
                await asyncio.sleep(3)
                try:
                    await page.wait_for_load_state("networkidle", timeout=10_000)
                except PlaywrightTimeout:
                    pass
        except Exception as exc:
            print(f"  nav skip {sel}: {exc}")
        if seen_clicks >= 3:
            break

    # Also: try direct hash routes that the modern.ct app honors.
    # NEVER hit /ncext/index.ct — known to log out per 2026-04-20 handoff.
    hash_routes = [
        f"{NETCHEF_BASE}/ncext/modern.ct#NCDashboard",
        f"{NETCHEF_BASE}/ncext/modern.ct#NCReports",
    ]
    for url in hash_routes:
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15_000)
            print(f"  goto {url}")
            await asyncio.sleep(4)
            try:
                await page.wait_for_load_state("networkidle", timeout=10_000)
            except PlaywrightTimeout:
                pass
        except Exception as exc:
            print(f"  goto skip {url}: {exc}")


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        page.on("response", lambda r: asyncio.create_task(on_response(r)))

        try:
            await do_login(page)
            await select_location(page)
            await warm_up(page)
        except Exception as exc:
            print(f"FATAL during navigation: {exc}", file=sys.stderr)
            await page.screenshot(path=str(DATA_DIR / "api_discover_error.png"))
            raise
        finally:
            # Persist cookies + storage state for cURL/requests replay
            cookies = await context.cookies()
            (DATA_DIR / "ct_cookies.json").write_text(json.dumps(cookies, indent=2))
            await context.storage_state(path=str(DATA_DIR / "ct_storage_state.json"))
            (DATA_DIR / "ct_api_endpoints.json").write_text(
                json.dumps(captured, indent=2, default=str)
            )
            print(f"\n-> captured {len(captured)} unique JSON endpoints")
            print(f"-> wrote ct_api_endpoints.json, ct_cookies.json, ct_storage_state.json")
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
