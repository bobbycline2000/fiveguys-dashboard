#!/usr/bin/env python3
"""
Re-mint a CrunchTime session via Playwright login, then enumerate every
location the login can see (GET /resource/ceslogin/locations) BEFORE choosing
a store. Saves fresh cookies to data/ct_cookies.json and the location list to
data/ct_locations.json.

Login flow lifted from api_discover.py (creds from .env).
"""
import os, json, sys, asyncio
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
NETCHEF_BASE = "https://fiveguysfr77.net-chef.com"

# load .env
env = ROOT / "scraper" / ".env"
if not env.exists():
    env = ROOT / ".env"
if env.exists():
    for line in env.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

USERNAME = os.environ.get("CRUNCHTIME_USERNAME", "")
PASSWORD = os.environ.get("CRUNCHTIME_PASSWORD", "")

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout


async def main():
    if not USERNAME or not PASSWORD:
        print("FATAL: CRUNCHTIME_USERNAME/PASSWORD not in .env", file=sys.stderr)
        sys.exit(2)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context()
        page = await ctx.new_page()
        print(f"-> goto {NETCHEF_BASE}")
        await page.goto(NETCHEF_BASE, wait_until="domcontentloaded", timeout=30_000)
        await page.wait_for_selector('input[type="text"]', timeout=30_000)
        await page.fill('input[type="text"]', USERNAME)
        await page.fill('input[type="password"]', PASSWORD)
        await page.keyboard.press("Enter")
        print("-> submitted creds")
        try:
            await page.wait_for_load_state("networkidle", timeout=45_000)
        except PlaywrightTimeout:
            pass
        print(f"  post-login URL: {page.url}")
        if "login" in page.url.lower():
            print("Still on login page — bad creds or MFA gate", file=sys.stderr)
            await browser.close(); sys.exit(1)

        # enumerate locations from the page context (carries session cookies)
        js = """
        async () => {
          const r = await fetch('/resource/ceslogin/locations?page=1&start=0&limit=100',
            {headers:{'Accept':'application/json','X-Requested-With':'XMLHttpRequest'}});
          return {status:r.status, text:await r.text()};
        }"""
        res = await page.evaluate(js)
        print(f"GET /ceslogin/locations -> {res['status']}")
        if res["status"] != 200:
            print(res["text"][:600]); await browser.close(); sys.exit(1)
        data = json.loads(res["text"])
        locs = (data.get("contentMap") or {}).get("locations") or data.get("locations") or []
        print(f"\n=== {len(locs)} locations visible to this login ===")
        for L in locs:
            print(f"  code={str(L.get('locationCode')):<8} id={str(L.get('locationId')):<8} {L.get('locationName')}")
        (DATA_DIR / "ct_locations.json").write_text(json.dumps(locs, indent=2))
        print(f"\nwrote {DATA_DIR / 'ct_locations.json'}")

        # save fresh cookies for reuse
        cookies = await ctx.cookies()
        (DATA_DIR / "ct_cookies.json").write_text(json.dumps(cookies, indent=2))
        print(f"saved {len(cookies)} cookies -> data/ct_cookies.json")
        await browser.close()

asyncio.run(main())
