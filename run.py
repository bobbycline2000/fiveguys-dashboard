"""
run.py — Single entry point for the Five Guys dashboard system.

Usage:
    python run.py              # uses STORE_ID from .env (default: 2065)
    python run.py 2065         # explicit store ID
    python run.py 2065 2066    # run multiple stores in sequence

Reads credentials from .env (or environment variables).
Reads store config from config/<STORE_ID>.json.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# ── load .env if present ───────────────────────────────────────────────────────
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

ROOT     = Path(__file__).parent
CONFIG   = ROOT / "config"
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def load_config(store_id: str) -> dict:
    cfg_path = CONFIG / f"{store_id}.json"
    if not cfg_path.exists():
        raise FileNotFoundError(f"No config found for store {store_id} — expected {cfg_path}")
    cfg = json.loads(cfg_path.read_text())
    cfg.pop("_instructions", None)
    return cfg


async def run_store(store_id: str):
    log.info(f"\n{'='*60}")
    log.info(f"  Running store {store_id}")
    log.info(f"{'='*60}")

    cfg = load_config(store_id)
    log.info(f"  Store: {cfg['store_name']}")

    # Pass config to scrapers via env vars so existing scripts work unchanged
    os.environ["STORE_ID"] = store_id

    # ── ComplianceMate scrape FIRST (dashboard.html will include fresh CM data) ─
    log.info("\n--- ComplianceMate ---")
    try:
        from scraper.scrape_compliancemate import scrape as cm_scrape
        cm_data = await cm_scrape()
        out = DATA_DIR / "compliancemate.json"
        out.write_text(json.dumps(cm_data, indent=2))
        log.info(f"ComplianceMate: {cm_data['meta']['status']} — {len(cm_data.get('lists', []))} lists")
    except Exception as e:
        log.error(f"ComplianceMate scrape failed: {e}")

    # ── KnowledgeForce (Secret Shops) ──────────────────────────────────────────
    log.info("\n--- KnowledgeForce (Secret Shops) ---")
    try:
        from scraper.scrape_knowledgeforce import scrape as ss_scrape
        ss_data = await ss_scrape()
        out = DATA_DIR / "secret_shops.json"
        out.write_text(json.dumps(ss_data, indent=2))
        log.info(f"Secret Shops: {ss_data['meta']['status']} — {ss_data['meta']['shops_total']} shops")
    except Exception as e:
        log.error(f"KnowledgeForce scrape failed: {e}")

    # ── Par Brink emailed reports (reads Gmail inbox) ──────────────────────────
    log.info("\n--- Par Brink (Gmail) ---")
    try:
        from scraper.read_parbrink_email import run as pb_run
        pb_run()
    except Exception as e:
        log.error(f"Par Brink email read failed: {e}")

    # ── Teamworx (scaffold — URL still TODO) ───────────────────────────────────
    log.info("\n--- Teamworx ---")
    try:
        from scraper.scrape_teamworx import run as tw_run
        tw_run()
    except Exception as e:
        log.error(f"Teamworx scrape failed: {e}")

    # ── CrunchTime scrape + generate dashboard.html (reads fresh CM data) ──────
    log.info("\n--- CrunchTime Net Chef ---")
    try:
        from scraper.main import main as ct_main
        await ct_main()
    except Exception as e:
        log.error(f"CrunchTime scrape failed: {e}")

    # ── Wire fresh data into dashboard.html (idempotent) ───────────────────────
    # main.py only writes data/latest.json; without this step the HTML stays
    # stale forever. Fixed 2026-04-24 after dashboard silently froze.
    log.info("\n--- Wire dashboard ---")
    import subprocess
    wire_rc = subprocess.run(
        [sys.executable, str(ROOT / "scraper" / "wire_dashboard.py")],
        cwd=ROOT,
    ).returncode
    if wire_rc != 0:
        log.error(f"wire_dashboard.py exited {wire_rc} — check data/debug-log.txt")

    # ── Verify dashboard actually reflects latest.json (backup gate) ───────────
    log.info("\n--- Verify dashboard freshness ---")
    verify_rc = subprocess.run(
        [sys.executable, str(ROOT / "scraper" / "verify_dashboard.py")],
        cwd=ROOT,
    ).returncode
    if verify_rc != 0:
        log.error("verify_dashboard.py detected stale dashboard — details in data/debug-log.txt")

    # ── Excel update ───────────────────────────────────────────────────────────
    log.info("\n--- SharePoint Excel ---")
    try:
        from scraper.update_excel import run as xl_run
        xl_run(os.getenv("STORE_ID", "2065"))
    except (Exception, SystemExit) as e:
        log.error(f"Excel update failed (no Azure credentials configured — skipping): {e}")

    # ── Discord daily brief post ───────────────────────────────────────────────
    log.info("\n--- Discord Daily Brief ---")
    try:
        from post_daily_brief import post as post_brief
        post_brief()
    except Exception as e:
        log.error(f"Discord brief post failed: {e}")

    log.info(f"\nDone — store {store_id} complete.")
    log.info(f"Dashboard: {ROOT / 'dashboard.html'}")


def main():
    store_ids = sys.argv[1:] if len(sys.argv) > 1 else [os.getenv("STORE_ID", "2065")]
    for sid in store_ids:
        asyncio.run(run_store(sid))


if __name__ == "__main__":
    main()
