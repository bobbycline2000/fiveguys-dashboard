"""Fill Jeff Reiss's live shared `east side tips.xlsx` (tab 2065) via Microsoft Graph.

Usage: python scraper/fill_east_side_tips.py [MM/DD/YYYY]   (week-ending Sunday)

Reads the snapshot produced by enter_tips_browser.py, clears the 2065 tab roster
block, and writes Charged Tips + per-employee hours/payout formulas. Reads back
and verifies the payout column ties to Charged Tips.

Source of truth: skills/crunchtime-enter-tips.md (2026-08-24 note).
"""
from __future__ import annotations
import datetime as dt
import json
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

TENANT_ID     = os.environ["GRAPH_TENANT_ID"]
CLIENT_ID     = os.environ["GRAPH_CLIENT_ID"]
REFRESH_TOKEN = os.environ["GRAPH_REFRESH_TOKEN"]

# Jeff Reiss's live shared workbook (resolved 2026-08-24 via /me/drive/sharedWithMe)
DRIVE_ID = "b!Z9-7DsyFjkSTKiPkeBbmCrvoLObE5KxIjPQX3SEcjeN49UTgLkxdTKpRKjYcWAQQ"
ITEM_ID  = "017OV65BY33T67AW4OZZA23AMGLMY7ZYCJ"
SHEET    = "2065"

FIRST_ROW = 6


def get_token() -> str:
    r = requests.post(
        f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token",
        data={
            "grant_type": "refresh_token",
            "client_id": CLIENT_ID,
            "refresh_token": REFRESH_TOKEN,
            # .default is required — named Files scopes 401 with AADSTS65002
            "scope": "https://graph.microsoft.com/.default offline_access",
        }, timeout=30)
    r.raise_for_status()
    body = r.json()
    new_rt = body.get("refresh_token")
    if new_rt and new_rt != REFRESH_TOKEN:
        txt = env_path.read_text()
        env_path.write_text(txt.replace(REFRESH_TOKEN, new_rt))
        print("[auth] refresh token rotated -> .env")
    return body["access_token"]


def main() -> int:
    arg = next((a for a in sys.argv[1:] if "/" in a), None)
    if not arg:
        print("usage: fill_east_side_tips.py MM/DD/YYYY")
        return 2
    sun = dt.datetime.strptime(arg, "%m/%d/%Y").date()
    snap_path = ROOT / "data" / f"tips_we_{sun.strftime('%Y_%m_%d')}_snapshot.json"
    snap = json.loads(snap_path.read_text())
    payouts = snap["payouts"]
    names = sorted(payouts)
    charged = float(snap["chargedTips"])

    last_row = FIRST_ROW + len(names) - 1
    tot_row = last_row + 1

    tok = get_token()
    H = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
    base = (f"https://graph.microsoft.com/v1.0/drives/{DRIVE_ID}/items/{ITEM_ID}"
            f"/workbook/worksheets('{SHEET}')")

    def patch(addr, values):
        r = requests.patch(f"{base}/range(address='{addr}')", headers=H,
                           json={"values": values}, timeout=60)
        r.raise_for_status()
        return r.json()

    # 1. clear the roster block (rows 6-40, cols A-C)
    r = requests.post(f"{base}/range(address='A{FIRST_ROW}:C40')/clear", headers=H,
                      json={"applyTo": "Contents"}, timeout=60)
    r.raise_for_status()
    print(f"[clear] A{FIRST_ROW}:C40")

    # 2. header: week end, charged tips, tips-per-hour formula
    patch("A2", [[f"Week End {sun.strftime('%-m/%-d') if os.name != 'nt' else sun.strftime('%#m/%#d')}"]])
    patch("C3", [[charged]])
    patch("D3", [[f"=C3/B{tot_row}"]])
    print(f"[header] C3=${charged:.2f}  D3==C3/B{tot_row}")

    # 3. roster rows
    rows = [[n, payouts[n]["hours"], f"=B{FIRST_ROW + i}*$D$3"]
            for i, n in enumerate(names)]
    patch(f"A{FIRST_ROW}:C{last_row}", rows)
    print(f"[roster] {len(rows)} employees rows {FIRST_ROW}-{last_row}")

    # 4. totals row — SUM starts at FIRST_ROW (sheet arrived with SUM(B7:..), a defect)
    patch(f"A{tot_row}:C{tot_row}", [["Total hours for Store",
                                      f"=SUM(B{FIRST_ROW}:B{last_row})",
                                      f"=SUM(C{FIRST_ROW}:C{last_row})"]])
    print(f"[totals] row {tot_row}")

    # 5. read back + verify
    rb = requests.get(f"{base}/range(address='A3:D{tot_row}')", headers=H, timeout=60)
    rb.raise_for_status()
    vals = rb.json()["values"]
    tot_payout = float(vals[-1][2] or 0)
    tot_hours = float(vals[-1][1] or 0)
    print(f"[verify] hours={tot_hours:.2f} payouts=${tot_payout:.2f} "
          f"charged=${charged:.2f} delta=${tot_payout - charged:+.2f}")
    if abs(tot_payout - charged) > 0.05:
        print("[FAIL] payout total does not tie to Charged Tips")
        return 1
    print("[OK] east side tips.xlsx tab 2065 updated and tied.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
