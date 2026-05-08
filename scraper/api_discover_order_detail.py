#!/usr/bin/env python3
"""
Targeted capture: open Purchasing Overview, click into a specific vendor order,
and capture all API calls fired by the detail view.

The goal is to find the line-item endpoint behind each PFG invoice.

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
            "response_truncated": body[:4000],
            "response_full_length": len(body),
        }
        is_new = clean not in captured
        captured[clean] = entry
        path = clean.replace(NETCHEF_BASE, "")
        marker = "NEW" if is_new else "   "
        print(f"  [{marker}] [{request.method}] {response.status} ({len(body):>7}b) -- {path[:110]}", flush=True)
        if req_body and len(req_body) < 300:
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
    print("Location selected. Waiting...")
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

async def click_view_on_order(page, vendor_order_id):
    """Click the 'View' link/button for a specific vendor order in the grid."""
    return await page.evaluate(f"""
        (() => {{
            if (typeof Ext === 'undefined') return 'no Ext';
            const targetId = {vendor_order_id};
            // Find all grid rows and look for our order
            const grids = Ext.ComponentQuery.query('grid, treegrid, gridpanel');
            for (const grid of grids) {{
                const store = grid.getStore && grid.getStore();
                if (!store) continue;
                let found = null;
                store.each(function(r) {{
                    if (r.get('vendorOrderId') === targetId || r.get('id') === targetId) {{
                        found = r;
                        return false;
                    }}
                }});
                if (found) {{
                    // Try to click the row first
                    const view = grid.getView && grid.getView();
                    if (view) {{
                        const node = view.getNode && view.getNode(found);
                        if (node) {{
                            // Look for View link in the row
                            const links = node.querySelectorAll('a, button');
                            for (const link of links) {{
                                if (link.textContent.trim().toLowerCase() === 'view') {{
                                    link.click();
                                    return 'dom-view-click';
                                }}
                            }}
                            // Try clicking any action cell
                            const actionCells = node.querySelectorAll('.x-action-col-cell, .x-grid-cell-action');
                            if (actionCells.length > 0) {{
                                actionCells[0].click();
                                return 'action-cell-click';
                            }}
                        }}
                    }}
                    // Try selecting and double-clicking
                    grid.getSelectionModel && grid.getSelectionModel().select(found);
                    grid.fireEvent('itemdblclick', grid, found, null, null, null);
                    return 'dblclick-fired';
                }}
            }}
            return 'order-not-found-in-grid';
        }})()
    """)

async def simulate_view_click(page, vendor_order_id):
    """Simulate the VIEW action by calling CrunchTime's internal action handler."""
    return await page.evaluate(f"""
        (() => {{
            if (typeof Ext === 'undefined') return 'no Ext';
            const vendorOrderId = {vendor_order_id};
            const locationId = 13969;
            const orderType = 'VO';
            const status = 3;

            // Try to find action column handlers
            const grids = Ext.ComponentQuery.query('grid, gridpanel');
            for (const grid of grids) {{
                const cols = grid.getColumns && grid.getColumns();
                if (!cols) continue;
                for (const col of cols) {{
                    if (col.xtype === 'actioncolumn' || col.isXType && col.isXType('actioncolumn')) {{
                        const store = grid.getStore && grid.getStore();
                        if (!store) continue;
                        let record = null;
                        store.each(function(r) {{
                            if (r.get('vendorOrderId') === vendorOrderId) {{
                                record = r;
                                return false;
                            }}
                        }});
                        if (record && col.items && col.items.length > 0) {{
                            const item = col.items[0];
                            if (item.handler) {{
                                item.handler.call(grid, grid.getView(), 0, record, col, 0, null);
                                return 'action-handler-fired';
                            }}
                        }}
                    }}
                }}
            }}
            return 'no-action-col-found';
        }})()
    """)

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        page.on("response", lambda r: asyncio.create_task(on_response(r)))
        try:
            await do_login(page)
            await select_location(page)

            # Navigate to Purchasing Overview
            print("\n=== Opening Purchasing Overview ===")
            result = await click_menuitem(page, "Purchasing Overview")
            print(f"Menu click: {result}")
            await page.wait_for_timeout(5000)
            try: await page.wait_for_load_state("networkidle", timeout=12000)
            except PlaywrightTimeout: pass

            print(f"\nEndpoints after Purchasing Overview: {len(captured)}")

            # Find vendor order 4578108 (Feb 9 PFG)
            vendor_order_id = 4578108
            print(f"\n=== Clicking View on order {vendor_order_id} ===")
            result = await click_view_on_order(page, vendor_order_id)
            print(f"Click result: {result}")
            await page.wait_for_timeout(4000)
            try: await page.wait_for_load_state("networkidle", timeout=10000)
            except PlaywrightTimeout: pass

            if "not-found" in result or result == "no Ext":
                print("Order not in grid — trying simulate approach...")
                result2 = await simulate_view_click(page, vendor_order_id)
                print(f"Simulate result: {result2}")
                await page.wait_for_timeout(4000)
                try: await page.wait_for_load_state("networkidle", timeout=10000)
                except PlaywrightTimeout: pass

            print(f"\nTotal endpoints captured: {len(captured)}")
            print("\nAll endpoints:")
            for url, entry in captured.items():
                path = url.replace(NETCHEF_BASE, "")
                print(f"  [{entry['method']}] {entry['status']} ({entry['response_full_length']}b) -- {path[:110]}")
                if entry.get('request_body') and len(entry['request_body']) < 300:
                    print(f"    body: {entry['request_body']}")
                # Print response for large non-layout responses
                if entry['response_full_length'] > 200 and not 'layout' in path and not 'configuration' in path:
                    print(f"    resp: {entry['response_truncated'][:300]}")

            out = DATA_DIR / "ct_order_detail_discovery.json"
            out.write_text(json.dumps(captured, indent=2, default=str))
            print(f"\nSaved to: {out}")

            cookies = await context.cookies()
            (DATA_DIR / "ct_cookies.json").write_text(json.dumps(cookies, indent=2))

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
