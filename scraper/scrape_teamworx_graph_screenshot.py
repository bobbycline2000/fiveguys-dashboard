#!/usr/bin/env python3
"""
Screenshot today's per-day hourly ideal-vs-scheduled graph from Teamworx.

Logs in via Playwright, navigates to the schedule page, opens today's
graph popup (grey graph icon beside the day's row), screenshots just
that popup, and saves it to data/raw/teamworx/<store>/<YYYY-MM-DD>/graph.png.

The dashboard's "Hourly Labor Forecast" card embeds the latest PNG.

Usage:
    python scraper/scrape_teamworx_graph_screenshot.py --store 2065
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date as date_cls
from pathlib import Path

ROOT     = Path(__file__).resolve().parents[1]
RAW      = ROOT / "data" / "raw" / "teamworx"
LOGIN_URL = "https://fiveguysfr77.ct-teamworx.com/views/login.jsp"


def run(store: str, target_date: date_cls) -> int:
    from playwright.sync_api import sync_playwright

    user = os.environ.get("CRUNCHTIME_USERNAME") or os.environ.get("TEAMWORX_USERNAME")
    pwd  = os.environ.get("CRUNCHTIME_PASSWORD") or os.environ.get("TEAMWORX_PASSWORD")
    if not user or not pwd:
        print("ERROR: CRUNCHTIME_USERNAME/PASSWORD not set", file=sys.stderr)
        return 2

    today_iso = target_date.isoformat()
    out_dir = RAW / store / today_iso
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "graph.png"

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = ctx.new_page()

        # 1. Login
        page.goto(LOGIN_URL, wait_until="domcontentloaded")
        page.fill('input[placeholder*="Username"], input[type="text"]', user)
        page.fill('input[type="password"]', pwd)
        page.get_by_role("button", name="Sign In").click()
        page.wait_for_load_state("networkidle", timeout=20000)

        # 2. Pick KY-2065 if Location Selection appears
        if "locationSelection" in page.url:
            page.get_by_role("cell", name=f"KY-{store}").first.click()
            page.wait_for_load_state("networkidle", timeout=20000)

        # 3. Open Labor Schedule (where the per-day graph icon lives)
        try:
            page.get_by_text("Labor Schedule", exact=True).first.click()
        except Exception:
            try:
                page.get_by_text("Schedule", exact=True).first.click()
            except Exception:
                pass
        page.wait_for_load_state("networkidle", timeout=20000)
        page.wait_for_timeout(1500)

        # 4. Find and click today's graph icon. Multiple fallback selectors.
        clicked = False
        selectors = [
            f'tr:has-text("{target_date.strftime("%a")}") .grey-graph-icon',
            f'tr:has-text("{target_date.strftime("%A")}") .grey-graph-icon',
            f'tr:has-text("{target_date.strftime("%b %d")}") .grey-graph-icon',
            f'tr:has-text("{target_date.strftime("%-m/%-d")}") .grey-graph-icon',
            '.grey-graph-icon',  # last-resort: first one on the page
        ]
        for sel in selectors:
            try:
                el = page.locator(sel).first
                if el.count():
                    el.click()
                    clicked = True
                    print(f"[teamworx-graph] clicked graph icon via selector: {sel}")
                    break
            except Exception:
                continue

        if not clicked:
            print("ERROR: could not find graph icon for today", file=sys.stderr)
            page.screenshot(path=str(out_dir / "schedule_page_debug.png"), full_page=True)
            ctx.close()
            browser.close()
            return 1

        # 5. Wait for the popup canvas / chart to render
        page.wait_for_timeout(2000)

        # 6. Screenshot the popup. Try common modal/popup selectors.
        popup_sel_candidates = [
            '.modal-content',
            '.popup-content',
            '.x-window',         # ExtJS
            '[role="dialog"]',
            '.chart-popup',
            'canvas:visible',    # last resort: just the canvas
        ]
        popup_locator = None
        for sel in popup_sel_candidates:
            try:
                loc = page.locator(sel).first
                if loc.count():
                    popup_locator = loc
                    print(f"[teamworx-graph] using popup selector: {sel}")
                    break
            except Exception:
                continue

        if popup_locator is None:
            print("WARN: no popup matched — falling back to viewport screenshot", file=sys.stderr)
            page.screenshot(path=str(out_path))
        else:
            popup_locator.screenshot(path=str(out_path))

        ctx.close()
        browser.close()

    if not out_path.exists() or out_path.stat().st_size < 500:
        print(f"ERROR: screenshot at {out_path} missing or empty", file=sys.stderr)
        return 1

    print(f"[teamworx-graph] saved {out_path} ({out_path.stat().st_size} bytes)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="2065")
    args = ap.parse_args()
    return run(args.store, date_cls.today())


if __name__ == "__main__":
    sys.exit(main())
