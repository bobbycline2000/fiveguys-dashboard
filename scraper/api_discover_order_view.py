#!/usr/bin/env python3
"""
Capture the vendor order detail by navigating to it via the 'View' URL
pattern. The vendor order list has urls[0] with linkType='VIEW', pk='4578108',
status='3', locationId='13969', orderType='VO'.

CrunchTime typically opens detail via a hash-based route or by clicking the
View link which fires the actioncolumn handler. This script tries to call the
exact View action for the grid row.

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
        if req_body and len(req_body) < 300:
            print(f"    req: {req_body}", flush=True)
    except Exception as exc:
        print(f"  capture err: {exc}", file=sys.stderr)

async def do_login_and_navigate(page):
    print("Logging in and navigating to Purchasing Overview...")
    await page.goto(NETCHEF_BASE, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_selector('input[type="text"]', timeout=30000)
    await page.fill('input[type="text"]', USERNAME)
    await page.fill('input[type="password"]', PASSWORD)
    await page.keyboard.press("Enter")
    try: await page.wait_for_load_state("networkidle", timeout=30000)
    except PlaywrightTimeout: pass

    # Select location
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
    await asyncio.sleep(4)

    # Click Purchasing Overview
    await page.evaluate("""
        (() => {
            if (typeof Ext === 'undefined') return;
            for (const btn of Ext.ComponentQuery.query('button')) {
                try {
                    const txt = (btn.getText && btn.getText()) || btn.text || '';
                    if (/menu|nav/i.test(txt) || (btn.iconCls && /menu|hamburger/i.test(btn.iconCls))) {
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
    result = await page.evaluate("""
        (() => {
            if (typeof Ext === 'undefined') return 'no Ext';
            const target = 'Purchasing Overview';
            const all = Ext.ComponentQuery.query('menuitem, treeitem, treelistitem, button');
            for (const c of all) {
                let txt = '';
                try { txt = (c.getText && c.getText()) || c.text || ''; } catch(e) {}
                if (String(txt).trim() !== target) continue;
                try { if (c.handler && typeof c.handler === 'function') { c.handler.call(c.scope || c, c); return 'handler-fn'; } } catch(e) {}
                try { if (c.click) { c.click(); return 'c.click'; } } catch(e) {}
                try { if (c.fireEvent) { c.fireEvent('click', c, null); return 'fireEvent'; } } catch(e) {}
                try { const el = c.getEl && c.getEl(); if (el) { el.dom.click(); return 'el.dom.click'; } } catch(e) {}
                return 'matched-but-no-fire';
            }
            return 'no-match';
        })()
    """)
    print(f"Purchasing Overview click: {result}")
    await page.wait_for_timeout(6000)
    try: await page.wait_for_load_state("networkidle", timeout=12000)
    except PlaywrightTimeout: pass
    print(f"Purchasing Overview loaded. Endpoints so far: {len(captured)}")

async def try_all_click_methods(page, vendor_order_id):
    """Exhaustive attempt to open the View detail for a vendor order."""
    result = await page.evaluate(f"""
        (() => {{
            if (typeof Ext === 'undefined') return 'no Ext';
            const targetId = {vendor_order_id};

            // Find the grid with vendor orders
            const grids = Ext.ComponentQuery.query('grid, gridpanel');
            for (const grid of grids) {{
                const store = grid.getStore && grid.getStore();
                if (!store || !store.getCount()) continue;
                let record = null;
                store.each(function(r) {{
                    const d = r.getData();
                    if (d.vendorOrderId === targetId) {{ record = r; return false; }}
                }});
                if (!record) continue;

                const idx = store.indexOf(record);
                const view = grid.getView && grid.getView();

                // Method A: actioncolumn item[0].handler
                const cols = grid.getColumns && grid.getColumns() || [];
                for (const col of cols) {{
                    if (col.xtype === 'actioncolumn' || (col.isXType && col.isXType('actioncolumn'))) {{
                        const items = col.items || [];
                        if (items[0] && items[0].handler) {{
                            try {{
                                items[0].handler(view, idx, record, col, idx, new Event('click'));
                                return 'actioncol-item0-handler';
                            }} catch(e) {{ return 'actioncol-err:' + e; }}
                        }}
                    }}
                }}

                // Method B: fire itemdblclick
                try {{
                    grid.fireEvent('itemdblclick', view, record, null, idx, new Event('dblclick'));
                    return 'itemdblclick-fired';
                }} catch(e) {{}}

                // Method C: find the View link anchor in the row node and click it
                try {{
                    const node = view && view.getNode && view.getNode(idx);
                    if (node) {{
                        const anchors = node.querySelectorAll('a[data-qtip="View"], a.x-action-col-icon, .x-action-col-icon');
                        if (anchors.length > 0) {{
                            anchors[0].click();
                            return 'anchor-dom-click: ' + anchors[0].outerHTML.substring(0, 100);
                        }}
                        // Try any link in the action cell
                        const actionCell = node.querySelector('.x-action-col-cell');
                        if (actionCell) {{
                            const icons = actionCell.querySelectorAll('img, span, a');
                            if (icons.length > 0) {{
                                icons[0].click();
                                return 'action-cell-icon-click';
                            }}
                            actionCell.click();
                            return 'action-cell-click';
                        }}
                    }}
                }} catch(e) {{}}

                // Method D: use the urls field from the record
                try {{
                    const urls = record.get('urls');
                    if (urls && urls.length > 0) {{
                        const u = urls[0];
                        // Try to navigate using the App routing
                        if (Ext.History) {{
                            Ext.History.add('purchasingMenu~vendororder~' + u.pk);
                            return 'history-add';
                        }}
                        if (NCApp && NCApp.getController) {{
                            return 'NCApp-exists';
                        }}
                    }}
                }} catch(e) {{}}

                return 'record-found-all-methods-failed-idx:' + idx;
            }}
            return 'order-not-found-in-any-grid';
        }})()
    """)
    return result

async def main():
    global phase
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        page.on("response", lambda r: asyncio.create_task(on_response(r)))
        try:
            phase = "setup"
            await do_login_and_navigate(page)

            vendor_order_id = 4578108
            print(f"\n=== Trying all click methods on order {vendor_order_id} ===")

            phase = "order_detail"
            result = await try_all_click_methods(page, vendor_order_id)
            print(f"Result: {result}")
            await page.wait_for_timeout(5000)
            try: await page.wait_for_load_state("networkidle", timeout=12000)
            except PlaywrightTimeout: pass

            # Check page text for any detail view indicators
            page_text = await page.evaluate("() => document.body.innerText.substring(0, 2000)")
            print(f"\nPage text snippet: {page_text[:500]}")

            # Print detail-phase endpoints
            print(f"\n=== Endpoints in 'order_detail' phase ===")
            detail_eps = {url: e for url, e in captured.items() if e.get('phase') == 'order_detail'}
            print(f"New endpoints: {len(detail_eps)}")
            for url, entry in detail_eps.items():
                path = url.replace(NETCHEF_BASE, "")
                print(f"  [{entry['method']}] {entry['status']} ({entry['response_full_length']}b) -- {path[:110]}")
                if entry.get('request_body'):
                    print(f"    body: {entry['request_body'][:300]}")
                if entry['response_full_length'] > 50:
                    print(f"    resp: {entry['response_truncated'][:400]}")

            # Try hash navigation to force the detail view
            print(f"\n=== Trying hash-based navigation for order {vendor_order_id} ===")
            for hash_pattern in [
                f"purchasingMenu~vendororder~{vendor_order_id}",
                f"purchasingMenu~vendororder~view~{vendor_order_id}",
                f"purchasingMenu~vendororderdetail~{vendor_order_id}",
                f"NCVendorOrderDetail~{vendor_order_id}",
            ]:
                old_count = len(captured)
                await page.evaluate(f"window.location.hash = '#{hash_pattern}'")
                await page.wait_for_timeout(3000)
                try: await page.wait_for_load_state("networkidle", timeout=8000)
                except PlaywrightTimeout: pass
                new_count = len(captured)
                new_eps = new_count - old_count
                print(f"  #{hash_pattern}: +{new_eps} endpoints")
                if new_eps > 0:
                    for url, entry in list(captured.items())[-new_eps:]:
                        path = url.replace(NETCHEF_BASE, "")
                        print(f"    [{entry['method']}] {entry['status']} ({entry['response_full_length']}b) -- {path}")
                        if entry.get('request_body'):
                            print(f"      body: {entry['request_body'][:200]}")

            # Save
            out = DATA_DIR / "ct_order_view_discovery.json"
            out.write_text(json.dumps(captured, indent=2, default=str))
            print(f"\nTotal captured: {len(captured)} endpoints")
            print(f"Saved to: {out}")

            cookies = await context.cookies()
            (DATA_DIR / "ct_cookies.json").write_text(json.dumps(cookies, indent=2))

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
