"""
Parse the latest Par Brink "Hourly Sales And Labor" PDF for a store and emit
a normalized JSON file the dashboard can consume.

Reads:   data/raw/parbrink/{store}/{date}/Hourly Sales And Labor.pdf
Writes:  data/raw/parbrink/{store}/{date}/hourly_sales_labor.json

Schema:
{
  "meta": {"store_id": "2065", "report_date": "2026-04-25", "generated": "...", "source_pdf": "..."},
  "totals": {
    "net_sales": 5541.00, "guests": 1014, "guest_average": 5.46,
    "orders": 207, "order_average": 26.77,
    "labor_hours": 102.58, "labor_dollars": 1073.11, "labor_percent": 19.37,
    "avg_hourly_wage": 10.46
  },
  "hours": [
    {"hour_24": 11, "label": "11A", "net_sales": 420.08, "guests": 75, "orders": 17,
     "labor_hours": 7.00, "labor_dollars": 77.00, "labor_percent": 18.33},
    ...
  ]
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
    daily = [x for x in base.iterdir() if x.is_dir() and re.match(r'^\d{4}-\d{2}-\d{2}$', x.name)]
    for d in sorted(daily, reverse=True):
        cand = d / "Hourly Sales And Labor.pdf"
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


def to_hour24(label: str) -> int:
    """'4:00 AM' -> 4, '12:00 PM' -> 12, '1:00 PM' -> 13, '12:00 AM' -> 0."""
    m = re.match(r"(\d{1,2}):00\s*(AM|PM)", label)
    if not m:
        return -1
    h, mer = int(m.group(1)), m.group(2)
    if mer == "AM":
        return 0 if h == 12 else h
    return 12 if h == 12 else h + 12


def short_label(hour24: int) -> str:
    """11 -> '11A', 13 -> '1P', 0 -> '12A', 12 -> '12P'."""
    if hour24 == 0:
        return "12A"
    if hour24 < 12:
        return f"{hour24}A"
    if hour24 == 12:
        return "12P"
    return f"{hour24 - 12}P"


# Each hour line looks like:
#   11:00 AM $420.08 75 $5.60 17 $24.71 7.00 $77.00 18.33%
HOUR_RE = re.compile(
    r"(\d{1,2}:\d{2}\s*[AP]M)\s+"
    r"\$([\d,]+\.\d{2})\s+(\d+)\s+\$([\d,]+\.\d{2})\s+(\d+)\s+\$([\d,]+\.\d{2})\s+"
    r"([\d,]+\.\d{2})\s+\$([\d,]+\.\d{2})\s+([\d,]+\.\d{2})%"
)

# Total line:
#   Total $5,541.00 1014 $5.46 207 $26.77 102.58 $1,073.11 19.37%
TOTAL_RE = re.compile(
    r"Total\s+"
    r"\$([\d,]+\.\d{2})\s+(\d+)\s+\$([\d,]+\.\d{2})\s+(\d+)\s+\$([\d,]+\.\d{2})\s+"
    r"([\d,]+\.\d{2})\s+\$([\d,]+\.\d{2})\s+([\d,]+\.\d{2})%"
)


def parse(text: str) -> dict:
    hours = []
    for m in HOUR_RE.finditer(text):
        label = m.group(1)
        h24 = to_hour24(label)
        hours.append({
            "hour_24": h24,
            "label": short_label(h24),
            "net_sales": money(m.group(2)),
            "guests": int(m.group(3)),
            "guest_average": money(m.group(4)),
            "orders": int(m.group(5)),
            "order_average": money(m.group(6)),
            "labor_hours": float(m.group(7).replace(",", "")),
            "labor_dollars": money(m.group(8)),
            "labor_percent": float(m.group(9).replace(",", "")),
        })

    totals = {}
    tm = TOTAL_RE.search(text)
    if tm:
        labor_dollars = money(tm.group(7))
        labor_hours = float(tm.group(6).replace(",", ""))
        totals = {
            "net_sales": money(tm.group(1)),
            "guests": int(tm.group(2)),
            "guest_average": money(tm.group(3)),
            "orders": int(tm.group(4)),
            "order_average": money(tm.group(5)),
            "labor_hours": labor_hours,
            "labor_dollars": labor_dollars,
            "labor_percent": float(tm.group(8).replace(",", "")),
            "avg_hourly_wage": round(labor_dollars / labor_hours, 2) if labor_hours else 0.0,
        }

    return {"totals": totals, "hours": hours}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True)
    ap.add_argument("--pdf", help="Override path to Hourly Sales And Labor.pdf")
    args = ap.parse_args()

    pdf = Path(args.pdf) if args.pdf else latest_pdf(args.store)
    if pdf is None or not pdf.exists():
        print(f"No Hourly Sales And Labor.pdf found for store {args.store}", file=sys.stderr)
        return 1

    text = extract_text(pdf)
    parsed = parse(text)

    if not parsed["totals"] or not parsed["hours"]:
        print("WARNING: Hourly Sales And Labor parsed but missing totals or hours. Dump:", file=sys.stderr)
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

    out_path = pdf.parent / "hourly_sales_labor.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    t = parsed.get("totals", {})
    if t:
        print(
            f"  Totals: Net ${t.get('net_sales', 0):,.2f}, "
            f"Labor ${t.get('labor_dollars', 0):,.2f} ({t.get('labor_percent', 0):.2f}%), "
            f"Hrs {t.get('labor_hours', 0):.2f}, Avg wage ${t.get('avg_hourly_wage', 0):.2f}"
        )
    print(f"  Parsed {len(parsed.get('hours', []))} hour rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
