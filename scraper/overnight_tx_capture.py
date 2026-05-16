#!/usr/bin/env python3
"""
Overnight Teamworx endpoint capture.

Loads cookies from data/twx_cookies.json (restored from TEAMWORX_COOKIES_JSON
secret in CI), opens Playwright with those cookies, walks the canonical
Teamworx pages, and dumps every JSON network request to
data/overnight/teamworx_<YYYY-MM-DD>.json for the morning brief to review.

If cookies are expired the workflow will exit with a clear marker file so
the brief can flag "Teamworx cookies need re-mint" tomorrow morning.
"""

from __future__ import annotations
import asyncio, json, os, sys
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

ROOT      = Path(__file__).resolve().parents[1]
COOKIE_F  = ROOT / "data" / "twx_cookies.json"
OUT_DIR   = ROOT / "data" / "overnight"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BASE = "https://fiveguysfr77.ct-teamworx.com"
WALK = [
    "/views/manager/tablet/dailyRoster.jsp",
    "/views/manager/index.jsp",
    "/views/manager/tablet/index.jsp",
    "/views/employees/employees.jsp",
    "/views/scheduling/scheduling.jsp",
]


def _load_cookies() -> list[dict]:
    if not COOKIE_F.exists():
        print(f"::error::No cookie file at {COOKIE_F}")
        return []
    raw = json.loads(COOKIE_F.read_text(encoding="utf-8"))
    cookies = raw["cookies"] if isinstance(raw, dict) and "cookies" in raw else raw
    out = []
    for c in cookies:
        out.append({
            "name": c["name"],
            "value": c["value"],
            "domain": c.get("domain", ".ct-teamworx.com"),
            "path": c.get("path", "/"),
            "httpOnly": c.get("httpOnly", False),
            "secure": c.get("secure", True),
            "sameSite": c.get("sameSite", "Lax"),
        })
    return out


async def main() -> int:
    cookies = _load_cookies()
    if not cookies:
        return 1

    captured: list[dict] = []
    auth_failed = False

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context()
        await ctx.add_cookies(cookies)
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

        for path in WALK:
            url = BASE + path
            try:
                print(f"  -> {path}")
                await page.goto(url, wait_until="networkidle", timeout=45_000)
                await page.wait_for_timeout(2500)
                if "login" in page.url.lower() and path != "/views/login/login.jsp":
                    print(f"::warning::Redirected to login at {path} — cookies likely expired")
                    auth_failed = True
                    break
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
    out = OUT_DIR / f"teamworx_{date}.json"
    out.write_text(json.dumps({
        "captured_at_utc": datetime.utcnow().isoformat(),
        "auth_failed": auth_failed,
        "raw_count": len(captured),
        "unique_endpoint_count": len(unique),
        "endpoints": unique,
    }, indent=2), encoding="utf-8")

    print(f"Captured {len(captured)} responses, {len(unique)} unique endpoints")
    print(f"Wrote {out.relative_to(ROOT)}")

    if auth_failed:
        marker = OUT_DIR / "TEAMWORX_COOKIES_EXPIRED.flag"
        marker.write_text(f"Detected {date}\n", encoding="utf-8")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
