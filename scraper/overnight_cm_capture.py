#!/usr/bin/env python3
"""
Overnight ComplianceMate endpoint capture.

Logs in with COMPLIANCEMATE_USERNAME/PASSWORD env vars, walks key pages,
captures all JSON network traffic, dumps to
data/overnight/compliancemate_<YYYY-MM-DD>.json.

Page walks are passive — real endpoint discovery needs click sequences
specific to each report. This script is the infrastructure pass; the
click sequences come in follow-up sessions.
"""

from __future__ import annotations
import asyncio, json, os, sys
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

ROOT     = Path(__file__).resolve().parents[1]
OUT_DIR  = ROOT / "data" / "overnight"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BASE = "https://fg-beta.compliancemate.com"
USERNAME = os.getenv("COMPLIANCEMATE_USERNAME", "")
PASSWORD = os.getenv("COMPLIANCEMATE_PASSWORD", "")

WALK = [
    "/",
    "/statistics",
    "/reports",
    "/manager",
    "/dashboard",
]


async def main() -> int:
    if not USERNAME or not PASSWORD:
        print("::error::COMPLIANCEMATE_USERNAME / PASSWORD not set")
        return 1

    captured: list[dict] = []
    auth_failed = False

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context()
        page = await ctx.new_page()

        async def on_response(resp):
            try:
                ct = (resp.headers.get("content-type") or "").lower()
                url = resp.url
                if BASE not in url:
                    return
                if "json" in ct or url.endswith(".json"):
                    captured.append({
                        "url": url.replace(BASE, ""),
                        "method": resp.request.method,
                        "status": resp.status,
                        "size_hint": int(resp.headers.get("content-length", 0) or 0),
                    })
            except Exception:
                pass

        page.on("response", on_response)

        # Login
        try:
            await page.goto(BASE, wait_until="domcontentloaded", timeout=30_000)
            await page.wait_for_timeout(2000)
            for sel in ['input[name*="user" i]', 'input[name*="email" i]', 'input[type="text"]', 'input[type="email"]']:
                if await page.locator(sel).count():
                    await page.fill(sel, USERNAME, timeout=3000)
                    break
            for sel in ['input[type="password"]', 'input[name*="pass" i]']:
                if await page.locator(sel).count():
                    await page.fill(sel, PASSWORD, timeout=3000)
                    break
            for sel in ['button[type="submit"]', 'button:has-text("Log")', 'button:has-text("Sign")', 'input[type="submit"]']:
                loc = page.locator(sel)
                if await loc.count() and await loc.first.is_visible():
                    await loc.first.click()
                    break
            else:
                await page.keyboard.press("Enter")
            await page.wait_for_load_state("networkidle", timeout=20_000)
        except Exception as e:
            print(f"::error::Login flow failed: {e}")
            auth_failed = True

        if not auth_failed:
            for path in WALK:
                try:
                    print(f"  -> {path}")
                    await page.goto(BASE + path, wait_until="networkidle", timeout=30_000)
                    await page.wait_for_timeout(2000)
                except Exception as e:
                    print(f"::warning::{path}: {e}")

        await browser.close()

    seen = set()
    unique: list[dict] = []
    for c in captured:
        key = (c["method"], c["url"].split("?", 1)[0])
        if key in seen:
            continue
        seen.add(key)
        unique.append(c)

    date = datetime.utcnow().strftime("%Y-%m-%d")
    out = OUT_DIR / f"compliancemate_{date}.json"
    out.write_text(json.dumps({
        "captured_at_utc": datetime.utcnow().isoformat(),
        "auth_failed": auth_failed,
        "raw_count": len(captured),
        "unique_endpoint_count": len(unique),
        "endpoints": unique,
    }, indent=2), encoding="utf-8")

    print(f"Captured {len(captured)} responses, {len(unique)} unique endpoints")
    print(f"Wrote {out.relative_to(ROOT)}")
    return 2 if auth_failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
