#!/usr/bin/env python3
"""
Bulk-reorder the item sequence within a CrunchTime/NetChef Inventory Setup
storage location (= a GL/category bucket on the count sheet, and the same
sort key CrunchTime's Create Vendor Order screen uses) — lights-out, pure
`requests`, cookie-replay. No Playwright/browser needed at runtime.

Reverse-engineered 2026-08-07 for KY-2065 (see scraper/CRUNCHTIME_API.md
Section 1.6c for the full discovery writeup). Do NOT re-discover this —
read that section first if anything here needs updating.

Endpoints used:
  POST /resource/inventorysetup/products        (read current rows)
  POST /resource/inventorysetup/products/save    (write — verified live
                                                    2026-08-07, single-row
                                                    array; body is the FULL
                                                    row object with only
                                                    productSequence changed,
                                                    response
                                                    {"success":true,"contentMap":{}})

Order-guide note: CrunchTime's Create Vendor Order item grid
(POST /resource/purchasing/vendororder/edit/list/) defaults its
`simpleFilterMap.sort` to `"inv_seq"` — the same inventory-sequence concept
set here. So reordering a storage location's Sequence in Inventory Setup is
expected to also reorder that GL's section on the truck order screen, not
just the printed count sheet. Not independently re-verified after a write
in this pass (the Freestyle test write in 2026-08-07's discovery session
only touched one item, not a full section) — sanity-check the order guide
screen after a real bulk reorder the first time you use this for real.

WRITE SAFETY:
  - This script only ever changes the `productSequence` field on rows that
    already exist for the given storageId. It never adds/removes items from
    a storage location, never touches `activeFlag`/`storageActiveFlag`, and
    never creates or submits a vendor order / count.
  - Each row is saved as a single-item array POST (`[row]`), matching the
    exact shape verified live against KY-2065. Not verified whether the
    endpoint accepts a multi-row batch in one call — this script saves one
    row per POST call by design (slower, but proven-safe) with a short
    delay between calls. If Bobby wants sub-second bulk writes for a big
    section, batch-POST can be tried and verified against a low-traffic
    storage location first (see the 2026-08-07 discovery notes for the
    verification pattern used on COGS: Freestyle test row).

USAGE:
    # List current sequence for a storage location (read-only, no risk)
    python ct_reorder_gl_sequence.py --list "COGS: Walk-In Cooler"

    # Reorder by explicit product-number order (first = sequence 1, etc.)
    python ct_reorder_gl_sequence.py --storage "COGS: Walk-In Cooler" \\
        --order P00004,P00001,P00003,P00002

    # Reorder from a JSON file: {"P00004": 1, "P00001": 2, ...}
    python ct_reorder_gl_sequence.py --storage "COGS: Walk-In Cooler" \\
        --order-file new_sequence.json

    # Dry run — print what would change, write nothing
    python ct_reorder_gl_sequence.py --storage "COGS: Walk-In Cooler" \\
        --order P00004,P00001 --dry-run
"""

import argparse
import json
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from api_query import load_cookies, session_alive, remint, HEADERS as BASE_HEADERS  # noqa: E402

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"

NETCHEF_BASE = "https://fiveguysfr77.net-chef.com"
INITIALDATA_URL = f"{NETCHEF_BASE}/resource/inventorysetup/initialdata"
PRODUCTS_URL = f"{NETCHEF_BASE}/resource/inventorysetup/products"
SAVE_URL = f"{NETCHEF_BASE}/resource/inventorysetup/products/save"

HEADERS = dict(BASE_HEADERS)


def get_session():
    jar = load_cookies()
    if not session_alive(jar):
        remint()
        jar = load_cookies()
    if not session_alive(jar):
        raise RuntimeError("CT session still dead after remint — check ct_cookies.json / login flow")
    return jar


def list_storages(jar):
    r = requests.post(INITIALDATA_URL, cookies=jar, headers=HEADERS, json={}, timeout=30)
    r.raise_for_status()
    return r.json()["contentMap"]["storages"]


def resolve_storage_id(jar, storage_name_or_id):
    if isinstance(storage_name_or_id, int) or str(storage_name_or_id).isdigit():
        return int(storage_name_or_id)
    storages = list_storages(jar)
    for s in storages:
        if s["storageName"].strip().lower() == str(storage_name_or_id).strip().lower():
            return s["storageId"]
    names = ", ".join(s["storageName"] for s in storages)
    raise ValueError(f"No storage location named {storage_name_or_id!r}. Available: {names}")


def fetch_products(jar, storage_id, active_only=True):
    body = {
        "pagingInfo": {"page": 1, "start": 0, "limit": 200},
        "extraCriteriaMap": {
            "storageId": storage_id,
            "readOnly": False,
            "primaryStorageName": "Primary",
            "secondaryStorageName": "Secondary",
        },
    }
    if active_only:
        body["simpleFilterMap"] = {
            "storageActiveFlag": {"value": "Y", "filterValue": "Y", "filterType": "string"}
        }
    r = requests.post(PRODUCTS_URL, cookies=jar, headers=HEADERS, json=body, timeout=30)
    r.raise_for_status()
    j = r.json()
    return j.get("rows", [])


def save_row(jar, row, dry_run=False):
    # Strip fields the UI grid attaches (like the ExtJS store 'index' key)
    # that aren't part of the real product-storage record.
    clean = {k: v for k, v in row.items() if k != "index"}
    if dry_run:
        return {"success": True, "dryRun": True}
    r = requests.post(SAVE_URL, cookies=jar, headers=HEADERS, json=[clean], timeout=30)
    r.raise_for_status()
    return r.json()


def reorder(jar, storage_id, desired_order_by_product_number, dry_run=False, delay=0.3):
    """
    desired_order_by_product_number: dict {productNumber: new_sequence_int}
    Only rows present in this dict are changed; anything not mentioned is
    left alone (its old productSequence stays as-is).
    """
    rows = fetch_products(jar, storage_id)
    by_number = {r["productNumber"]: r for r in rows}

    missing = [pn for pn in desired_order_by_product_number if pn not in by_number]
    if missing:
        print(f"WARNING: these product numbers were not found in this storage location and will be skipped: {missing}")

    results = []
    for pn, new_seq in desired_order_by_product_number.items():
        row = by_number.get(pn)
        if not row:
            continue
        old_seq = row.get("productSequence")
        if old_seq == new_seq:
            print(f"  {pn} ({row['productName']}): already at sequence {new_seq}, skipping")
            continue
        row = dict(row)
        row["productSequence"] = new_seq
        action = "[DRY RUN] would set" if dry_run else "setting"
        print(f"  {pn} ({row['productName']}): {old_seq} -> {new_seq} — {action}")
        resp = save_row(jar, row, dry_run=dry_run)
        ok = resp.get("success", False)
        results.append({"productNumber": pn, "old": old_seq, "new": new_seq, "success": ok})
        if not ok:
            print(f"    !! save did NOT report success: {resp}")
        if not dry_run:
            time.sleep(delay)
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--storage", help="Storage location name (e.g. 'COGS: Walk-In Cooler') or its storageId")
    ap.add_argument("--list", metavar="STORAGE", help="List current sequence for a storage location and exit (read-only)")
    ap.add_argument("--order", help="Comma-separated product numbers in desired order (first = sequence 1)")
    ap.add_argument("--order-file", help="Path to a JSON file: {\"P00001\": 1, \"P00002\": 2, ...}")
    ap.add_argument("--dry-run", action="store_true", help="Print what would change, write nothing")
    ap.add_argument("--delay", type=float, default=0.3, help="Seconds to sleep between save calls (default 0.3)")
    args = ap.parse_args()

    jar = get_session()

    if args.list:
        storage_id = resolve_storage_id(jar, args.list)
        rows = fetch_products(jar, storage_id)
        rows.sort(key=lambda r: (r.get("productSequence") is None, r.get("productSequence") or 0))
        print(f"{args.list} (storageId={storage_id}) — {len(rows)} active items")
        for r in rows:
            seq = r.get("productSequence")
            seq_str = f"{seq:>6.2f}" if seq is not None else "  none"
            print(f"  {seq_str}  {r['productNumber']:<10} {r['productName']}")
        return

    if not args.storage:
        ap.error("--storage is required unless using --list")

    if args.order_file:
        desired = json.loads(Path(args.order_file).read_text())
        desired = {k: int(v) for k, v in desired.items()}
    elif args.order:
        product_numbers = [p.strip() for p in args.order.split(",") if p.strip()]
        desired = {pn: i + 1 for i, pn in enumerate(product_numbers)}
    else:
        ap.error("one of --order or --order-file is required unless using --list")

    storage_id = resolve_storage_id(jar, args.storage)
    print(f"Reordering {args.storage} (storageId={storage_id}) — {len(desired)} item(s) targeted")
    results = reorder(jar, storage_id, desired, dry_run=args.dry_run, delay=args.delay)

    failed = [r for r in results if not r["success"]]
    print(f"\nDone. {len(results)} change(s) attempted, {len(failed)} failed.")
    if failed:
        print("FAILED:", failed)
        sys.exit(1)


if __name__ == "__main__":
    main()
