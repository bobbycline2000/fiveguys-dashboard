"""
Parse the latest Par Brink "Sales Summary" PDF for a store and emit a
normalized JSON file the dashboard can consume.

Reads:   data/raw/parbrink/{store}/{date}/Sales Summary.pdf
Writes:  data/raw/parbrink/{store}/{date}/sales_summary.json

Schema (only the fields the dashboard actually reads today; expand as needed):
{
  "meta": {"store_id": "2065", "report_date": "2026-04-25", "generated": "...", "source_pdf": "..."},
  "gross_sales": 5644.84,
  "net_sales": 5541.00,
  "order_count": 207,
  "guest_count": 1014,
  "order_average": 26.77,
  "labor_cost": 1073.11,
  "labor_hours": 102.58,
  "labor_percent": 19.37
}
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def latest_pdf(store_id: str) -> Path | None:
    base = ROOT / "data" / "raw" / "parbrink" / store_id
    if not base.exists():
        return None
    # Only consider daily folders (YYYY-MM-DD); skip week-ending-* (weekly aggregates)
    daily = [x for x in base.iterdir() if x.is_dir() and re.match(r'^\d{4}-\d{2}-\d{2}$', x.name)]
    for d in sorted(daily, reverse=True):
        cand = d / "Sales Summary.pdf"
        if cand.exists():
            return cand
    return None


def extract_text(pdf_path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        print("ERROR: pypdf not installed. Run: pip install pypdf", file=sys.stderr)
        sys.exit(1)
    reader = PdfReader(str(pdf_path))
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text(extraction_mode="layout") or "")
        except TypeError:
            parts.append(page.extract_text() or "")
    return "\n".join(parts)


def money(s: str) -> float:
    return float(s.replace("$", "").replace(",", ""))


def find(pattern: str, text: str, group: int = 1, default=None):
    m = re.search(pattern, text)
    return m.group(group) if m else default


def parse(text: str) -> dict:
    out = {}
    gross = find(r'Gross Sales\s+\$([\d,]+\.\d{2})', text)
    net = find(r'Net Sales\s+\$([\d,]+\.\d{2})', text)
    order_count = find(r'Order Count:\s+(\d+)', text)
    guest_count = find(r'Guest Count:\s+(\d+)', text)
    order_avg = find(r'Order Average:\s+\$([\d,]+\.\d{2})', text)
    labor_cost = find(r'Labor Cost:\s+\$([\d,]+\.\d{2})', text)
    labor_hours = find(r'Labor Hours:\s+([\d,]+\.\d{2})', text)
    labor_pct = find(r'Labor Percent:\s+([\d,]+\.\d{2})%', text)

    if gross is not None:
        out["gross_sales"] = money(gross)
    if net is not None:
        out["net_sales"] = money(net)
    if order_count is not None:
        out["order_count"] = int(order_count)
    if guest_count is not None:
        out["guest_count"] = int(guest_count)
    if order_avg is not None:
        out["order_average"] = money(order_avg)
    if labor_cost is not None:
        out["labor_cost"] = money(labor_cost)
    if labor_hours is not None:
        out["labor_hours"] = float(labor_hours.replace(",", ""))
    if labor_pct is not None:
        out["labor_percent"] = float(labor_pct.replace(",", ""))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True)
    ap.add_argument("--pdf", help="Override path to Sales Summary.pdf")
    args = ap.parse_args()

    pdf = Path(args.pdf) if args.pdf else latest_pdf(args.store)
    if pdf is None or not pdf.exists():
        print(f"No Sales Summary.pdf found for store {args.store}", file=sys.stderr)
        return 1

    text = extract_text(pdf)
    parsed = parse(text)

    if "order_count" not in parsed or "guest_count" not in parsed:
        print(f"WARNING: Sales Summary parsed but missing order/guest counts. Dump:", file=sys.stderr)
        print(text[:600], file=sys.stderr)

    report_date = pdf.parent.name
    out = {
        "meta": {
            "store_id": args.store,
            "report_date": report_date,
            "generated": datetime.now().isoformat(timespec="seconds"),
            "source_pdf": str(pdf.relative_to(ROOT)).replace("\\", "/"),
        },
        **parsed,
    }

    out_path = pdf.parent / "sales_summary.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    if "order_count" in parsed:
        print(f"  Orders: {parsed['order_count']}, Guests: {parsed.get('guest_count', '—')}, Net: ${parsed.get('net_sales', 0):,.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
