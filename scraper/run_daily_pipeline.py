"""
Daily pipeline: Gmail pickup → PDF parse → wire dashboard → git push

Run at 4:00 AM daily (after Par Brink emails arrive ~2:30 AM).
Logs each step and exits non-zero on any hard failure.

Usage:
  python scraper/run_daily_pipeline.py --store 2065 [--no-push] [--date YYYY-MM-DD]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRAPER = ROOT / "scraper"


def run(label: str, cmd: list[str], cwd: Path = ROOT, allow_fail: bool = False) -> int:
    print(f"\n{'='*60}", flush=True)
    print(f"  {label}", flush=True)
    print(f"{'='*60}", flush=True)
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0 and not allow_fail:
        print(f"\n[PIPELINE FAIL] {label} exited {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)
    return result.returncode


def latest_date_folder(store: str, expected_date: date | None = None) -> Path | None:
    """Return the most recent dated folder that contains a Sales Summary PDF.

    If *expected_date* is supplied, the folder's ISO date must be within 1 day
    of it.  If no qualifying folder is found the function returns None and the
    pipeline aborts rather than silently re-parsing a stale day's PDFs.

    Without *expected_date* the old "any folder with Sales Summary.pdf" logic
    applies — useful for back-fills and manual reruns with --date.
    """
    base = ROOT / "data" / "raw" / "parbrink" / store
    if not base.exists():
        return None
    folders = sorted(
        (d for d in base.iterdir() if d.is_dir() and d.name[:4].isdigit()),
        reverse=True,
    )
    for folder in folders:
        if not (folder / "Sales Summary.pdf").exists():
            continue
        if expected_date is not None:
            try:
                folder_dt = date.fromisoformat(folder.name)
            except ValueError:
                continue
            delta = abs((folder_dt - expected_date).days)
            if delta > 1:
                # This folder is too old — don't re-parse stale data.
                print(
                    f"[PIPELINE GUARD] Skipping {folder.name}: "
                    f"{delta} day(s) behind expected {expected_date} — "
                    "Par Brink email likely hasn't arrived yet. Aborting.",
                    file=sys.stderr,
                )
                return None
        return folder
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="2065")
    ap.add_argument("--no-push", action="store_true", help="Skip git push")
    ap.add_argument("--date", help="Override expected business date (YYYY-MM-DD)")
    args = ap.parse_args()

    python = sys.executable

    # Determine the business date we expect PDFs for.
    # Par Brink sends yesterday's reports ~2:30 AM, so at 4 AM we expect
    # yesterday's date.  --date overrides (useful for back-fills).
    if args.date:
        try:
            expected = date.fromisoformat(args.date)
        except ValueError:
            print(f"[PIPELINE FAIL] --date {args.date!r} is not a valid ISO date.", file=sys.stderr)
            return 1
    else:
        expected = date.today() - timedelta(days=1)

    print(f"\nExpected business date: {expected}")

    # ── Step 1: Gmail pickup ─────────────────────────────────────────────────
    run(
        "Step 1/5 — Gmail pickup (Par Brink daily email)",
        [python, str(SCRAPER / "parbrink_email_pickup.py"), "--store", args.store, "--mode", "daily"],
        allow_fail=True,  # old email already downloaded → exit 1 is OK
    )

    # ── Step 2: Locate PDFs ───────────────────────────────────────────────────
    folder = latest_date_folder(args.store, expected_date=expected)
    if folder is None:
        print(
            f"[PIPELINE ABORT] No Par Brink PDFs found for {expected} "
            "(email may not have arrived yet — the 9 AM GitHub Actions run will retry).",
            file=sys.stderr,
        )
        return 1
    print(f"\nUsing PDF folder: {folder}")

    sales_pdf = folder / "Sales Summary.pdf"
    discounts_pdf = folder / "Discount Summary.pdf"
    hourly_pdf = folder / "Hourly Sales And Labor.pdf"

    # ── Step 3: Parse PDFs ────────────────────────────────────────────────────
    if sales_pdf.exists():
        run(
            "Step 2/5 — Parse Sales Summary",
            [python, str(SCRAPER / "parbrink_parse_sales_summary.py"),
             "--store", args.store, "--pdf", str(sales_pdf)],
        )
    else:
        print(f"WARNING: Sales Summary.pdf missing in {folder} — skipping")

    if discounts_pdf.exists():
        run(
            "Step 3/5 — Parse Discount Summary",
            [python, str(SCRAPER / "parbrink_parse_discounts.py"),
             "--store", args.store, "--pdf", str(discounts_pdf)],
            allow_fail=True,
        )
    else:
        print(f"WARNING: Discount Summary.pdf missing in {folder} — skipping")

    if hourly_pdf.exists():
        run(
            "Step 4/5 — Parse Hourly Sales And Labor",
            [python, str(SCRAPER / "parbrink_parse_hourly_sales_labor.py"),
             "--store", args.store, "--pdf", str(hourly_pdf)],
            allow_fail=True,
        )
    else:
        print(f"WARNING: Hourly Sales And Labor.pdf missing in {folder} — skipping")

    # ── Step 4a: Compute WTD/MTD/QTD rollups from Par Brink history ──────────
    run(
        "Step 4a/5 — Compute Par Brink period rollups (WTD/MTD/QTD)",
        [python, str(SCRAPER / "aggregate_periods.py"), "--store", args.store],
        allow_fail=True,
    )

    # ── Step 4b: Wire dashboard ───────────────────────────────────────────────
    run(
        "Step 4b/5 — Wire dashboard",
        [python, str(SCRAPER / "wire_dashboard.py")],
    )

    # ── Step 5: Verify ────────────────────────────────────────────────────────
    run(
        "Step 5/5 — Verify dashboard freshness",
        [python, str(SCRAPER / "verify_dashboard.py")],
        allow_fail=True,
    )

    # ── Step 6: Git push ──────────────────────────────────────────────────────
    if not args.no_push:
        print(f"\n{'='*60}")
        print(f"  Step 6/6 — Git commit + push")
        print(f"{'='*60}")
        today = date.today().isoformat()
        subprocess.run(
            ["git", "add", "dashboard.html", "data/latest.json"],
            cwd=ROOT,
        )
        subprocess.run(
            ["git", "commit", "-m", f"[auto] Par Brink daily pipeline {today}"],
            cwd=ROOT,
        )
        subprocess.run(["git", "push"], cwd=ROOT)
        print("\nPushed to origin/main — GitHub Pages will update in ~60s.")
    else:
        print("\n[--no-push] Skipping git push.")

    print("\nPipeline complete.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
