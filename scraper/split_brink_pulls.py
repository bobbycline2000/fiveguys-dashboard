"""
Take the localStorage-dumped Brink JSON file from Chrome (Downloads/brink_pull_all_*.json)
and split it into per-date JSON files at data/raw/parbrink/{store}/{date}/hourly_sales_labor.json
so the analyzer picks them up.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = Path.home() / "Downloads"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--store", default="2065")
    p.add_argument("--input", help="Path to dumped JSON; defaults to newest brink_pull_all*.json in Downloads")
    args = p.parse_args()

    if args.input:
        src = Path(args.input)
    else:
        candidates = sorted(DOWNLOADS.glob("brink_pull_all_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not candidates:
            print("No brink_pull_all*.json found in Downloads", file=sys.stderr)
            sys.exit(1)
        src = candidates[0]
    print(f"Reading {src}")

    data = json.loads(src.read_text())
    print(f"Loaded {len(data)} days")

    placed = 0
    for date_str, rows in data.items():
        if not rows:
            print(f"  SKIP {date_str}: empty")
            continue
        out_dir = ROOT / "data" / "raw" / "parbrink" / args.store / date_str
        out_dir.mkdir(parents=True, exist_ok=True)
        out = {
            "date": date_str,
            "store": args.store,
            "rows": rows,
            "_source": "Chrome MCP localStorage dump"
        }
        (out_dir / "hourly_sales_labor.json").write_text(json.dumps(out, indent=2))
        placed += 1
    print(f"Placed {placed} files.")


if __name__ == "__main__":
    main()
