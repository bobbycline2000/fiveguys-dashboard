"""
Ingest manually-downloaded Brink "Sales and Labor Report by Hour" PDFs from
~/Downloads. Detects the report date from PDF text, files each one to
data/raw/parbrink/{store}/{date}/Hourly Sales And Labor.pdf so the analyzer
picks it up.

Usage:
  python scraper/ingest_brink_downloads.py --store 2065
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = Path.home() / "Downloads"


def extract_text(pdf_path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        print("pip install pypdf", file=sys.stderr)
        sys.exit(1)
    reader = PdfReader(str(pdf_path))
    return "\n".join(p.extract_text() or "" for p in reader.pages)


DOW_NAMES = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
MONTH_NAMES = ["January","February","March","April","May","June","July","August","September","October","November","December"]


def detect_report_date(text: str) -> str | None:
    """Find report date — 'Monday, April 27, 2026' OR 'M/D/YYYY - M/D/YYYY' (range mode shows the day twice)."""
    # Try named-date pattern first
    pat = r"(" + "|".join(DOW_NAMES) + r"),\s+(" + "|".join(MONTH_NAMES) + r")\s+(\d{1,2}),\s+(\d{4})"
    m = re.search(pat, text)
    if m:
        month = MONTH_NAMES.index(m.group(2)) + 1
        return f"{m.group(4)}-{month:02d}-{int(m.group(3)):02d}"
    # Try date-range "M/D/YYYY - M/D/YYYY" (single-day range)
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})\s*-\s*(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if m and m.group(1) == m.group(4) and m.group(2) == m.group(5) and m.group(3) == m.group(6):
        return f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--store", default="2065")
    args = p.parse_args()

    pdfs = sorted(DOWNLOADS.glob("Sales and Labor Report by Hour*.pdf"))
    print(f"Found {len(pdfs)} candidate PDFs in {DOWNLOADS}")

    placed = 0
    skipped = 0
    for pdf in pdfs:
        text = extract_text(pdf)
        date = detect_report_date(text)
        if not date:
            print(f"  SKIP {pdf.name}: no date found")
            skipped += 1
            continue
        # Store check is best-effort; trust user's manual download
        out_dir = ROOT / "data" / "raw" / "parbrink" / args.store / date
        out_dir.mkdir(parents=True, exist_ok=True)
        dest = out_dir / "Hourly Sales And Labor.pdf"
        shutil.copy2(pdf, dest)
        print(f"  PLACED {date} <- {pdf.name}")
        placed += 1

    print(f"\n=== Placed {placed} | skipped {skipped} ===")


if __name__ == "__main__":
    main()
