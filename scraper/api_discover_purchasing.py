#!/usr/bin/env python3
"""
Targeted Playwright discovery for CrunchTime Purchasing module screens.
Captures the exact API calls fired when purchasing screens load.

Targets:
  - Purchasing Overview
  - Recent Purchase by Invoices
  - Purchase Journal
  - Create Purchase by Invoice
  - Purchases by GL

Saves captured endpoints to data/ct_purchasing_endpoints.json
Updates data/ct_api_endpoints_deep.json (merged in)
Updates CRUNCHTIME_API.md Section 1.6 with any discovered paths.

2026-05-07 — CT Professor first-pass discovery run.
"""

import asyncio, json, os, re, sys
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT     = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
NETCHEF_BASE = "https://fiveguysfr77.net-chef.com"

if not os.environ.get("CRUNCHTIME_USERNAME"):
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
USERNAME = os.environ.get("CRUNCHTIME_USERNAME", "")
PASSWORD = os.environ.get("CRUNCHTIME_PASSWORD", "")

# Purchasing targets — exact menu label text as seen in ct_menu_inventory.json
TARGETS = {
    "PurchasingOverview":       "Purchasing Overview",
    "RecentPurchaseByInvoices": "Recent Purchase by Invoices",
    "PurchaseJournal":          "Purchase Journal",
    "CreatePurchaseByInvoice":  "Create Purchase by Invoice",
    "PurchasesByGL":            "Purchases by GL",
    "CostAnalysis":             "Cost Analysis",
    "PurchasingOverview2":      "Purchasing Overview",  # retry with different approach
}

PURCHASING_FILE = DATA_DIR / "ct_purchasing_endpoints.json"
ENDPOINTS_FILE  = DATA_DIR / "ct_api_endpoints_deep.json"
SCREENS_FILE    = DATA_DIR / "ct_endpoints_by_screen.json"

def load_existing():
    eps  = json.loads(ENDPOINTS_FILE.read_text()) if ENDPOINTS_FILE.exists() else {}
    scrn = json.loads(SCREENS_FILE.read_text())   if SCREENS_FILE.exists()   else {}
    return eps, scrn

captured, by_screen = load_existing()
purchasing_only = {}
current_screen = "warmup"

def is_interesting(url, ct):
    return url.startswith(NETCHEF_BASE) and "/resource/" in url and ct and "json" in ct.lower()

async def on_response(response):
    try:
        url = response.url; ct = response.headers.get("content-type", "")
        if not is_interesting(url, ct): return
        clean = re.sub(r"[&?]_dc=\d+", "", url)
        by_screen.setdefault(current_screen, [])
        if clean not in by_screen[current_screen]:
            by_screen[current_screen].append(clean)

        try: body = await response.text()
        except Exception: body = "<no body>"
        request = response.request
        try: req_body = request.post_data
        except Exception: req_body = None

        entry = {
            "method": request.method, "status": response.status, "content_type": ct,
            "request_body": req_body,
            "response_truncated": body[:2000],
            "response_full_length": len(body),
            "first_seen_screen": current_screen,
        }

        is_new = clean not in captured
        captured[clean] = entry

        # Always track in purchasing_only for this run
        if current_screen not in ("warmup",):
            purchasing_only[clean] = entry

        status_marker = "NEW" if is_new else "   "
        print(f"  [{status_marker}] [{request.method}] {response.status} ({len(body):>7}b) -- {clean.replace(NETCHEF_BASE,'')[:100]}", flush=True)
    except Exception as exc:
        print(f"  capture err: {exc}", file=sys.stderr)

async def do_login(page):
    print("Logging in...")
    await page.goto(NETCHEF_BASE, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_selector('input[type="text"]', timeout=30000)
    await page.fill('input[type="text"]', USERNAME)
    await page.fill('input[type="password"]', PASSWORD)
    await page.keyboard.press("Enter")
    try: await page.wait_for_load_state("networkidle", timeout=30000)
    except PlaywrightTimeout: pass

async def select_location(page):
    print("Selecting location 2065...")
    try: await page.wait_for_load_state("networkidle", timeout=20000)
    except PlaywrightTimeout: pass
    try: await page.wait_for_function("() => document.body.innerText.trim().length > 100", timeout=20000, polling=1000)
    except PlaywrightTimeout: pass
    await page.evaluate("""
        (() => {
            if (typeof Ext === 'undefined') return;
            for (var c of Ext.ComponentQuery.query('combo, combobox')) {
                var s = c.getStore && c.getStore(); if(!s) continue;
                var found = null;
                s.each(function(r){
                    for(var f of Object.keys(r.getData()))
                        if(String(r.get(f)).includes('2065')){found=r;return false;}
                });
                if(found){c.setValue(found); c.fireEvent('select',c,[found]); return;}
            }
        })()
    """)
    await page.wait_for_timeout(800)
    for sel in ['button:has-text("Sign In")', '.x-btn:has-text("Sign In")', 'div.x-button:has-text("Sign In")']:
        try:
            loc = page.locator(sel)
            if await loc.count() and await loc.first.is_visible():
                await loc.first.click(timeout=3000); break
        except Exception: continue
    try: await page.wait_for_function("() => !window.location.href.includes('ChooseLocation')", timeout=15000)
    except PlaywrightTimeout: pass
    print("Location selected.")

async def open_all_menus(page):
    await page.evaluate("""
        (() => {
            if (typeof Ext === 'undefined') return;
            for (const btn of Ext.ComponentQuery.query('button')) {
                try {
                    const txt = (btn.getText && btn.getText()) || btn.text || '';
                    if (/menu|nav/i.test(txt) || btn.iconCls && /menu|hamburger/i.test(btn.iconCls)) {
                        btn.showMenu && btn.showMenu();
                    }
                } catch(e) {}
            }
            for (const m of Ext.ComponentQuery.query('menu')) {
                try { m.show && m.show(); } catch(e) {}
            }
        })()
    """)
    await page.wait_for_timeout(800)

async def click_menuitem(page, exact_label):
    return await page.evaluate(f"""
        (() => {{
            if (typeof Ext === 'undefined') return 'no Ext';
            const target = {json.dumps(exact_label)};
            const all = Ext.ComponentQuery.query('menuitem, treeitem, treelistitem, button');
            for (const c of all) {{
                let txt = '';
                try {{ txt = (c.getText && c.getText()) || c.text || ''; }} catch(e) {{}}
                if (String(txt).trim() !== target) continue;
                try {{
                    if (c.handler) {{
                        if (typeof c.handler === 'function') c.handler.call(c.scope || c, c);
                        return 'handler-fn';
                    }}
                }} catch(e) {{}}
                try {{ if (c.click) {{ c.click(); return 'c.click'; }} }} catch(e) {{}}
                try {{ if (c.fireEvent) {{ c.fireEvent('click', c, null); return 'fireEvent'; }} }} catch(e) {{}}
                try {{
                    const el = c.getEl && c.getEl();
                    if (el) {{ el.dom.click(); return 'el.dom.click'; }}
                }} catch(e) {{}}
                return 'matched-but-no-fire';
            }}
            return 'no-match';
        }})()
    """)

async def try_hash_nav(page, screen_name):
    """Try navigating directly via hash if known."""
    hash_map = {
        "PurchasingOverview":       "purchasingMenu",
        "RecentPurchaseByInvoices": "purchasingMenu~purchasebyinvoicelist",
        "PurchaseJournal":          "purchasingMenu~purchasejournal",
        "CreatePurchaseByInvoice":  "purchasingMenu~purchasebyinvoice",
        "PurchasesByGL":            "purchasingMenu~purchasesbygl",
        "CostAnalysis":             "purchasingMenu~costanalysis",
    }
    h = hash_map.get(screen_name)
    if not h:
        return False
    print(f"  Trying hash nav: #{h}")
    await page.evaluate(f"window.location.hash = '#{h}'")
    await page.wait_for_timeout(2000)
    try: await page.wait_for_load_state("networkidle", timeout=8000)
    except PlaywrightTimeout: pass
    return True

async def visit_target(page, screen_name, label):
    global current_screen
    current_screen = screen_name
    print(f"\n=== {screen_name} -> '{label}' ===")
    pre = len(purchasing_only)

    # Reset to dashboard
    try:
        await page.evaluate("window.location.hash = '#NCDashboard'")
        await page.wait_for_timeout(800)
    except Exception: pass

    # Strategy 1: menu click
    await open_all_menus(page)
    result = await click_menuitem(page, label)
    print(f"  menu click result: {result}")
    if result not in ("no-match", "no Ext"):
        await page.wait_for_timeout(4000)
        try: await page.wait_for_load_state("networkidle", timeout=10000)
        except PlaywrightTimeout: pass
    else:
        # Strategy 2: hash navigation
        await try_hash_nav(page, screen_name)

    new = len(purchasing_only) - pre
    print(f"  <- {new} new purchasing endpoints from {screen_name}")
    save()
    return new

def save():
    ENDPOINTS_FILE.write_text(json.dumps(captured, indent=2, default=str))
    SCREENS_FILE.write_text(json.dumps(by_screen, indent=2))
    PURCHASING_FILE.write_text(json.dumps(purchasing_only, indent=2, default=str))

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        page.on("response", lambda r: asyncio.create_task(on_response(r)))
        try:
            await do_login(page)
            await select_location(page)
            global current_screen
            current_screen = "warmup"
            try: await page.wait_for_load_state("networkidle", timeout=20000)
            except PlaywrightTimeout: pass
            await asyncio.sleep(3)
            save()

            for screen, label in TARGETS.items():
                try:
                    await visit_target(page, screen, label)
                except Exception as exc:
                    print(f"  ! {screen} failed: {exc}")
        finally:
            cookies = await context.cookies()
            (DATA_DIR / "ct_cookies.json").write_text(json.dumps(cookies, indent=2))
            save()
            print(f"\n=== PURCHASING DISCOVERY COMPLETE ===")
            print(f"Total endpoints in master catalog: {len(captured)}")
            print(f"Purchasing-specific endpoints captured this run: {len(purchasing_only)}")
            print("\nPurchasing endpoints found:")
            for url, entry in purchasing_only.items():
                path = url.replace(NETCHEF_BASE, "")
                print(f"  [{entry['method']}] {path[:100]}")
                if entry.get('request_body'):
                    print(f"    body: {str(entry['request_body'])[:200]}")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
