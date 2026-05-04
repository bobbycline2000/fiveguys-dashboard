#!/usr/bin/env python3
"""
Single-target CT discovery — runs login + location + ONE target screen,
writes results immediately, exits. Designed for resilient sweeps:
re-run with different --target until all are captured.

Usage:
  python scraper/api_discover_one.py CashOverShortDeposits
  python scraper/api_discover_one.py WeeklySales
  python scraper/api_discover_one.py HistoricalSales
  python scraper/api_discover_one.py EmployeeMaintenance
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
DATA_DIR.mkdir(exist_ok=True)
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

TARGETS = {
    "CashOverShortDeposits": {
        "label_matches": ["Over/Short", "Cash Over", "Over Short", "Deposit", "Daily Deposit"],
        "hash_routes": ["#NCOverShort", "#NCDailyDeposit", "#Deposits"],
    },
    "WeeklySales": {
        "label_matches": ["Weekly Sales", "Sales Summary", "Sales Report"],
        "hash_routes": ["#NCWeeklySales", "#NCSalesSummary"],
    },
    "HistoricalSales": {
        "label_matches": ["Historical Sales", "Sales History", "Sales Trend"],
        "hash_routes": ["#NCHistoricalSales", "#SalesHistory", "#NCSalesTrend"],
    },
    "EmployeeMaintenance": {
        "label_matches": ["Employee Maintenance", "Employee Setup", "Manage Employees", "Employees"],
        "hash_routes": ["#NCEmployeeMaintenance", "#NCEmployees", "#NCEmployeeSetup"],
    },
}

# ─── Persistence ──────────────────────────────────────────────────────────────
ENDPOINTS_FILE = DATA_DIR / "ct_api_endpoints_deep.json"
SCREENS_FILE   = DATA_DIR / "ct_endpoints_by_screen.json"

def load_existing():
    eps  = json.loads(ENDPOINTS_FILE.read_text()) if ENDPOINTS_FILE.exists() else {}
    scrn = json.loads(SCREENS_FILE.read_text())   if SCREENS_FILE.exists()   else {}
    return eps, scrn

# ─── Capture state ────────────────────────────────────────────────────────────
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
        if clean in captured:
            if clean not in by_screen[current_screen]:
                by_screen[current_screen].append(clean)
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
        if clean not in by_screen[current_screen]:
            by_screen[current_screen].append(clean)
        print(f"  [{request.method}] {response.status} ({len(body):>7}b) -- {clean.replace(NETCHEF_BASE,'')[:110]}", flush=True)
    except Exception as exc:
        print(f"  capture err: {exc}", file=sys.stderr)

async def do_login(page):
    print("-> login")
    await page.goto(NETCHEF_BASE, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_selector('input[type="text"]', timeout=30000)
    await page.fill('input[type="text"]', USERNAME)
    await page.fill('input[type="password"]', PASSWORD)
    await page.keyboard.press("Enter")
    try: await page.wait_for_load_state("networkidle", timeout=30000)
    except PlaywrightTimeout: pass
    print(f"  post-login: {page.url}")

async def select_location(page):
    print("-> location pick KY-2065")
    try: await page.wait_for_load_state("networkidle", timeout=20000)
    except PlaywrightTimeout: pass
    try:
        await page.wait_for_function("() => document.body.innerText.trim().length > 100",
                                     timeout=20000, polling=1000)
    except PlaywrightTimeout: pass
    result = await page.evaluate("""
        (() => {
            try {
                if (typeof Ext === 'undefined') return 'no Ext';
                var combos = Ext.ComponentQuery.query('combo, combobox');
                for (var c of combos) {
                    var s=c.getStore?c.getStore():null; if(!s) continue;
                    var found=null;
                    s.each(function(r){
                        for(var f of Object.keys(r.getData()))
                            if(String(r.get(f)).includes('2065')){found=r;return false;}
                    });
                    if(found){c.setValue(found); c.fireEvent('select',c,[found]); return 'ok';}
                }
                return 'no match';
            } catch(e) { return 'err: '+e.message; }
        })()
    """)
    print(f"  ext-select: {result}")
    if result == "ok":
        await page.wait_for_timeout(800)
        for sel in ['button:has-text("Sign In")', '.x-btn:has-text("Sign In")', 'div.x-button:has-text("Sign In")']:
            try:
                loc = page.locator(sel)
                if await loc.count() and await loc.first.is_visible():
                    await loc.first.click(timeout=3000)
                    break
            except Exception: continue
    try: await page.wait_for_function("() => !window.location.href.includes('ChooseLocation')", timeout=15000)
    except PlaywrightTimeout: print("  WARN still on ChooseLocation")
    print(f"  post-location: {page.url}")

async def quick_mask_wait(page, ms=4000):
    try:
        await page.wait_for_function(
            "() => !Array.from(document.querySelectorAll('.x-mask')).some(m => m.offsetWidth > 0 && getComputedStyle(m).visibility !== 'hidden' && getComputedStyle(m).display !== 'none')",
            timeout=ms,
        )
    except PlaywrightTimeout: pass

async def visit_target(page, name, cfg):
    global current_screen
    current_screen = name
    print(f"\n=== {name} ===")
    pre = len(captured)

    # hash routes
    for h in cfg["hash_routes"]:
        try:
            await page.evaluate(f"window.location.hash = {json.dumps(h)}")
            await page.wait_for_timeout(1500)
            await quick_mask_wait(page, 3000)
        except Exception as exc:
            print(f"  hash {h} err: {exc}")

    # ext menu walk
    for label in cfg["label_matches"]:
        try:
            r = await page.evaluate(f"""
                (() => {{
                    if (typeof Ext === 'undefined') return null;
                    const target = {json.dumps(label.lower())};
                    const all = Ext.ComponentQuery.query('menuitem, treeitem, button');
                    for (const c of all) {{
                        let txt = '';
                        try {{ txt = (c.getText && c.getText()) || c.text || c.tooltip || ''; }} catch(e) {{}}
                        if (txt && String(txt).toLowerCase().includes(target)) {{
                            try {{
                                if (c.fireEvent) c.fireEvent('click', c);
                                if (c.handler) c.handler.call(c.scope || c, c);
                                if (c.click) c.click();
                                return 'clicked: '+txt;
                            }} catch(e) {{}}
                        }}
                    }}
                    return null;
                }})()
            """)
            if r and r.startswith("clicked:"):
                print(f"  ext-menu: {r}")
                await page.wait_for_timeout(2500)
                await quick_mask_wait(page, 3000)
                break
        except Exception as exc:
            print(f"  ext-menu err: {exc}")

    # dom click fallback
    for label in cfg["label_matches"]:
        try:
            clicked = await page.evaluate(f"""
                (() => {{
                    const target = {json.dumps(label.lower())};
                    for (const el of document.querySelectorAll('span, a, div, li, td')) {{
                        const t = (el.textContent || '').trim();
                        if (t.toLowerCase().includes(target) && t.length < 80 && el.offsetParent) {{
                            el.dispatchEvent(new MouseEvent('mousedown', {{bubbles: true}}));
                            el.dispatchEvent(new MouseEvent('mouseup', {{bubbles: true}}));
                            el.dispatchEvent(new MouseEvent('click', {{bubbles: true}}));
                            return t;
                        }}
                    }}
                    return null;
                }})()
            """)
            if clicked:
                print(f"  dom-click: {clicked}")
                await page.wait_for_timeout(2500)
                break
        except Exception: pass

    try: await page.wait_for_load_state("networkidle", timeout=5000)
    except PlaywrightTimeout: pass
    print(f"  <- {len(captured) - pre} new endpoints from {name}")

def save():
    ENDPOINTS_FILE.write_text(json.dumps(captured, indent=2, default=str))
    SCREENS_FILE.write_text(json.dumps(by_screen, indent=2))

async def main(target_name):
    cfg = TARGETS.get(target_name)
    if not cfg:
        print(f"unknown target: {target_name}; known: {list(TARGETS)}", file=sys.stderr)
        sys.exit(2)

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
            try: await page.wait_for_load_state("networkidle", timeout=15000)
            except PlaywrightTimeout: pass
            await asyncio.sleep(3)
            await visit_target(page, target_name, cfg)
        finally:
            cookies = await context.cookies()
            (DATA_DIR / "ct_cookies.json").write_text(json.dumps(cookies, indent=2))
            save()
            print(f"\nsaved {len(captured)} endpoints across {len(by_screen)} screens")
            for s, urls in by_screen.items():
                print(f"  {s}: {len(urls)}")
            await browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"usage: {sys.argv[0]} <target>; targets: {list(TARGETS)}")
        sys.exit(2)
    asyncio.run(main(sys.argv[1]))
