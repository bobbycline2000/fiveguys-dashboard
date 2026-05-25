#!/usr/bin/env python3
"""
Discover the CrunchTime P&L / cost API. Logs in, navigates Inventory -> Profit
and Loss, sets a Mon-Sun range, clicks Retrieve, and captures every /resource/*
XHR (URL + method + request body + response) that fires. Dumps to
data/pnl_discovery.json so we can replace the fragile page-scrape with a JSON pull.
"""
import os, sys, json, asyncio
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
env = ROOT/".env"
if env.exists():
    for line in env.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k,v=line.split("=",1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

sys.path.insert(0, str(Path(__file__).parent))
from main import NETCHEF_BASE, do_login, select_location  # noqa
from scrape_cogs import _navigate_to_pnl, _set_date_range_and_retrieve, _ct_date_str, _last_week_mon_sun
from playwright.async_api import async_playwright

CAP = []

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        ctx = await b.new_context(viewport={"width":1600,"height":1000})
        page = await ctx.new_page()

        async def on_resp(resp):
            u = resp.url
            if "/resource/" not in u: return
            low = u.lower()
            if not any(k in low for k in ("pnl","profit","cost","inventory","theoretical","gl","margin","report")): return
            try:
                body = await resp.text()
            except Exception:
                body = ""
            req = resp.request
            CAP.append({"method":req.method,"url":u,"status":resp.status,
                        "req_body": (req.post_data or "")[:800],
                        "resp_head": body[:1200], "resp_len": len(body)})

        page.on("response", on_resp)

        await page.goto(NETCHEF_BASE, wait_until="domcontentloaded", timeout=30_000)
        if not await do_login(page):
            print("login failed"); await b.close(); return
        await select_location(page)
        await page.wait_for_timeout(4000)

        s, e = _last_week_mon_sun(date.today())
        print(f"navigating P&L for {s} -> {e}")
        await _navigate_to_pnl(page)
        await page.wait_for_timeout(3000)
        await _set_date_range_and_retrieve(page, _ct_date_str(s), _ct_date_str(e))
        await page.wait_for_timeout(6000)

        await b.close()

    (DATA/"pnl_discovery.json").write_text(json.dumps(CAP, indent=2))
    print(f"captured {len(CAP)} /resource calls -> data/pnl_discovery.json")
    for c in CAP:
        print(f"  {c['method']} {c['status']} {c['url'][:110]}  ({c['resp_len']}b)")

asyncio.run(main())
