#!/usr/bin/env python3
"""
Deep discovery of the Cost Analysis data endpoint.
Opens the Cost Analysis screen, selects a date range, and captures the API call.

2026-05-07 — CT Professor targeted capture.
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

captured_new = {}

def is_interesting(url, ct):
    return url.startswith(NETCHEF_BASE) and "/resource/" in url and ct and "json" in ct.lower()

async def on_response(response):
    try:
        url = response.url; ct = response.headers.get("content-type", "")
        if not is_interesting(url, ct): return
        clean = re.sub(r"[&?]_dc=\d+", "", url)
        try: body = await response.text()
        except Exception: body = "<no body>"
        request = response.request
        try: req_body = request.post_data
        except Exception: req_body = None

        entry = {
            "method": request.method, "status": response.status,
            "request_body": req_body,
            "response_truncated": body[:3000],
            "response_full_length": len(body),
        }
        captured_new[clean] = entry
        path = clean.replace(NETCHEF_BASE, "")
        print(f"  [{request.method}] {response.status} ({len(body):>7}b) -- {path[:110]}", flush=True)
        if req_body and len(req_body) < 500:
            print(f"    req: {req_body}", flush=True)
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
    for sel in ['button:has-text("Sign In")', '.x-btn:has-text("Sign In")']:
        try:
            loc = page.locator(sel)
            if await loc.count() and await loc.first.is_visible():
                await loc.first.click(timeout=3000); break
        except Exception: continue
    try: await page.wait_for_function("() => !window.location.href.includes('ChooseLocation')", timeout=15000)
    except PlaywrightTimeout: pass
    print("Location selected. Waiting for dashboard...")
    await asyncio.sleep(4)

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
                try {{ if (c.handler && typeof c.handler === 'function') {{ c.handler.call(c.scope || c, c); return 'handler-fn'; }} }} catch(e) {{}}
                try {{ if (c.click) {{ c.click(); return 'c.click'; }} }} catch(e) {{}}
                try {{ if (c.fireEvent) {{ c.fireEvent('click', c, null); return 'fireEvent'; }} }} catch(e) {{}}
                try {{ const el = c.getEl && c.getEl(); if (el) {{ el.dom.click(); return 'el.dom.click'; }} }} catch(e) {{}}
                return 'matched-but-no-fire';
            }}
            return 'no-match';
        }})()
    """)

async def select_date_in_costanalysis(page, target_start="01/05/2026"):
    """After Cost Analysis is open, select a date range from the date picker."""
    print(f"\nAttempting to select date range starting {target_start}...")

    # Strategy 1: Find and use the date combo/picker via ExtJS
    result = await page.evaluate(f"""
        (() => {{
            if (typeof Ext === 'undefined') return 'no Ext';
            const target_start = {json.dumps(target_start)};
            // Look for comboboxes that have date data
            const combos = Ext.ComponentQuery.query('combo, combobox, datefield');
            for (const c of combos) {{
                const s = c.getStore && c.getStore();
                if (!s) continue;
                let found = null;
                s.each(function(r) {{
                    const data = r.getData();
                    for (const f of Object.keys(data)) {{
                        if (String(data[f]).includes(target_start.split(' ')[0])) {{
                            found = r;
                            return false;
                        }}
                    }}
                }});
                if (found) {{
                    c.setValue(found);
                    c.fireEvent('select', c, [found]);
                    return 'date-combo-selected';
                }}
                // Try raw value set
                try {{
                    c.setValue(target_start);
                    c.fireEvent('change', c, target_start);
                    return 'date-value-set';
                }} catch(e) {{}}
            }}
            return 'no date combo found';
        }})()
    """)
    print(f"  Date select result: {result}")

    if result == 'no date combo found':
        # Strategy 2: Use the dates endpoint and simulate store select
        print("  Trying store-based date selection...")
        result2 = await page.evaluate(f"""
            (() => {{
                if (typeof Ext === 'undefined') return 'no Ext';
                // Find stores that have startDate data
                const allStores = Ext.data.StoreManager.getRange();
                for (const store of allStores) {{
                    if (!store.getCount()) continue;
                    const first = store.getAt(0);
                    if (!first) continue;
                    const data = first.getData();
                    if (!data.startDate) continue;
                    // This is our date range store
                    let found = null;
                    store.each(function(r) {{
                        if (r.get('startDate') && r.get('startDate').includes('01/05/2026')) {{
                            found = r;
                            return false;
                        }}
                    }});
                    if (found) {{
                        // Find the bound combo
                        const combos = Ext.ComponentQuery.query('combo');
                        for (const c of combos) {{
                            if (c.getStore && c.getStore() === store) {{
                                c.setValue(found);
                                c.fireEvent('select', c, [found]);
                                return 'store-combo-selected';
                            }}
                        }}
                        return 'found-record-but-no-combo';
                    }}
                }}
                return 'no store with startDate';
            }})()
        """)
        print(f"  Store select result: {result2}")

    await page.wait_for_timeout(4000)
    try: await page.wait_for_load_state("networkidle", timeout=10000)
    except PlaywrightTimeout: pass

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        page.on("response", lambda r: asyncio.create_task(on_response(r)))
        try:
            await do_login(page)
            await select_location(page)

            # Navigate to Cost Analysis
            print("\n=== Navigating to Cost Analysis ===")
            result = await click_menuitem(page, "Cost Analysis")
            print(f"Menu click: {result}")
            if result in ("no-match", "no Ext"):
                print("Trying hash navigation...")
                await page.evaluate("window.location.hash = '#purchasingMenu~costanalysis'")
            await page.wait_for_timeout(4000)
            try: await page.wait_for_load_state("networkidle", timeout=10000)
            except PlaywrightTimeout: pass

            print(f"\nEndpoints captured so far: {len(captured_new)}")

            # Now try to interact with the date picker
            await select_date_in_costanalysis(page, "01/05/2026")

            print(f"\nEndpoints after date select: {len(captured_new)}")

            # Print any new endpoints that look like cost analysis data
            print("\nAll captured endpoints:")
            for url, entry in captured_new.items():
                path = url.replace(NETCHEF_BASE, "")
                print(f"  [{entry['method']}] {entry['status']} ({entry['response_full_length']}b) -- {path[:100]}")
                if entry.get('request_body'):
                    print(f"    body: {str(entry['request_body'])[:200]}")
                if entry['response_full_length'] > 500 and 'costanalysis' in path.lower():
                    print(f"    response: {entry['response_truncated'][:300]}")

            # Save the discovery
            out = DATA_DIR / "ct_costanalysis_discovery.json"
            out.write_text(json.dumps(captured_new, indent=2, default=str))
            print(f"\nSaved to: {out}")

            # Also save updated cookies
            cookies = await context.cookies()
            (DATA_DIR / "ct_cookies.json").write_text(json.dumps(cookies, indent=2))

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
