#!/usr/bin/env python3
"""
Targeted discovery using actual menu labels enumerated from
ct_menu_inventory.json. For each label, finds the menuitem in
ExtJS and tries: c.handler() -> c.click() -> c.fireEvent('click') -> simulate full DOM click.

Saves to ct_api_endpoints_deep.json + ct_endpoints_by_screen.json incrementally.
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

# Map screen-name -> exact menu label
TARGETS = {
    "MenuMix":                "Menu Mix",
    "ConsolidatedMenuMix":    "Consolidated Menu Mix",
    "Checks":                 "Checks",
    "ScheduleShiftAudit":     "Schedule Shift Audit",
    "ConsolidatedScheduleShiftAudit": "Consolidated Schedule Shift Audit",
    "HrsVarToSchedule":       "Hrs. Var. to Schedule",
    "Hourly":                 "Hourly",
    "Sales":                  "Sales",
    "LaborOverview":          "Labor Overview",
    "PostLabor":              "Post Labor",
    "EmployeeBreaks":         "Employee Breaks",
    "EmployeeChanges":        "Employee Changes",
    "PeriodToDate":           "Period-to-Date",
    "LaborProductivity":      "Labor Productivity",
    "ConsolidatedLaborProductivity": "Consolidated Labor Productivity",
    "ConsolidatedPayrollControl": "Consolidated Payroll Control",
}

ENDPOINTS_FILE = DATA_DIR / "ct_api_endpoints_deep.json"
SCREENS_FILE   = DATA_DIR / "ct_endpoints_by_screen.json"

def load_existing():
    eps  = json.loads(ENDPOINTS_FILE.read_text()) if ENDPOINTS_FILE.exists() else {}
    scrn = json.loads(SCREENS_FILE.read_text())   if SCREENS_FILE.exists()   else {}
    return eps, scrn

captured, by_screen = load_existing()
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
        if clean in captured:
            return
        try: body = await response.text()
        except Exception: body = "<no body>"
        request = response.request
        try: req_body = request.post_data
        except Exception: req_body = None
        captured[clean] = {
            "method": request.method, "status": response.status, "content_type": ct,
            "request_body": req_body,
            "response_truncated": body[:1500],
            "response_full_length": len(body),
            "first_seen_screen": current_screen,
        }
        print(f"  [{request.method}] {response.status} ({len(body):>7}b) -- {clean.replace(NETCHEF_BASE,'')[:110]}", flush=True)
    except Exception as exc:
        print(f"  capture err: {exc}", file=sys.stderr)

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

async def click_menuitem(page, exact_label):
    """Find ExtJS menuitem by exact text match and try every way to fire it."""
    return await page.evaluate(f"""
        (() => {{
            if (typeof Ext === 'undefined') return 'no Ext';
            const target = {json.dumps(exact_label)};
            const all = Ext.ComponentQuery.query('menuitem, treeitem, treelistitem, button');
            for (const c of all) {{
                let txt = '';
                try {{ txt = (c.getText && c.getText()) || c.text || ''; }} catch(e) {{}}
                if (String(txt).trim() !== target) continue;
                // 1) handler
                try {{
                    if (c.handler) {{
                        if (typeof c.handler === 'function') c.handler.call(c.scope || c, c);
                        return 'handler-fn';
                    }}
                }} catch(e) {{}}
                // 2) c.click() (ExtJS internal)
                try {{ if (c.click) {{ c.click(); return 'c.click'; }} }} catch(e) {{}}
                // 3) fireEvent
                try {{ if (c.fireEvent) {{ c.fireEvent('click', c, null); return 'fireEvent'; }} }} catch(e) {{}}
                // 4) DOM click on the rendered element
                try {{
                    const el = c.getEl && c.getEl();
                    if (el) {{ el.dom.click(); return 'el.dom.click'; }}
                }} catch(e) {{}}
                return 'matched-but-no-fire';
            }}
            return 'no-match';
        }})()
    """)

async def open_all_menus(page):
    """Click hamburger / open every collapsed menu so menuitems become live."""
    await page.evaluate("""
        (() => {
            if (typeof Ext === 'undefined') return;
            // Click any visible button that looks like a menu trigger
            for (const btn of Ext.ComponentQuery.query('button')) {
                try {
                    const txt = (btn.getText && btn.getText()) || btn.text || '';
                    if (/menu|nav/i.test(txt) || btn.iconCls && /menu|hamburger/i.test(btn.iconCls)) {
                        btn.showMenu && btn.showMenu();
                    }
                } catch(e) {}
            }
            // Walk all menu components and showMenu
            for (const m of Ext.ComponentQuery.query('menu')) {
                try { m.show && m.show(); } catch(e) {}
            }
        })()
    """)
    await page.wait_for_timeout(800)

async def visit_target(page, screen_name, label):
    global current_screen
    current_screen = screen_name
    print(f"\n=== {screen_name} -> '{label}' ===")
    pre = len(captured)

    # Always reset to dashboard before each target
    try:
        await page.evaluate("window.location.hash = '#NCDashboard'")
        await page.wait_for_timeout(800)
    except Exception: pass

    await open_all_menus(page)
    result = await click_menuitem(page, label)
    print(f"  click result: {result}")
    if result not in ("no-match", "no Ext"):
        await page.wait_for_timeout(3500)
        try: await page.wait_for_load_state("networkidle", timeout=8000)
        except PlaywrightTimeout: pass

    new = len(captured) - pre
    print(f"  <- {new} new endpoints from {screen_name}")
    save()
    return new

def save():
    ENDPOINTS_FILE.write_text(json.dumps(captured, indent=2, default=str))
    SCREENS_FILE.write_text(json.dumps(by_screen, indent=2))

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
            print(f"\nFINAL: {len(captured)} endpoints across {len(by_screen)} screens")
            for s, urls in by_screen.items():
                print(f"  {s}: {len(urls)}")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
