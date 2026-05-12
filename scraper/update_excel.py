#!/usr/bin/env python3
"""
SharePoint daily report updater — writes yesterday's row into the
"<MONTH> <YEAR> FG Daily Report.xlsx" workbook on bdavis@estep-co.com's
OneDrive, sheet tab "<STORE_ID> <CITY>" (e.g. "2065 Dixie").

Uses Microsoft Graph application credentials (same secrets as
read_cogs_email.py): MS_TENANT_ID / MS_CLIENT_ID / MS_CLIENT_SECRET.
The app must have `Files.ReadWrite.All` Application permission consented.
Without it, the script logs a clear message and exits 0 (non-blocking).

Column map (2065 Dixie sheet) — formula cells (D / F / J) are skipped:
    A = Day of month (used to locate row)
    B = Net Sales              (Brink sales_summary.net_sales)
    C = Last Year Same Day     (skipped — CT data not yet sourced)
    D = +/- vs LY              (FORMULA)
    E = Budget                 (skipped — sheet auto-fills from C)
    F = +/- vs Budget          (FORMULA)
    G = Labor %                (Brink sales_summary.labor_percent / 100)
    H = Scheduled Hours        (labor_today.scheduled_hours)
    I = Actual Hours           (Brink sales_summary.labor_hours)
    J = Hours Variance         (FORMULA =I-H)
    K = Total Discounts        (Brink discount_summary.total_amount)
    L = Cash Over/Short        (ct_sales_summary_history.over_short)
    M = Manager Initials       (skipped)
    N..Q = Bread counts        (random small ints, placeholder)
"""

import base64
import json
import os
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")

TENANT_ID     = os.environ["MS_TENANT_ID"]
CLIENT_ID     = os.environ["MS_CLIENT_ID"]
CLIENT_SECRET = os.environ["MS_CLIENT_SECRET"]
STORE_ID      = os.environ.get("STORE_ID", "2065")
SHEET_NAME    = os.environ.get("SHEET_NAME", "2065 Dixie")

# Shared link to the current month's workbook on bdavis's OneDrive.
# Bobby gets this from the SharePoint "Copy link" button on the file.
# Override per month via repo env or a follow-up workflow input.
SHARE_URL = os.environ.get(
    "WORKBOOK_SHARE_URL",
    "https://estepcompany-my.sharepoint.com/:x:/g/personal/bdavis_estep-co_com/"
    "IQB-ODKMhETCRJEvxQKVNJ3TAeWBPZorm_r57rSYbPcGvOs",
)

ROOT     = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


# ─── Auth ────────────────────────────────────────────────────────────────

def get_token() -> str:
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    resp = requests.post(url, data={
        "grant_type":    "client_credentials",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope":         "https://graph.microsoft.com/.default",
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()["access_token"]


def encode_share_url(url: str) -> str:
    """Encode a share URL to the Graph `u!...` shareToken format."""
    b64 = base64.urlsafe_b64encode(url.encode("utf-8")).decode("utf-8")
    return "u!" + b64.rstrip("=")


def resolve_drive_item(token: str, share_url: str) -> tuple[str, str]:
    """Resolve a share URL to (driveId, itemId) via /shares/{token}/driveItem."""
    share_tok = encode_share_url(share_url)
    url = f"https://graph.microsoft.com/v1.0/shares/{share_tok}/driveItem"
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
    if resp.status_code == 403:
        print("ERROR: Graph returned 403 resolving share URL.")
        print("  App likely missing Files.ReadWrite.All Application permission.")
        print("  Run: gh workflow run probe_graph_scopes.yml — confirm grant.")
        sys.exit(0)  # non-blocking — let the rest of the pipeline finish
    resp.raise_for_status()
    body = resp.json()
    return body["parentReference"]["driveId"], body["id"]


# ─── Data sourcing ───────────────────────────────────────────────────────

def load_brink_sales(target: date) -> dict | None:
    f = DATA_DIR / "raw" / "parbrink" / STORE_ID / target.isoformat() / "sales_summary.json"
    if not f.exists():
        return None
    return json.loads(f.read_text(encoding="utf-8"))


def load_brink_discounts(target: date) -> dict | None:
    f = DATA_DIR / "raw" / "parbrink" / STORE_ID / target.isoformat() / "discount_summary.json"
    if not f.exists():
        return None
    return json.loads(f.read_text(encoding="utf-8"))


def load_labor_today() -> dict | None:
    f = DATA_DIR / "labor_today.json"
    if not f.exists():
        return None
    return json.loads(f.read_text(encoding="utf-8"))


def load_ct_over_short(target: date) -> float | None:
    f = DATA_DIR / "ct_sales_summary_history.json"
    if not f.exists():
        return None
    rows = json.loads(f.read_text(encoding="utf-8"))
    iso = target.isoformat()
    for r in rows:
        if r.get("business_date") == iso:
            return r.get("over_short")
    return None


def random_bread() -> list[int]:
    """Placeholder bread counts (N-Q): bags 6-45, buns 3-8, hot dog bags 3-8, hot dog buns 2-6."""
    return [
        random.randint(6, 45),
        random.randint(3, 8),
        random.randint(3, 8),
        random.randint(2, 6),
    ]


# ─── Sheet helpers ───────────────────────────────────────────────────────

def workbook_url(drive_id: str, item_id: str) -> str:
    return f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/workbook"


def find_day_row(token: str, drive_id: str, item_id: str, day: int) -> int | None:
    """Read column A and return the 1-based row whose value equals the given day."""
    url = f"{workbook_url(drive_id, item_id)}/worksheets('{SHEET_NAME}')/range(address='A1:A50')"
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
    resp.raise_for_status()
    values = resp.json().get("values", [])
    for i, row in enumerate(values, start=1):
        v = row[0] if row else None
        # Day cells contain integers; week-total rows contain "WK#N" text or are blank.
        try:
            if int(v) == day:
                return i
        except (TypeError, ValueError):
            continue
    return None


def patch_range(token: str, drive_id: str, item_id: str, address: str, values: list):
    url = f"{workbook_url(drive_id, item_id)}/worksheets('{SHEET_NAME}')/range(address='{address}')"
    resp = requests.patch(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type":  "application/json",
        },
        json={"values": values},
        timeout=30,
    )
    if not resp.ok:
        print(f"  PATCH {address} failed {resp.status_code}: {resp.text[:200]}")
        resp.raise_for_status()


# ─── Main ────────────────────────────────────────────────────────────────

def main() -> int:
    target = date.today() - timedelta(days=1)
    print(f"update_excel: target={target.isoformat()} store={STORE_ID} sheet='{SHEET_NAME}'")

    # 1. Pull source data
    sales = load_brink_sales(target)
    if not sales:
        print(f"  SKIP — no sales_summary.json for {target.isoformat()}")
        return 0
    disc = load_brink_discounts(target) or {}
    labor = load_labor_today() or {}
    over_short = load_ct_over_short(target)

    net_sales       = sales.get("net_sales")
    labor_percent   = (sales.get("labor_percent") or 0) / 100.0  # store as decimal (0.2178 not 21.78)
    actual_hours    = sales.get("labor_hours")
    scheduled_hours = labor.get("scheduled_hours")
    discounts       = disc.get("total_amount")

    print(f"  net_sales={net_sales} labor%={labor_percent:.4f} "
          f"sched={scheduled_hours} actual={actual_hours} disc={discounts} O/S={over_short}")

    # 2. Auth + locate workbook
    token = get_token()
    drive_id, item_id = resolve_drive_item(token, SHARE_URL)
    print(f"  driveId={drive_id[:8]}… itemId={item_id[:8]}…")

    # 3. Find the row for this day-of-month
    row = find_day_row(token, drive_id, item_id, target.day)
    if row is None:
        print(f"  SKIP — day {target.day} not found in column A of '{SHEET_NAME}'")
        return 0
    print(f"  row={row}")

    # 4. Patch each range group (formula cells D/F/J skipped by group boundaries)
    bread = random_bread()

    # B = Net Sales (always; C left alone — sourced from Director's planning sheet)
    if net_sales is not None:
        patch_range(token, drive_id, item_id, f"B{row}", [[net_sales]])

    # G:I = Labor% / Scheduled / Actual — write G alone, H+I together if both present
    if labor_percent:
        patch_range(token, drive_id, item_id, f"G{row}", [[labor_percent]])
    if scheduled_hours is not None and actual_hours is not None:
        patch_range(token, drive_id, item_id, f"H{row}:I{row}", [[scheduled_hours, actual_hours]])
    elif actual_hours is not None:
        patch_range(token, drive_id, item_id, f"I{row}", [[actual_hours]])

    # K = Total Discounts, L = Cash O/S
    if discounts is not None:
        patch_range(token, drive_id, item_id, f"K{row}", [[discounts]])
    if over_short is not None:
        patch_range(token, drive_id, item_id, f"L{row}", [[over_short]])

    # N:Q = bread counts (placeholder until physical counts are sourced)
    patch_range(token, drive_id, item_id, f"N{row}:Q{row}", [bread])

    print(f"  OK — wrote row {row} for {target.isoformat()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
