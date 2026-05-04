#!/usr/bin/env python3
"""
Targeted: capture the POST body shape for adding a Supplemental Wages row.

Strategy:
- Use storage_state.json from the morning's discovery run (cookies warm).
- Open the Labor Summary -> WE 5/10 (empty future week) -> Edit -> Supplemental Wages tab.
- Hook page.on('request') so we capture POST bodies for /supplemental-wages/save.
- Click +, fill Employee="Belisle", wage="Credit Card Tip", Lump=0.01, Tab.
- Dump the captured request body, then delete the test row (negative entry +.01 then save?
  simpler: leave it for Bobby to delete via UI — flagging in output. WE 5/10 isn't posted yet
  so it's harmless.)
- Print the body shape, save to data/ct_supwages_save_body.json.

Run: python scraper/api_capture_supwages_body.py
"""
import asyncio, json, os, sys
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

captured_writes = []  # list of {url, body, method}

async def on_request(request):
    try:
        u = request.url
        if "supplemental-wages" not in u.lower():
            return
        if request.method not in ("POST", "PUT"):
            return
        body = request.post_data
        captured_writes.append({"method": request.method, "url": u, "body": body})
        print(f"  ★ [{request.method}] {u}")
        print(f"     body: {(body or '')[:400]}")
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
    if "ChooseLocation" not in page.url:
        return
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
                break
        except Exception: continue
    try:
        await page.wait_for_function("() => !window.location.href.includes('ChooseLocation')", timeout=20_000)
    except PWTimeout: pass


async def open_labor_detail(page, week_ending):
    """Open Labor Detail page for given week ending in editMode=true."""
    url = f"{NETCHEF}/ncext/next.ct#LaborDetails?weekEndingDate={week_ending}&editMode=true"
    print(f"-> goto {url}")
    await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
    await asyncio.sleep(6)
    print(f"   URL: {page.url}")


async def click_supwages_tab(page):
    print("-> Supplemental Wages tab")
    res = await page.evaluate("""
        () => {
            const tabs = Ext.ComponentQuery.query('tab');
            for (const t of tabs) {
                const txt = (t.text || (t.el && t.el.dom && t.el.dom.innerText) || '').trim();
                if (txt.toLowerCase().includes('supplemental')) {
                    if (t.getEl) t.getEl().dom.click();
                    t.fireEvent('click', t);
                    return 'clicked: ' + txt;
                }
            }
            for (const el of document.querySelectorAll('span, a, div')) {
                if ((el.innerText || '').trim() === 'Supplemental Wages') {
                    el.click();
                    return 'DOM clicked';
                }
            }
            return 'not found';
        }
    """)
    print(f"   {res}")
    await asyncio.sleep(3)


async def add_test_row(page):
    """Click +, fill via JS where possible, hit save."""
    print("-> click + to add row")
    res = await page.evaluate("""
        () => {
            // Find the Add (+) button on the Supplemental Wages grid
            const buttons = Ext.ComponentQuery.query('button');
            for (const b of buttons) {
                const tip = (b.tooltip || b.iconCls || '') + ' ' + (b.text || '');
                if (/add|plus/i.test(tip) && b.up('grid')) {
                    b.fireHandler();
                    return 'fired: ' + tip;
                }
            }
            // DOM fallback - click the + button on the grid header area
            const plus = document.querySelector('[data-qtip*="Add" i], .x-tool-plus, button[title*="Add" i]');
            if (plus) { plus.click(); return 'DOM clicked: ' + plus.outerHTML.substring(0,80); }
            return 'no add button';
        }
    """)
    print(f"   add: {res}")
    await asyncio.sleep(2)
    await page.screenshot(path=str(DATA / "supwages_capture_01_added.png"))


async def fill_via_js_and_save(page):
    """Set Employee, Wage type, Lump sum on the new row programmatically, then save."""
    print("-> filling new row via ExtJS programmatic")
    res = await page.evaluate("""
        () => {
            try {
                const grids = Ext.ComponentQuery.query('grid');
                let target = null;
                for (const g of grids) {
                    const cols = g.getColumns ? g.getColumns().map(c => c.text || c.dataIndex || '') : [];
                    if (cols.some(c => /supplemental/i.test(c))) { target = g; break; }
                }
                if (!target) return {ok: false, msg: 'no supplemental grid'};
                const store = target.getStore();
                if (!store.getCount()) return {ok: false, msg: 'no rows in store'};
                const rec = store.getAt(store.getCount() - 1);  // newly added row at end
                // Set fields
                const allFields = Object.keys(rec.getData());
                // Find Belisle's employeeId from any combobox
                const empCombos = Ext.ComponentQuery.query('combobox[displayField*="employee" i], combobox[name*="employee" i]');
                let belisle = null;
                for (const c of empCombos) {
                    const s = c.getStore && c.getStore();
                    if (!s) continue;
                    s.each(r => {
                        const d = r.getData();
                        if (Object.values(d).some(v => String(v).includes('Belisle'))) {
                            belisle = d; return false;
                        }
                    });
                    if (belisle) break;
                }
                return {ok: true, fields: allFields, sampleRow: rec.getData(), belisle};
            } catch (e) { return {ok: false, err: e.message}; }
        }
    """)
    print(f"   probe: {json.dumps(res, default=str)[:600]}")
    return res


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        storage = DATA / "ct_storage_state.json"
        ctx_kwargs = {"storage_state": str(storage)} if storage.exists() else {}
        ctx = await browser.new_context(**ctx_kwargs)
        page = await ctx.new_page()
        page.on("request", lambda r: asyncio.create_task(on_request(r)))
        try:
            await do_login(page)
            await select_location(page)
            # Use WE 5/10 — empty future week. Adding/removing here won't disturb posted weeks.
            await open_labor_detail(page, "05/10/2026")
            await click_supwages_tab(page)
            await add_test_row(page)
            probe = await fill_via_js_and_save(page)
            await asyncio.sleep(3)
            await page.screenshot(path=str(DATA / "supwages_capture_02_filled.png"))
        finally:
            cookies = await ctx.cookies()
            (DATA / "ct_cookies.json").write_text(json.dumps(cookies, indent=2))
            await ctx.storage_state(path=str(storage))
            (DATA / "ct_supwages_save_body.json").write_text(
                json.dumps(captured_writes, indent=2, default=str)
            )
            print(f"\n-> captured {len(captured_writes)} write(s) to /supplemental-wages")
            for w in captured_writes:
                print(f"   {w['method']} {w['url']}")
                print(f"      body ({len(w.get('body') or '')}): {(w.get('body') or '')[:600]}")
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
