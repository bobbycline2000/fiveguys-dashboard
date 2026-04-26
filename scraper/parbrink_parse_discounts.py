"""
Parse the latest Par Brink "Discount Summary" PDF for a store and emit a
normalized JSON file the dashboard can consume.

Reads:   data/raw/parbrink/{store}/{date}/Discount Summary.pdf
Writes:  data/raw/parbrink/{store}/{date}/discount_summary.json

Schema:
{
  "meta": {"store_id": "2065", "report_date": "2026-04-25", "generated": "..."},
  "items": [{"name": "Employee 100%", "count": 8, "total": 103.84, "average": 12.98, "type": "Discount"}],
  "total_count": 8,
  "total_amount": 103.84,
  "total_average": 12.98,
  "comps_total": 0.0,
  "discounts_total": 103.84
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


COMP_NAMES = {"Item Comp", "100% Mgr Promo AI", "100% Mrg/PR", "Manager Meal 100%", "No Show"}

LINE_RE = re.compile(r'^(?P<name>.+?)\s+(?P<count>\d+)\s+\$(?P<total>[\d,]+\.\d{2})(?:\s+\$(?P<avg>[\d,]+\.\d{2}))?\s*$')
TOTAL_RE = re.compile(r'^Total\s+(?P<count>\d+)\s+\$(?P<total>[\d,]+\.\d{2})\s+\$(?P<avg>[\d,]+\.\d{2})\s*$', re.IGNORECASE)


def latest_pdf(store_id: str) -> Path | None:
    base = ROOT / "data" / "raw" / "parbrink" / store_id
    if not base.exists():
        return None
    dated = sorted([d for d in base.iterdir() if d.is_dir()], reverse=True)
    for d in dated:
        cand = d / "Discount Summary.pdf"
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
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def parse(text: str) -> dict:
    items: list[dict] = []
    grand_total = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("Discount Summary", "Discount", "Page", "KY-")):
            continue
        if "Time (US" in line or "/" in line[:11] and ":" in line[:13]:
            continue
        m = TOTAL_RE.match(line)
        if m:
            grand_total = {
                "count": int(m.group("count")),
                "total": float(m.group("total").replace(",", "")),
                "average": float(m.group("avg").replace(",", "")),
            }
            continue
        m = LINE_RE.match(line)
        if not m:
            continue
        name = m.group("name").strip()
        if name.lower() == "discount":
            continue
        count = int(m.group("count"))
        total = float(m.group("total").replace(",", ""))
        avg_raw = m.group("avg")
        average = float(avg_raw.replace(",", "")) if avg_raw else (round(total / count, 2) if count else 0.0)
        items.append({
            "name": name,
            "count": count,
            "total": total,
            "average": average,
            "type": "Comp" if name in COMP_NAMES else "Discount",
        })
    return {"items": items, "grand_total": grand_total}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True)
    ap.add_argument("--pdf", help="Override path to Discount Summary.pdf")
    args = ap.parse_args()

    pdf = Path(args.pdf) if args.pdf else latest_pdf(args.store)
    if pdf is None or not pdf.exists():
        print(f"No Discount Summary.pdf found for store {args.store}", file=sys.stderr)
        return 1

    text = extract_text(pdf)
    parsed = parse(text)

    items = parsed["items"]
    discounts_total = sum(it["total"] for it in items if it["type"] == "Discount")
    comps_total = sum(it["total"] for it in items if it["type"] == "Comp")
    total_count = sum(it["count"] for it in items)
    total_amount = sum(it["total"] for it in items)
    total_average = round(total_amount / total_count, 2) if total_count else 0.0

    report_date = pdf.parent.name
    out = {
        "meta": {
            "store_id": args.store,
            "report_date": report_date,
            "generated": datetime.now().isoformat(timespec="seconds"),
            "source_pdf": str(pdf.relative_to(ROOT)).replace("\\", "/"),
        },
        "items": items,
        "total_count": total_count,
        "total_amount": round(total_amount, 2),
        "total_average": total_average,
        "comps_total": round(comps_total, 2),
        "discounts_total": round(discounts_total, 2),
    }

    out_path = pdf.parent / "discount_summary.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"  {len(items)} line items, {total_count} redemptions, ${total_amount:.2f} total")
    return 0


if __name__ == "__main__":
    sys.exit(main())
