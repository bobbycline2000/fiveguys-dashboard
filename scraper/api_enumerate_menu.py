#!/usr/bin/env python3
"""
Enumerate the LIVE menu structure in modern.ct — pull every menu item
ExtJS knows about, with its label and any associated handler/route.
This tells us exactly what screen names exist for navigation.

Outputs: data/ct_menu_inventory.json (label, type, handler, depth, parent path)
"""
import asyncio, json, os, sys
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

async def do_login(page):
    await page.goto(NETCHEF_BASE, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_selector('input[type="text"]', timeout=30000)
    await page.fill('input[type="text"]', USERNAME)
    await page.fill('input[type="password"]', PASSWORD)
    await page.keyboard.press("Enter")
    try: await page.wait_for_load_state("networkidle", timeout=30000)
    except PlaywrightTimeout: pass

async def select_location(page):
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

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        await do_login(page)
        await select_location(page)
        try: await page.wait_for_load_state("networkidle", timeout=30000)
        except PlaywrightTimeout: pass
        await asyncio.sleep(4)

        # 1) Open every menu we can find so children render
        await page.evaluate("""
            (() => {
                if (typeof Ext === 'undefined') return;
                // Click all top-level menu buttons to expand
                Ext.ComponentQuery.query('button[menu], button[arrowVisible=true]').forEach(btn => {
                    try { btn.showMenu && btn.showMenu(); } catch(e) {}
                });
                // Open all tree nodes
                Ext.ComponentQuery.query('treelist, tree, treepanel').forEach(t => {
                    try { t.expandAll && t.expandAll(); } catch(e) {}
                });
            })()
        """)
        await page.wait_for_timeout(2000)

        # 2) Enumerate every menuitem / treeitem / button with a handler
        items = await page.evaluate("""
            (() => {
                if (typeof Ext === 'undefined') return {error: 'no Ext'};
                const out = [];
                const seen = new Set();
                const types = ['menuitem', 'treeitem', 'button', 'treelistitem'];
                for (const t of types) {
                    for (const c of Ext.ComponentQuery.query(t)) {
                        const id = c.id;
                        if (seen.has(id)) continue;
                        seen.add(id);
                        let text = '';
                        try { text = (c.getText && c.getText()) || c.text || c.tooltip || ''; } catch(e) {}
                        if (!text) continue;
                        let parent = '';
                        try {
                            let p = c.up && c.up();
                            while (p && !parent) {
                                if (p.title || p.text || p.tooltip) {
                                    parent = p.title || p.text || p.tooltip;
                                    break;
                                }
                                p = p.up && p.up();
                            }
                        } catch(e) {}
                        let handler = !!(c.handler);
                        let route = '';
                        try { route = c.routeTo || c.target || c.href || ''; } catch(e) {}
                        out.push({type: t, text: String(text).trim(), parent: String(parent).trim(),
                                  hasHandler: handler, route: String(route)});
                    }
                }
                return out;
            })()
        """)
        outfile = DATA_DIR / "ct_menu_inventory.json"
        outfile.write_text(json.dumps(items, indent=2))
        print(f"saved {len(items) if isinstance(items, list) else 'ERR'} menu items to {outfile}")

        # Also save the dashboard config payload for reference
        ext_routes = await page.evaluate("""
            (() => {
                if (typeof Ext === 'undefined') return null;
                // Try to find the Application's controller and route table
                const apps = Ext.app && Ext.app.Application ? Object.values(Ext.app.Application.instances || {}) : [];
                const out = {apps: apps.length, routes: []};
                try {
                    if (Ext.app && Ext.app.route && Ext.app.route.Router) {
                        const r = Ext.app.route.Router;
                        if (r.routes) {
                            for (const k of Object.keys(r.routes)) out.routes.push(k);
                        }
                    }
                } catch(e) { out.routesErr = e.message; }
                return out;
            })()
        """)
        (DATA_DIR / "ct_ext_routes.json").write_text(json.dumps(ext_routes, indent=2))
        print(f"ext routes: {ext_routes}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
