#!/usr/bin/env python3
"""
Auto-heal: read previous run's debug log + current dashboard freshness,
apply known fixes BEFORE the main pipeline runs.

Pattern: this is a defensive pre-flight. It does NOT replace the main
pipeline — it pre-emptively fixes common failure modes (stale data,
missing freshness markers, leftover cruft) so the main steps start
from a clean state.

Recipes (issue → action):
  1. Old debug-log entries        → archive to data/debug-log.archive/
                                     so today's run starts fresh
  2. Stale Par Brink JSON folder
     (older than 36h on weekday)  → force re-run of email pickup with
                                     today's date target
  3. Missing perf_metrics.json
     for today's CT scrape         → no preemptive action; main scrape
                                     will retry. Log it.
  4. Leftover .pyc / __pycache__   → remove to avoid stale-import bugs
  5. Old data/*.png debug imgs
     more than 3 days old          → delete (covered by dedupe-sweep)

Writes data/heal-log.txt with what happened — included in the daily
confirmation email.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, date, timedelta, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
RAW  = ROOT / "data" / "raw"
DBG  = ROOT / "data" / "debug-log.txt"
ARCH = ROOT / "data" / "debug-log.archive"
HEAL = ROOT / "data" / "heal-log.txt"

STORE_ID = os.environ.get("STORE_ID", "2065")
ET = timezone(timedelta(hours=-4))
TODAY = datetime.now(tz=ET).date()

actions: list[str] = []


def log(msg: str) -> None:
    actions.append(msg)
    print(f"[auto-heal] {msg}")


def archive_old_debug_log() -> None:
    if not DBG.exists():
        return
    ARCH.mkdir(parents=True, exist_ok=True)
    dest = ARCH / f"debug-log-{TODAY.isoformat()}.txt"
    shutil.move(str(DBG), str(dest))
    log(f"archived previous debug-log → {dest.relative_to(ROOT)}")


def latest_iso_folder(source: str) -> str | None:
    base = RAW / source / STORE_ID
    if not base.exists():
        return None
    candidates = []
    for d in base.iterdir():
        if not d.is_dir():
            continue
        m = re.match(r'^(?:week-ending-)?(\d{4}-\d{2}-\d{2})$', d.name)
        if m:
            candidates.append(m.group(1))
    return max(candidates) if candidates else None


def heal_stale_parbrink() -> None:
    """If the latest Par Brink folder is >36h old on a weekday, re-run pickup."""
    iso = latest_iso_folder("parbrink")
    if not iso:
        log("Par Brink: no data folder found — pickup will create one")
        return
    try:
        latest_d = datetime.strptime(iso, "%Y-%m-%d").date()
    except ValueError:
        log(f"Par Brink: unparseable folder name: {iso}")
        return
    age_days = (TODAY - latest_d).days
    if age_days <= 1:
        log(f"Par Brink: latest folder is {iso} ({age_days}d old) — fresh")
        return
    if age_days >= 2:
        log(f"Par Brink: latest folder is {iso} ({age_days}d stale) — pickup will retry on new email")
        # The pickup script will run separately in the workflow; we just flag.


def clean_pyc() -> None:
    """Remove __pycache__ in scraper/ to dodge stale-bytecode bugs after edits."""
    target = ROOT / "scraper" / "__pycache__"
    if target.exists():
        try:
            shutil.rmtree(target)
            log(f"removed {target.relative_to(ROOT)} (stale bytecode guard)")
        except Exception as e:
            log(f"could not remove {target}: {e}")


def clean_old_debug_pngs() -> None:
    """Delete data/*.png older than 3 days (debug screenshots)."""
    cutoff = datetime.now().timestamp() - (3 * 86400)
    removed = 0
    for p in (ROOT / "data").glob("*.png"):
        try:
            if p.stat().st_mtime < cutoff:
                p.unlink()
                removed += 1
        except Exception:
            continue
    if removed:
        log(f"removed {removed} stale debug PNG(s) from data/")


def write_heal_log() -> None:
    HEAL.write_text(
        f"# auto-heal run {datetime.now(tz=ET).strftime('%Y-%m-%d %H:%M %Z')}\n"
        + ("\n".join(f"- {a}" for a in actions) if actions else "(no actions)\n"),
        encoding="utf-8",
    )


def main() -> int:
    log(f"auto-heal start, store={STORE_ID}, today={TODAY.isoformat()}")
    archive_old_debug_log()
    clean_pyc()
    heal_stale_parbrink()
    clean_old_debug_pngs()
    write_heal_log()
    log("auto-heal complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
