#!/usr/bin/env python3
"""
District CrunchTime pull — for each store in config/stores.json, opens a fresh
authenticated CrunchTime session bound to that store's NetChef locationId, pulls
/dashboard/performance/metrics in-page, and writes live KPIs into
data/district/<store_id>/summary.json.

Why per-store login: CrunchTime binds the session to ONE location at login.
choose-location mid-session returns success but does NOT re-bind, and
allLocations:true only returns the bound store. So each store needs its own
fresh login+choose. Verified 2026-05-24.

Creds from .env (CRUNCHTIME_USERNAME / CRUNCHTIME_PASSWORD).
"""
import os, json, sys, asyncio, datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
CFG  = ROOT / "config"
B    = "https://fiveguysfr77.net-chef.com"

env = ROOT/"scraper"/".env"
if not env.exists(): env = ROOT/".env"
if env.exists():
    for line in env.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k,v = line.split("=",1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
USER = os.environ.get("CRUNCHTIME_USERNAME",""); PW = os.environ.get("CRUNCHTIME_PASSWORD","")

from playwright.async_api import async_playwright, TimeoutError as PWTimeout

KPI_MAP = {
    "Actual Net Sales":      ("net_sales",   "Net Sales",     "money"),
    "Labor % of Net Sales":  ("labor_pct",   "Labor %",       "pct"),
    "Sales / Guest":         ("sales_guest", "Sales / Guest", "money2"),
    "Total Cash Over/Shorts":("cash_os",     "Cash O/S",      "money"),
}

def num(v):
    if v is None: return None
    try: return float(str(v).replace(",","").replace("$","").strip())
    except (ValueError,TypeError): return None

def fmt(v, kind):
    n = num(v)
    if n is None: return None
    if kind=="money":  return f"${n:,.0f}"
    if kind=="money2": return f"${n:,.2f}"
    if kind=="pct":    return f"{n:.1f}%"
    return n

async def login(page):
    await page.goto(B, wait_until="domcontentloaded", timeout=30_000)
    await page.wait_for_selector('input[type="text"]', timeout=30_000)
    await page.fill('input[type="text"]', USER)
    await page.fill('input[type="password"]', PW)
    await page.keyboard.press("Enter")
    try: await page.wait_for_load_state("networkidle", timeout=45_000)
    except PWTimeout: pass
    if "login" in page.url.lower():
        raise RuntimeError("stuck on login page")

async def pull_metrics(page, loc_id):
    js = """async (loc) => {
      const h={'Accept':'application/json','Content-Type':'application/json;charset=UTF-8','X-Requested-With':'XMLHttpRequest'};
      await fetch('/resource/ceslogin/choose-location',{method:'POST',headers:h,body:JSON.stringify({locationId:loc})});
      const r=await fetch('/resource/dashboard/performance/metrics',{method:'POST',headers:h,body:JSON.stringify({allLocations:false,pagingInfo:{infinite:false}})});
      return {status:r.status, text:await r.text()};
    }"""
    res = await page.evaluate(js, loc_id)
    if res["status"] != 200:
        raise RuntimeError(f"metrics -> {res['status']}")
    rows = json.loads(res["text"])
    out = {}
    for row in rows:
        nm = row.get("name")
        if nm in KPI_MAP:
            key,label,kind = KPI_MAP[nm]
            if key in out: continue
            wtd = next((x.get("value") for x in row.get("metrics",[]) if str(x.get("calcId"))=="WTD"), None)
            out[key] = {"value":fmt(wtd,kind),"raw":num(wtd),"label":label,"source":"CrunchTime","status":"live","window":"WTD"}
    return out

async def main():
    if not USER or not PW:
        print("FATAL: no creds in .env", file=sys.stderr); sys.exit(2)
    reg = json.loads((CFG/"stores.json").read_text())
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M ET")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for st in reg["stores"]:
            sid = st["store_id"]
            cfg = json.loads((CFG/f"{sid}.json").read_text())
            loc = cfg["crunchtime"]["location_id"]
            ctx = await browser.new_context()
            page = await ctx.new_page()
            try:
                await login(page)
                kpis = await pull_metrics(page, loc)
                sumf = DATA/"district"/sid/"summary.json"
                doc = json.loads(sumf.read_text())
                doc["generated"] = now
                doc["_status"] = "live CrunchTime KPIs (WTD); Brink/Steritech pending"
                doc["kpis"].update(kpis)
                doc["sections"]["sales"]["status"] = "live"
                doc["sections"]["labor"]["status"] = "live"
                sumf.write_text(json.dumps(doc, indent=2))
                print(f"  {sid} {cfg['store_name']:<28} net={kpis.get('net_sales',{}).get('value')} labor={kpis.get('labor_pct',{}).get('value')}")
            except Exception as e:
                print(f"  {sid} FAILED: {e}", file=sys.stderr)
            finally:
                await ctx.close()
        await browser.close()
    print(f"done {now}")

if __name__ == "__main__":
    asyncio.run(main())
