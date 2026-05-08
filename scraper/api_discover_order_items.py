#!/usr/bin/env python3
"""
Extended purchasing discovery: opens Purchasing Overview, then tries to
click into a specific vendor order to capture the line-item API endpoint.

Builds on api_discover_purchasing.py pattern which successfully navigated
the purchasing screens.

2026-05-07 — CT Professor.
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

captured = {}
phase = "warmup"

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
        is_new = clean not in captured
        captured[clean] = {
            "method": request.method, "status": response.status, "phase": phase,
            "request_body": req_body,
            "response_truncated": body[:4000],
            "response_full_length": len(body),
        }
        path = clean.replace(NETCHEF_BASE, "")
        marker = "NEW" if is_new else "   "
        print(f"  [{marker}] [{request.method}] {response.status} ({len(body):>7}b) -- {path[:110]}", flush=True)
        if req_body and len(req_body) < 400:
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
    for sel in ['button:has-text("Sign In")', '.x-btn:has-text("Sign In")', 'div.x-button:has-text("Sign In")']:
        try:
            loc = page.locator(sel)
            if await loc.count() and await loc.first.is_visible():
                await loc.first.click(timeout=3000); break
        except Exception: continue
    try: await page.wait_for_function("() => !window.location.href.includes('ChooseLocation')", timeout=15000)
    except PlaywrightTimeout: pass

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
                try {{ if (c.handler && typeof c.handler === 'function') {{ c.handler.call(c.scope || c, c); return 'handler-fn'; }} }} catch(e) {{}}
                try {{ if (c.click) {{ c.click(); return 'c.click'; }} }} catch(e) {{}}
                try {{ if (c.fireEvent) {{ c.fireEvent('click', c, null); return 'fireEvent'; }} }} catch(e) {{}}
                try {{ const el = c.getEl && c.getEl(); if (el) {{ el.dom.click(); return 'el.dom.click'; }} }} catch(e) {{}}
                return 'matched-but-no-fire';
            }}
            return 'no-match';
        }})()
    """)

async def click_vendor_order_in_grid(page, vendor_order_id):
    """After Purchasing Overview loads, click into a specific order."""
    return await page.evaluate(f"""
        (() => {{
            if (typeof Ext === 'undefined') return 'no Ext';
            const targetId = {vendor_order_id};
            const grids = Ext.ComponentQuery.query('grid, gridpanel');
            console.log('Grids found: ' + grids.length);
            for (const grid of grids) {{
                const store = grid.getStore && grid.getStore();
                if (!store || !store.getCount()) continue;
                console.log('Grid store count: ' + store.getCount());
                let record = null;
                store.each(function(r) {{
                    const d = r.getData();
                    if (d.vendorOrderId === targetId || d.id === targetId) {{
                        record = r;
                        return false;
                    }}
                }});
                if (!record) continue;
                console.log('Found record for order ' + targetId);

                // Method 1: fire itemclick
                const view = grid.getView && grid.getView();
                if (view) {{
                    grid.fireEvent('itemclick', view, record, null, 0, {{target: view.getEl() && view.getEl().dom}});
                    return 'itemclick-fired';
                }}

                // Method 2: find action column and fire its handler
                const cols = grid.getColumns && grid.getColumns() || [];
                for (const col of cols) {{
                    if (col.xtype === 'actioncolumn' || (col.isXType && col.isXType('actioncolumn'))) {{
                        const items = col.items || [];
                        for (const item of items) {{
                            if (item.handler && (item.tooltip === 'View' || item.iconCls && /view|eye/i.test(item.iconCls))) {{
                                item.handler.call(grid, view, 0, record, col, 0, null);
                                return 'action-view-handler';
                            }}
                        }}
                        if (items.length > 0 && items[0].handler) {{
                            items[0].handler.call(grid, view, 0, record, col, 0, null);
                            return 'action-first-handler';
                        }}
                    }}
                }}
                return 'record-found-no-click-method';
            }}
            return 'order-not-in-grid';
        }})()
    """)

async def try_dom_click_view_link(page, vendor_order_id):
    """Try clicking the View link in the DOM for a specific order."""
    # Get page content to find view links
    content = await page.evaluate("""
        (() => {
            const links = document.querySelectorAll('a, button, span');
            const results = [];
            for (const el of links) {
                const text = el.textContent.trim();
                if (text === 'View' || text === 'VIEW') {
                    const rect = el.getBoundingClientRect();
                    results.push({text, x: rect.x + rect.width/2, y: rect.y + rect.height/2, tag: el.tagName});
                }
            }
            return results;
        })()
    """)
    print(f"  'View' links in DOM: {content}")
    if content:
        # Click the first View link
        first = content[0]
        await page.mouse.click(first['x'], first['y'])
        return f"dom-clicked-view at ({first['x']:.0f},{first['y']:.0f})"
    return "no-view-links-in-dom"

async def main():
    global phase
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        page.on("response", lambda r: asyncio.create_task(on_response(r)))
        try:
            phase = "login"
            await do_login(page)
            await select_location(page)

            phase = "warmup"
            try: await page.wait_for_load_state("networkidle", timeout=20000)
            except PlaywrightTimeout: pass
            await asyncio.sleep(3)

            # Open Purchasing Overview
            phase = "purchasing_overview"
            print(f"\n=== Opening Purchasing Overview ===")
            await open_all_menus(page)
            result = await click_menuitem(page, "Purchasing Overview")
            print(f"Menu click: {result}")
            await page.wait_for_timeout(5000)
            try: await page.wait_for_load_state("networkidle", timeout=12000)
            except PlaywrightTimeout: pass
            print(f"Endpoints after Purchasing Overview: {len(captured)}")

            # Check what's in the grid
            grid_info = await page.evaluate("""
                (() => {
                    if (typeof Ext === 'undefined') return 'no Ext';
                    const grids = Ext.ComponentQuery.query('grid, gridpanel');
                    return grids.map(g => {
                        const s = g.getStore && g.getStore();
                        return {
                            xtype: g.xtype,
                            count: s ? s.getCount() : 0,
                            fields: s && s.getCount() > 0 ? Object.keys(s.getAt(0).getData()).slice(0,5) : []
                        };
                    });
                })()
            """)
            print(f"Grids in DOM: {json.dumps(grid_info)}")

            # Try to click into a vendor order
            phase = "order_detail"
            vendor_order_id = 4578108
            print(f"\n=== Clicking View on order {vendor_order_id} ===")
            result = await click_vendor_order_in_grid(page, vendor_order_id)
            print(f"Click result: {result}")
            await page.wait_for_timeout(4000)
            try: await page.wait_for_load_state("networkidle", timeout=10000)
            except PlaywrightTimeout: pass

            if "not-in-grid" in result or "no Ext" in result:
                print("Order not in grid yet — trying DOM approach...")
                result2 = await try_dom_click_view_link(page, vendor_order_id)
                print(f"DOM result: {result2}")
                await page.wait_for_timeout(4000)
                try: await page.wait_for_load_state("networkidle", timeout=10000)
                except PlaywrightTimeout: pass

            # Look for new endpoints after clicking
            print(f"\nTotal endpoints: {len(captured)}")
            print("\nEndpoints captured in 'order_detail' phase:")
            for url, entry in captured.items():
                if entry.get('phase') == 'order_detail':
                    path = url.replace(NETCHEF_BASE, "")
                    print(f"  [{entry['method']}] {entry['status']} ({entry['response_full_length']}b) -- {path[:110]}")
                    if entry.get('request_body'):
                        print(f"    body: {entry['request_body'][:300]}")
                    if entry['response_full_length'] > 100:
                        print(f"    resp: {entry['response_truncated'][:400]}")

            # Save
            out = DATA_DIR / "ct_order_items_discovery.json"
            out.write_text(json.dumps(captured, indent=2, default=str))
            print(f"\nSaved to: {out}")

            cookies = await context.cookies()
            (DATA_DIR / "ct_cookies.json").write_text(json.dumps(cookies, indent=2))

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
