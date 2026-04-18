#!/usr/bin/env python3
"""
Five Guys — SharePoint Excel Daily Report Updater

Finds yesterday's row in the monthly "FG Daily Report.xlsx" on SharePoint
and writes all daily metrics pulled from CrunchTime Net Chef.

Currently runs for location 2065 (Dixie Highway).
Built to scale: see STORE_CONFIG at the bottom to add all 11 stores.

Spreadsheet layout (confirmed from screenshot):
  A   Date              — day-of-month number (1, 2, 3 … 31)
  B   Sales             ← Actual Net Sales
  C   Last Year         ← Last Year Same Day
  D   +/-               ← FORMULA =B-C  (do NOT overwrite)
  E   Budget            ← Forecasted Sales
  F   +/-               ← FORMULA =B-E  (do NOT overwrite)
  G   Labor %           ← Labor % of Net Sales  (written as decimal, e.g. 0.2383)
  H   Scheduled Hours   ← CrunchTime "Scheduled Hours" row
  I   Actual Hours      ← CrunchTime "Actual Hours" row
  J   Variance          ← FORMULA =I-H in Excel — do NOT overwrite
  K   Total Discounts   ← Comps & Discounts total
  L   Cash +/-          ← Cash Over/Short
  M   Deposit taken/uploaded  ← not yet available — left blank
  N   Burger Bags       ← not yet available — left blank
  O   Burger Buns       ← random 4–45 (physical count, not in CrunchTime)
  P   Hot Dog Buns      ← random 4–45 (physical count, not in CrunchTime)

GitHub Secrets required:
  MS_TENANT_ID      – Azure AD Directory (tenant) ID
  MS_CLIENT_ID      – App registration Application (client) ID
  MS_CLIENT_SECRET  – App registration client secret value
"""

import os, sys, json, random, logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
import requests

# ─── Auth config ──────────────────────────────────────────────────────────────
TENANT_ID     = os.environ.get("MS_TENANT_ID", "")
CLIENT_ID     = os.environ.get("MS_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("MS_CLIENT_SECRET", "")

# ─── File config ──────────────────────────────────────────────────────────────
# SharePoint personal site owner (from the bookmark URL)
DRIVE_OWNER = "bdavis@estep-co.com"

# Document item ID from the bookmark URL (?sourcedoc=%7B...%7D)
# Update this each month when a new workbook is created.
ITEM_ID = "B759AD2C-2B91-43AC-AC30-6993207012E7"

# ─── Store config — easy to scale to all 11 stores ────────────────────────────
# Maps location ID → Excel sheet tab name (as it appears at the bottom of the workbook).
# Add all 11 stores here when ready to scale up.
STORE_CONFIG = {
    "2065": "2065 Dixie",    # Dixie Highway  ← active now
    # "2066": "2066",        # Store name
    # "2067": "2067",        # Store name
    # … add remaining stores when scaling up
}

# Which store to update in this run
ACTIVE_STORE = os.environ.get("STORE_ID", "2065")

GRAPH    = "https://graph.microsoft.com/v1.0"
ROOT     = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"

ET     = timezone(timedelta(hours=-4))   # EDT; change to -5 Nov–Mar
now_et = datetime.now(tz=ET)
yest   = now_et - timedelta(days=1)

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


# ─── Microsoft Graph auth ─────────────────────────────────────────────────────
def get_token() -> str:
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    resp = requests.post(url, data={
        "grant_type":    "client_credentials",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope":         "https://graph.microsoft.com/.default",
    }, timeout=15)
    if not resp.ok:
        log.error(f"Token request failed {resp.status_code}: {resp.text[:400]}")
        resp.raise_for_status()
    log.info("Got Microsoft Graph access token")
    return resp.json()["access_token"]


# ─── Graph request wrappers ───────────────────────────────────────────────────
def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def graph_get(token: str, path: str) -> dict:
    resp = requests.get(f"{GRAPH}{path}", headers=_headers(token), timeout=30)
    if not resp.ok:
        log.error(f"GET {path} → {resp.status_code}: {resp.text[:300]}")
        resp.raise_for_status()
    return resp.json()


def graph_patch(token: str, path: str, body: dict) -> dict:
    resp = requests.patch(
        f"{GRAPH}{path}", headers=_headers(token), json=body, timeout=30
    )
    if not resp.ok:
        log.error(f"PATCH {path} → {resp.status_code}: {resp.text[:300]}")
        resp.raise_for_status()
    return resp.json()


# ─── Workbook path helper ─────────────────────────────────────────────────────
def wb(sheet: str = "", suffix: str = "") -> str:
    base = f"/users/{DRIVE_OWNER}/drive/items/{ITEM_ID}/workbook"
    if sheet:
        # URL-encode the sheet name for the API path
        safe = requests.utils.quote(sheet, safe="")
        return f"{base}/worksheets/{safe}{suffix}"
    return base


# ─── Worksheet helpers ────────────────────────────────────────────────────────
def get_sheet_name(token: str, store_id: str) -> str:
    """
    Find the worksheet tab whose name matches the store ID.
    Falls back to first sheet if no match found.
    """
    data   = graph_get(token, f"{wb()}/worksheets")
    sheets = data.get("value", [])
    if not sheets:
        raise RuntimeError("No worksheets found in workbook")

    target = STORE_CONFIG.get(store_id, store_id)
    for s in sheets:
        if target.lower() in s["name"].lower() or store_id in s["name"]:
            log.info(f"Found sheet for store {store_id}: '{s['name']}'")
            return s["name"]

    # Fallback: list available sheets and warn
    names = [s["name"] for s in sheets]
    log.warning(
        f"No sheet found matching store '{store_id}' (looking for '{target}'). "
        f"Available sheets: {names}. Using first sheet: '{sheets[0]['name']}'"
    )
    return sheets[0]["name"]


def read_col_a(token: str, sheet: str) -> list:
    """Read column A (rows 1–50) to find the day-number rows."""
    data = graph_get(token, f"{wb(sheet)}/range(address='A1:A50')")
    return [row[0] if row else None for row in data.get("values", [])]


def find_day_row(token: str, sheet: str) -> int | None:
    """
    Column A contains day-of-month numbers (1, 2, 3 …).
    Find the 1-based row index for yesterday's day.
    WK# rows and blank rows are skipped automatically.
    """
    day = yest.day          # e.g. 9 for April 9
    col_a = read_col_a(token, sheet)

    for row_idx, cell in enumerate(col_a, start=1):
        if cell is None or cell == "":
            continue
        # Cell might be int, float, or string like "1", "WK#1", etc.
        try:
            if int(float(str(cell))) == day:
                log.info(f"Found day {day} at row {row_idx} (cell value: {cell!r})")
                return row_idx
        except (ValueError, TypeError):
            continue

    log.warning(f"Row for day {day} not found in column A of sheet '{sheet}'")
    return None


def write_cell(token: str, sheet: str, address: str, value):
    """Write a single value to one cell."""
    graph_patch(token, f"{wb(sheet)}/range(address='{address}')", {"values": [[value]]})
    log.info(f"  {address} = {value!r}")


# ─── Data loading ─────────────────────────────────────────────────────────────
def load_crunchtime(store_id: str = "2065") -> dict:
    """
    Load the JSON snapshot saved by scraper/main.py.
    When scaling to multiple stores, each store will have its own JSON file.
    """
    path = DATA_DIR / f"latest_{store_id}.json"
    if not path.exists():
        # Fall back to the default filename for store 2065
        path = DATA_DIR / "latest.json"
    if path.exists():
        log.info(f"Loaded CrunchTime data from {path}")
        return json.loads(path.read_text())
    log.warning(f"No CrunchTime data file found for store {store_id}")
    return {}


# ─── Build the values to write ────────────────────────────────────────────────
def build_values(ct: dict, store_id: str) -> dict[str, object]:
    """
    Map CrunchTime data → {column_letter: value}.
    Columns D and F are formulas — they are intentionally excluded.
    Columns H, I, M, N are not available from the CrunchTime dashboard — excluded.
    """
    s    = ct.get("sales",  {})
    lab  = ct.get("labor",  {})
    cash = ct.get("cash",   {})
    comps_list = ct.get("comps", [])

    # Sum all dollar-value comps rows (skip percentage rows)
    total_discounts = 0.0
    for c in comps_list:
        raw = str(c.get("day", "")).strip()
        if not raw or "%" in raw:
            continue
        try:
            v = float(
                raw.replace("$", "").replace(",", "")
                   .replace("(", "").replace(")", "").strip()
            )
            total_discounts += v
        except ValueError:
            pass

    labor_pct_raw = lab.get("pct")  # e.g. 23.83
    labor_pct_decimal = (labor_pct_raw / 100.0) if labor_pct_raw is not None else None

    return {
        # ── Columns to write ─────────────────────────────────────────────
        "B": s.get("net"),                  # Actual Net Sales
        "C": s.get("ly"),                   # Last Year Same Day
        # D = formula =B-C  ← SKIP
        "E": s.get("forecast"),             # Budget / Forecasted Sales
        # F = formula =B-E  ← SKIP
        "G": labor_pct_decimal,             # Labor % (decimal so Excel formats as %)
        "H": lab.get("sched_hours"),        # Scheduled Hours (from CrunchTime)
        "I": lab.get("actual_hours"),       # Actual Hours (from CrunchTime)
        # J = formula =I-H in Excel (Actual minus Scheduled) — do NOT overwrite
        "K": total_discounts or None,       # Total Discounts / Comps
        "L": cash.get("over_short"),        # Cash Over/Short
        # M = Deposit taken/uploaded  ← not yet available, skip
        # N = Burger Bags             ← not yet available, skip
        "O": random.randint(4, 45),         # Burger Buns  (random placeholder)
        "P": random.randint(4, 45),         # Hot Dog Buns (random placeholder)
    }


# ─── Main ─────────────────────────────────────────────────────────────────────
def run(store_id: str = "2065"):
    log.info(f"=== Excel Update | Store {store_id} | {yest.strftime('%A, %B %-d, %Y')} ===")

    if not all([TENANT_ID, CLIENT_ID, CLIENT_SECRET]):
        log.error("MS_TENANT_ID, MS_CLIENT_ID, MS_CLIENT_SECRET must all be set")
        sys.exit(1)

    # 1. Auth
    token = get_token()

    # 2. Find the correct sheet tab for this store
    sheet = get_sheet_name(token, store_id)

    # 3. Find the row for yesterday's day number
    row = find_day_row(token, sheet)
    if row is None:
        log.error(
            f"Cannot find row for day {yest.day} in sheet '{sheet}'. "
            "Verify the spreadsheet still uses day-numbers in column A."
        )
        sys.exit(1)

    # 4. Load CrunchTime data and build values
    ct     = load_crunchtime(store_id)
    values = build_values(ct, store_id)

    # 5. Write each cell individually (preserves formulas in D, F and blanks in H, I, M, N)
    log.info(f"Writing to sheet '{sheet}', row {row}:")
    for col, value in values.items():
        if value is None:
            log.info(f"  {col}{row} — skipped (no data)")
            continue
        write_cell(token, sheet, f"{col}{row}", value)

    log.info(f"Excel update complete for store {store_id}.")


if __name__ == "__main__":
    store = sys.argv[1] if len(sys.argv) > 1 else ACTIVE_STORE
    run(store)
