#!/usr/bin/env python3
"""
Targeted discovery: Labor Summary -> Edit week -> Supplemental Wages tab.
Captures every JSON XHR + the POST body that submits a new Credit Card Tip row.

Reuses storage_state.json from a prior api_discover.py run when available.
Run: python scraper/api_discover_supwages.py
"""
import asyncio, json, os, re, sys
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
NETCHEF = "https://fiveguysfr77.net-chef.com"

# Load .env
if not os.environ.get("CRUNCHTIME_USERNAME"):
    env = ROOT / ".env"
    if env.exists():
        for ln in env.read_text().splitlines():
            ln = ln.strip()
            if "=" in ln and not ln.startswith("#"):
                k, v = ln.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

USER = os.environ["CRUNCHTIME_USERNAME"]
PASS = os.environ["CRUNCHTIME_PASSWORD"]

captured = {}
def is_interesting(url, ct):
    if not url.startswith(NETCHEF): return False
    if "/resource/" not in url: return False
    if "json" not in (ct or "").lower(): return False
    return True

async def on_response(resp):
    try:
        url = resp.url
        ct = resp.headers.get("content-type", "")
        if not is_interesting(url, ct): return
        clean = re.sub(r"[&?]_dc=\d+", "", url)
        # Don't dedup writes - we want every save
        method = resp.request.method
        key = f"{method} {clean}"
        if key in captured and method == "GET": return
        try: body = await resp.text()
        except Exception: body = "<unreadable>"
        try: req_body = resp.request.post_data
        except Exception: req_body = None
        if key not in captured: captured[key] = []
        captured[key].append({
            "method": method, "status": resp.status, "ct": ct,
            "request_body": req_body,
            "response_truncated": body[:3000],
            "response_full_length": len(body),
        })
        marker = "★" if method in ("POST","PUT","DELETE") else " "
        print(f"  {marker} [{method}] {resp.status} {clean[:130]}")
    except Exception as e:
        print(f"  err: {e}", file=sys.stderr)


async def do_login(page):
    print(f"-> goto {NETCHEF}")
    await page.goto(NETCHEF, wait_until="domcontentloaded", timeout=30_000)
    await page.wait_for_selector('input[type="text"]', timeout=30_000)
    await page.fill('input[type="text"]', USER)
    await page.fill('input[type="password"]', PASS)
    await page.keyboard.press("Enter")
    try: await page.wait_for_load_state("networkidle", timeout=45_000)
    except PWTimeout: pass


async def select_location(page):
    print("-> selecting 2065")
    await asyncio.sleep(2)
    res = await page.evaluate("""
        () => {
            try {
                if (typeof Ext === 'undefined') return 'no Ext';
                const combos = Ext.ComponentQuery.query('combo, combobox');
                for (const c of combos) {
                    const s = c.getStore && c.getStore(); if (!s) continue;
                    let f = null;
                    s.each(r => {
                        for (const k of Object.keys(r.getData())) {
                            if (String(r.get(k)).includes('2065')) { f = r; return false; }
                        }
                    });
                    if (f) { c.setValue(f); c.fireEvent('select', c, [f]); return 'ok'; }
                }
                return 'no match';
            } catch (e) { return 'err: ' + e.message; }
        }
    """)
    print(f"   loc result: {res}")
    await asyncio.sleep(1)
    for sel in ['button:has-text("Sign In")', '.x-btn:has-text("Sign In")', 'div.x-button:has-text("Sign In")']:
        try:
            l = page.locator(sel)
            if await l.count() and await l.first.is_visible():
                await l.first.click(timeout=3000)
                print(f"   clicked {sel}")
                break
        except Exception: continue
    try:
        await page.wait_for_function("() => !window.location.href.includes('ChooseLocation')", timeout=20_000)
    except PWTimeout: pass
    print(f"   post-loc URL: {page.url}")


async def navigate_labor_summary(page):
    """Open Labor Summary via search bar."""
    print("-> opening Labor Summary via search")
    await asyncio.sleep(3)
    # Try direct hash route first
    try:
        await page.goto(f"{NETCHEF}/ncext/modern.ct#NCLaborSummary", wait_until="domcontentloaded", timeout=15_000)
        await asyncio.sleep(5)
    except Exception as e:
        print(f"   direct hash failed: {e}")
    print(f"   URL: {page.url}")
    await page.screenshot(path=str(DATA / "supwages_01_laborsummary.png"))


async def open_we_edit(page):
    """Find the WE 5/3 row and click Edit."""
    print("-> looking for WE 05/03 row")
    await asyncio.sleep(4)
    # ExtJS grid — find row with Sun 5/3 and click edit/pencil
    res = await page.evaluate("""
        () => {
            try {
                const grids = Ext.ComponentQuery.query('grid, gridpanel');
                for (const g of grids) {
                    const store = g.getStore && g.getStore();
                    if (!store) continue;
                    let target = null;
                    store.each(rec => {
                        const vals = Object.values(rec.getData()).map(v => String(v));
                        if (vals.some(v => v.includes('05/03') || v.includes('5/3'))) {
                            target = rec; return false;
                        }
                    });
                    if (target) {
                        const view = g.getView();
                        const idx = store.indexOf(target);
                        const node = view.getNode(idx);
                        if (node) {
                            // Look for an edit/pencil action
                            const actions = node.querySelectorAll('img, .x-action-col-icon, [data-qtip]');
                            for (const a of actions) {
                                const tip = (a.getAttribute('data-qtip') || a.getAttribute('title') || '').toLowerCase();
                                if (tip.includes('edit') || tip.includes('pencil')) {
                                    a.click();
                                    return 'clicked edit on idx=' + idx + ' tip=' + tip;
                                }
                            }
                            // fallback: dblclick row
                            view.fireEvent('rowdblclick', view, target, node, idx);
                            return 'dblclick idx=' + idx;
                        }
                    }
                }
                return 'no WE 5/3 row found';
            } catch (e) { return 'err ' + e.message; }
        }
    """)
    print(f"   edit result: {res}")
    await asyncio.sleep(5)
    await page.screenshot(path=str(DATA / "supwages_02_after_edit.png"))


async def click_supwages_tab(page):
    print("-> clicking Supplemental Wages tab")
    await asyncio.sleep(2)
    res = await page.evaluate("""
        () => {
            try {
                // Find any tab with "Supplemental Wages" text
                const tabs = Ext.ComponentQuery.query('tab');
                for (const t of tabs) {
                    const txt = (t.text || (t.el && t.el.dom && t.el.dom.innerText) || '').trim();
                    if (txt.toLowerCase().includes('supplemental')) {
                        t.fireEvent('click', t);
                        if (t.getEl) t.getEl().dom.click();
                        return 'clicked tab: ' + txt;
                    }
                }
                // Fallback DOM
                for (const el of document.querySelectorAll('span, a, div')) {
                    const t = (el.innerText || '').trim();
                    if (t === 'Supplemental Wages') {
                        el.click();
                        return 'clicked DOM: ' + t;
                    }
                }
                return 'tab not found';
            } catch (e) { return 'err ' + e.message; }
        }
    """)
    print(f"   tab result: {res}")
    await asyncio.sleep(5)
    await page.screenshot(path=str(DATA / "supwages_03_tab.png"))


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        # Use storage state if it has cookies
        storage = DATA / "ct_storage_state.json"
        ctx_kwargs = {}
        if storage.exists():
            ctx_kwargs["storage_state"] = str(storage)
        ctx = await browser.new_context(**ctx_kwargs)
        page = await ctx.new_page()
        page.on("response", lambda r: asyncio.create_task(on_response(r)))
        try:
            await do_login(page)
            if "ChooseLocation" in page.url:
                await select_location(page)
            await navigate_labor_summary(page)
            await open_we_edit(page)
            await click_supwages_tab(page)
            # Hold open 5s to let endpoints fire
            await asyncio.sleep(5)
        finally:
            cookies = await ctx.cookies()
            (DATA / "ct_cookies.json").write_text(json.dumps(cookies, indent=2))
            await ctx.storage_state(path=str(storage))
            (DATA / "ct_supwages_endpoints.json").write_text(
                json.dumps(captured, indent=2, default=str)
            )
            print(f"\n-> captured {len(captured)} keyed endpoints")
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
