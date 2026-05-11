"""Agent-side deposit entry — reads pending queue, posts to CrunchTime.

Workflow:
  1. Load data/deposits_pending.json (written by the Cloudflare worker
     when a manager taps "Enter Deposit in CT" on safe_drawer.html).
  2. For each pending entry, look up the salesId + posId for the date
     from data/ct_sales_summary_history.json.
  3. Open the next.ct edit form for that salesId via Playwright (so the
     form-prep chain fires implicitly). Sniff the active session cookies.
  4. POST the deposit row to /resource/salestransactions/bankdeposits/save.
  5. POST the commit to /resource/salestransactions/submit.
  6. Mark the entry processed in deposits_pending.json (append to .history,
     remove from .pending).

Schema for data/deposits_pending.json:
  {
    "pending":   [{ "id": "...", "business_date": "2026-05-10", "amount": 940.74,
                    "memo": "", "mgr": "BC", "requested_at": "..." }],
    "processed": [{ ...above..., "processed_at": "...", "result": "ok|error",
                    "error": "...", "deposit_id": 12345 }]
  }
"""
from __future__ import annotations

import datetime as _dt
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import requests
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
NETCHEF = "https://fiveguysfr77.net-chef.com"
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json;charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": NETCHEF,
    "Referer": f"{NETCHEF}/ncext/next.ct",
}
PENDING_FILE = DATA / "deposits_pending.json"
CT_HISTORY = DATA / "ct_sales_summary_history.json"


def _load_pending() -> dict:
    if not PENDING_FILE.exists():
        return {"pending": [], "processed": []}
    try:
        return json.loads(PENDING_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"pending": [], "processed": []}


def _save_pending(d: dict) -> None:
    PENDING_FILE.write_text(json.dumps(d, indent=2), encoding="utf-8")


def _find_transaction(business_date: str) -> Optional[tuple[int, int]]:
    """Return (salesId, posId) for the given iso business_date from CT history.

    The summary endpoint surfaces salesId + posId per register-day; the
    track_ct_sales_summary.py script also dumps a fresh sample to
    data/ct_sales_summary_sample.json on each run. We use that for the
    lookup so the entry agent doesn't have to call CT just to find the ids.
    """
    sample = DATA / "ct_sales_summary_sample.json"
    if not sample.exists():
        return None
    try:
        rows = json.loads(sample.read_text(encoding="utf-8"))
    except Exception:
        return None
    iso = business_date
    for r in rows:
        s = (r.get("salesDate") or "").split(" ")[0]
        # CT returns MM/DD/YYYY
        if "/" in s:
            m, d, y = s.split("/")
            row_iso = f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
        else:
            row_iso = s[:10]
        if row_iso == iso:
            return r.get("salesId"), r.get("posId")
    return None


def _open_form_and_get_cookies(sales_id: int, *, headless: bool = True) -> dict:
    """Open the next.ct edit form for the given salesId via Playwright.

    The form load fires the prep chain (retrieveResources / currentmode /
    validateedit / prepare). We then read the cookies and return them for
    pure-requests replay of /save and /submit.

    Requires CRUNCHTIME_USERNAME + CRUNCHTIME_PASSWORD env vars OR an
    existing live session in data/ct_cookies.json (the daily scraper mints
    these and we reuse).
    """
    import os
    user = os.environ.get("CRUNCHTIME_USERNAME")
    pw   = os.environ.get("CRUNCHTIME_PASSWORD")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        ctx = browser.new_context()
        # If we have minted cookies, hydrate so login is skipped.
        ck_file = DATA / "ct_cookies.json"
        if ck_file.exists():
            try:
                cks = json.loads(ck_file.read_text(encoding="utf-8"))
                ctx.add_cookies([
                    {"name": c["name"], "value": c["value"],
                     "domain": c.get("domain") or "fiveguysfr77.net-chef.com",
                     "path": c.get("path") or "/"}
                    for c in cks
                ])
            except Exception:
                pass
        page = ctx.new_page()
        page.goto(f"{NETCHEF}/ncext/next.ct#SalesTransactions?mode=edit&salesId={sales_id}",
                  wait_until="domcontentloaded", timeout=60_000)
        # Detect login bounce
        if "/login" in page.url.lower() or "ceslogin" in page.url.lower():
            if not user or not pw:
                raise RuntimeError("CT session expired and no credentials available to re-login.")
            page.fill("input[name='username']", user)
            page.fill("input[name='password']", pw)
            page.keyboard.press("Enter")
            page.wait_for_load_state("networkidle", timeout=30_000)
            page.goto(f"{NETCHEF}/ncext/next.ct#SalesTransactions?mode=edit&salesId={sales_id}",
                      wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(3000)  # let prep chain settle
        cookies = ctx.cookies()
        ctx.close(); browser.close()
        return {c["name"]: c["value"] for c in cookies}


def _post_deposit(jar: dict, sales_id: int, pos_id: int,
                   business_date_iso: str, amount: float, memo: str) -> dict:
    """Post the deposit save + commit. Returns a dict with the outcome."""
    # CT expects MM/DD/YYYY
    y, m, d = business_date_iso.split("-")
    md = f"{int(m):02d}/{int(d):02d}/{int(y):04d}"

    save_url = f"{NETCHEF}/resource/salestransactions/bankdeposits/save"
    submit_url = f"{NETCHEF}/resource/salestransactions/submit"
    deposit_payload = [{"depositId": -1, "amount": float(amount),
                         "memo": memo or ""}]
    r1 = requests.post(save_url, json=deposit_payload, cookies=jar,
                        headers=HEADERS, timeout=30)
    if not r1.ok:
        return {"ok": False, "step": "save", "status": r1.status_code,
                "text": r1.text[:500]}
    save_resp = None
    try:
        save_resp = r1.json()
    except Exception:
        pass

    submit_body = {"extraCriteriaMap": {
        "salesId": sales_id, "viewOnly": False,
        "posId": pos_id, "salesDate": md,
    }}
    r2 = requests.post(submit_url, json=submit_body, cookies=jar,
                        headers=HEADERS, timeout=30)
    if not r2.ok:
        return {"ok": False, "step": "submit", "status": r2.status_code,
                "text": r2.text[:500]}
    return {"ok": True, "save_resp": save_resp, "amount": float(amount),
            "sales_date": md}


def main() -> int:
    state = _load_pending()
    if not state.get("pending"):
        print("[enter-ct-deposits] no pending entries.")
        return 0

    headless = "--headed" not in sys.argv

    new_pending = []
    new_processed = list(state.get("processed", []))
    for item in state["pending"]:
        bd = item.get("business_date")
        amt = item.get("amount")
        memo = item.get("memo", "")
        mgr = item.get("mgr", "?")
        print(f"[enter-ct-deposits] processing {bd} ${amt} by {mgr}", flush=True)

        ids = _find_transaction(bd)
        if not ids:
            print(f"  -> no salesId for {bd}; leaving pending.")
            new_pending.append(item)
            continue
        sales_id, pos_id = ids

        try:
            jar = _open_form_and_get_cookies(sales_id, headless=headless)
        except Exception as e:
            print(f"  -> session open failed: {e}")
            new_pending.append(item)
            continue

        result = _post_deposit(jar, sales_id, pos_id, bd, amt, memo)
        rec = dict(item)
        rec["processed_at"] = _dt.datetime.now().isoformat(timespec="seconds")
        rec["sales_id"] = sales_id
        rec["pos_id"] = pos_id
        if result["ok"]:
            rec["result"] = "ok"
            new_processed.append(rec)
            print(f"  -> entered. (save + submit OK)")
        else:
            rec["result"] = "error"
            rec["error"] = f"{result.get('step')}:{result.get('status')}:{result.get('text','')[:300]}"
            new_processed.append(rec)
            print(f"  -> ERROR: {rec['error']}")

    _save_pending({"pending": new_pending, "processed": new_processed[-200:]})
    print(f"[enter-ct-deposits] done. pending={len(new_pending)} processed_total={len(new_processed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
