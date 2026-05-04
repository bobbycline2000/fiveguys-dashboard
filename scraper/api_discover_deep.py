#!/usr/bin/env python3
"""
Deep CrunchTime/NetChef API discovery — sweeps the report screens Bobby
named: Employee Time Detail, Projected Sales, Over/Short Deposits,
Weekly Sales, Historical Sales, Employee Maintenance.

Strategy per target:
  1. Try direct hash route (window.location.hash = <guess>)
  2. Programmatic ExtJS menu walk: Ext.ComponentQuery for menu items,
     match by text, fire 'click' event
  3. Sidebar text-match click with force=True (after waiting for mask)

After each navigation: wait 6s for XHRs, capture all /resource/*.json hits.

Outputs:
  data/ct_api_endpoints_deep.json   — {url: {...}}
  data/ct_endpoints_by_screen.json  — {screen_name: [urls...]}
  data/ct_cookies.json              — overwritten with fresh
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

# Load .env
if not os.environ.get("CRUNCHTIME_USERNAME"):
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

USERNAME = os.environ.get("CRUNCHTIME_USERNAME", "")
PASSWORD = os.environ.get("CRUNCHTIME_PASSWORD", "")
if not USERNAME or not PASSWORD:
    print("FATAL: creds not set", file=sys.stderr); sys.exit(2)

# ─── Targets ──────────────────────────────────────────────────────────────────
# Each target lists possible nav strategies. We try them in order;
# we record which captured endpoints fired during each target's window.
# Keep target names stable — they become keys in ct_endpoints_by_screen.json.
TARGETS = [
    {
        "name": "EmployeeTimeDetail",
        "label_matches": ["Time Detail", "Consolidated Time Detail", "Time Card", "Punch Detail", "Time Punch"],
        "hash_routes": ["#TimeDetail", "#NCTimeDetail", "#ConsolidatedTimeDetail", "#NCConsolidatedTimeDetail", "#PunchDetail"],
    },
    {
        "name": "ProjectedSales",
        "label_matches": ["Projected Sales", "Sales Forecast", "Forecast", "Projected", "Sales Projection"],
        "hash_routes": ["#NCProjectedSales", "#ProjectedSales", "#SalesForecast", "#NCForecast", "#NCSalesForecast"],
    },
    {
        "name": "CashOverShortDeposits",
        "label_matches": ["Over/Short", "Cash Over", "Over Short", "Deposit", "Cash Management", "Daily Deposit", "Cash Deposit"],
        "hash_routes": ["#NCOverShort", "#OverShort", "#NCCashOverShort", "#NCDailyDeposit", "#Deposits", "#NCDeposits"],
    },
    {
        "name": "WeeklySales",
        "label_matches": ["Weekly Sales", "Sales Summary", "Sales Week", "Sales Report", "Weekly Sales Report"],
        "hash_routes": ["#NCWeeklySales", "#WeeklySales", "#NCSalesSummary", "#SalesSummary"],
    },
    {
        "name": "HistoricalSales",
        "label_matches": ["Historical Sales", "Sales History", "Historic Sales", "Sales Trend", "Trend Sales"],
        "hash_routes": ["#NCHistoricalSales", "#HistoricalSales", "#SalesHistory", "#NCSalesTrend"],
    },
    {
        "name": "EmployeeMaintenance",
        "label_matches": ["Employee Maintenance", "Employees", "Employee Setup", "Employee Records", "Employee Master", "Manage Employees"],
        "hash_routes": ["#NCEmployeeMaintenance", "#EmployeeMaintenance", "#NCEmployees", "#Employees", "#EmployeeSetup", "#NCEmployeeSetup"],
    },
]

# ─── Capture state ────────────────────────────────────────────────────────────
captured = {}                      # url -> entry
endpoints_by_screen = {}           # screen_name -> [urls]
current_screen = "warmup"

def is_interesting(url, ct):
    if not url.startswith(NETCHEF_BASE): return False
    if "/resource/" not in url: return False
    if not ct or "json" not in ct.lower(): return False
    return True

async def on_response(response):
    try:
        url = response.url
        ct = response.headers.get("content-type", "")
        if not is_interesting(url, ct): return
        clean = re.sub(r"[&?]_dc=\d+", "", url)
        if clean in captured:
            # still tag this screen as having seen it
            endpoints_by_screen.setdefault(current_screen, [])
            if clean not in endpoints_by_screen[current_screen]:
                endpoints_by_screen[current_screen].append(clean)
            return
        try: body = await response.text()
        except Exception: body = "<no body>"
        request = response.request
        try: req_body = request.post_data
        except Exception: req_body = None
        captured[clean] = {
            "method": request.method,
            "status": response.status,
            "content_type": ct,
            "request_body": req_body,
            "response_truncated": body[:1500],
            "response_full_length": len(body),
            "first_seen_screen": current_screen,
        }
        endpoints_by_screen.setdefault(current_screen, []).append(clean)
        print(f"  [{request.method}] {response.status} ({len(body):>7}b) -- {clean.replace(NETCHEF_BASE,'')[:110]}", flush=True)
    except Exception as exc:
        print(f"  capture error: {exc}", file=sys.stderr)

# ─── Login / location (proven) ────────────────────────────────────────────────
async def do_login(page):
    print("-> login")
    await page.goto(NETCHEF_BASE, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_selector('input[type="text"]', timeout=30000)
    await page.fill('input[type="text"]', USERNAME)
    await page.fill('input[type="password"]', PASSWORD)
    await page.keyboard.press("Enter")
    try: await page.wait_for_load_state("networkidle", timeout=45000)
    except PlaywrightTimeout: pass
    print(f"  post-login: {page.url}")

async def _click_sign_in(page):
    for sel in ['button:has-text("Sign In")', 'a:has-text("Sign In")',
                '.x-btn:has-text("Sign In")', '.x-btn-inner:has-text("Sign In")',
                'div.x-button:has-text("Sign In")']:
        try:
            loc = page.locator(sel)
            if await loc.count() and await loc.first.is_visible():
                await loc.first.click(timeout=3000)
                return True
        except Exception: continue
    return False

async def select_location(page):
    print("-> location pick KY-2065")
    try: await page.wait_for_load_state("networkidle", timeout=30000)
    except PlaywrightTimeout: pass
    try:
        await page.wait_for_function("() => document.body.innerText.trim().length > 100",
                                     timeout=30000, polling=1000)
    except PlaywrightTimeout: pass
    result = await page.evaluate("""
        (() => {
            try {
                if (typeof Ext === 'undefined') return 'no Ext';
                var combos = Ext.ComponentQuery.query('combo, combobox');
                for (var i=0;i<combos.length;i++) {
                    var c=combos[i], s=c.getStore?c.getStore():null; if(!s) continue;
                    var found=null;
                    s.each(function(r){
                        for(var f of Object.keys(r.getData()))
                            if(String(r.get(f)).includes('2065')){found=r;return false;}
                    });
                    if(found){c.setValue(found); c.fireEvent('select',c,[found]);
                              return 'ok: '+JSON.stringify(found.getData()).substring(0,80);}
                }
                return 'no match';
            } catch(e) { return 'err: '+e.message; }
        })()
    """)
    print(f"  ext-select: {result}")
    if result and result.startswith("ok:"):
        await page.wait_for_timeout(800)
        await _click_sign_in(page)
    try:
        await page.wait_for_function("() => !window.location.href.includes('ChooseLocation')", timeout=20000)
    except PlaywrightTimeout:
        print("  WARN: still on ChooseLocation")
    print(f"  post-location: {page.url}")

# ─── Mask handling ────────────────────────────────────────────────────────────
async def wait_for_mask_clear(page, timeout=15000):
    """ExtJS x-mask overlays block clicks. Wait for any visible mask to disappear."""
    try:
        await page.wait_for_function(
            "() => !Array.from(document.querySelectorAll('.x-mask')).some(m => m.offsetWidth > 0 && getComputedStyle(m).visibility !== 'hidden' && getComputedStyle(m).display !== 'none')",
            timeout=timeout
        )
    except PlaywrightTimeout:
        pass

# ─── Navigate to a target ─────────────────────────────────────────────────────
async def nav_via_hash(page, hash_route):
    try:
        url = f"{NETCHEF_BASE}/ncext/modern.ct{hash_route}"
        await page.evaluate(f"window.location.hash = {json.dumps(hash_route)}")
        await page.wait_for_timeout(1500)
        return True
    except Exception as exc:
        print(f"    hash {hash_route} err: {exc}")
        return False

async def nav_via_extjs_menu(page, label):
    """Walk every menu item ExtJS knows about, click the one matching label."""
    try:
        result = await page.evaluate(f"""
            (() => {{
                if (typeof Ext === 'undefined') return 'no Ext';
                const target = {json.dumps(label.lower())};
                const all = Ext.ComponentQuery.query('menuitem, treeitem, button, [text], [tooltip]');
                for (const c of all) {{
                    let txt = '';
                    try {{ txt = (c.getText && c.getText()) || c.text || c.tooltip || ''; }} catch(e) {{}}
                    if (txt && String(txt).toLowerCase().includes(target)) {{
                        try {{
                            if (c.fireEvent) c.fireEvent('click', c);
                            if (c.handler) c.handler.call(c.scope || c, c);
                            if (c.click) c.click();
                            return 'clicked: '+txt;
                        }} catch(e) {{ return 'click err: '+e.message; }}
                    }}
                }}
                return 'no match for '+target+' (scanned '+all.length+')';
            }})()
        """)
        return result
    except Exception as exc:
        return f"err: {exc}"

async def nav_via_dom_text(page, label):
    """Fallback: click any element containing the label text via JS."""
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
        return clicked
    except Exception as exc:
        return None

async def visit_target(page, target):
    global current_screen
    current_screen = target["name"]
    print(f"\n=== {target['name']} ===")
    pre_count = len(captured)

    # Strategy 1: hash routes (cheapest, often free XHRs even if rendering fails)
    for h in target["hash_routes"]:
        await wait_for_mask_clear(page, 8000)
        ok = await nav_via_hash(page, h)
        if ok:
            await page.wait_for_timeout(2000)

    # Strategy 2: ExtJS programmatic menu click
    for label in target["label_matches"]:
        await wait_for_mask_clear(page, 8000)
        r = await nav_via_extjs_menu(page, label)
        if r and r.startswith("clicked:"):
            print(f"  ext-menu hit: {r}")
            await page.wait_for_timeout(3500)
            break

    # Strategy 3: DOM text click
    for label in target["label_matches"]:
        await wait_for_mask_clear(page, 5000)
        r = await nav_via_dom_text(page, label)
        if r:
            print(f"  dom-text hit: {r}")
            await page.wait_for_timeout(3000)
            break

    # Final settle
    try: await page.wait_for_load_state("networkidle", timeout=8000)
    except PlaywrightTimeout: pass

    new_count = len(captured) - pre_count
    print(f"  <- {new_count} new endpoints from {target['name']}")

# ─── Main ─────────────────────────────────────────────────────────────────────
async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        page.on("response", lambda r: asyncio.create_task(on_response(r)))

        try:
            await do_login(page)
            await select_location(page)
            print("\n=== warmup (dashboard load) ===")
            try: await page.wait_for_load_state("networkidle", timeout=30000)
            except PlaywrightTimeout: pass
            await asyncio.sleep(4)

            # Sweep targets
            for tgt in TARGETS:
                try:
                    await visit_target(page, tgt)
                except Exception as exc:
                    print(f"  ! visit_target {tgt['name']} failed: {exc}")
                # return to dashboard between targets so subsequent navs aren't trapped
                try:
                    await page.evaluate("window.location.hash='#NCDashboard'")
                    await page.wait_for_timeout(1500)
                    await wait_for_mask_clear(page, 5000)
                except Exception:
                    pass

        except Exception as exc:
            print(f"FATAL: {exc}", file=sys.stderr)
            await page.screenshot(path=str(DATA_DIR / "api_discover_deep_error.png"))
            raise
        finally:
            cookies = await context.cookies()
            (DATA_DIR / "ct_cookies.json").write_text(json.dumps(cookies, indent=2))
            await context.storage_state(path=str(DATA_DIR / "ct_storage_state.json"))
            (DATA_DIR / "ct_api_endpoints_deep.json").write_text(json.dumps(captured, indent=2, default=str))
            (DATA_DIR / "ct_endpoints_by_screen.json").write_text(json.dumps(endpoints_by_screen, indent=2))
            print(f"\n=== TOTAL: {len(captured)} unique endpoints across {len(endpoints_by_screen)} screens ===")
            for screen, urls in endpoints_by_screen.items():
                print(f"  {screen}: {len(urls)} endpoints")
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
