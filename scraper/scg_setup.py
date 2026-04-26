"""
Savior Consulting Group Dashboard — first-install setup wizard.

Run this ONCE on a new install. It will:
  1. Ask the customer for their store ID and store name
  2. Generate config/{store_id}.json from the template
  3. Open a browser window for the customer to grant Gmail access
  4. Save a per-machine refresh token to secrets/scg_refresh_token.json

After this completes, the daily report pickup runs automatically — no further
customer interaction required.

This is the wizard the customer sees. Keep prompts in plain English.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "config"
TEMPLATE = CONFIG_DIR / "template.json"
SECRETS_DIR = REPO_ROOT / "secrets"
CLIENT_FILE = SECRETS_DIR / "scg_oauth_client.json"
TOKEN_FILE = SECRETS_DIR / "scg_refresh_token.json"
REQUIREMENTS = REPO_ROOT / "scraper" / "requirements.txt"


def banner() -> None:
    print()
    print("  ===========================================================")
    print("    Savior Consulting Group Dashboard — First-Install Setup")
    print("  ===========================================================")
    print()
    print("  This wizard will get your store connected. Takes about 2 minutes.")
    print("  You'll need:")
    print("    - Your store number (e.g., 2065)")
    print("    - The Gmail address that receives Par Brink scheduled reports")
    print()


def ask(prompt: str, validator=None, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        raw = input(f"  {prompt}{suffix}: ").strip()
        if not raw and default is not None:
            raw = default
        if not raw:
            print("    -> required, please enter a value")
            continue
        if validator:
            err = validator(raw)
            if err:
                print(f"    -> {err}")
                continue
        return raw


def validate_store_id(s: str) -> str | None:
    if not re.fullmatch(r"\d{2,6}", s):
        return "store ID should be digits only, e.g., 2065"
    return None


def validate_email(s: str) -> str | None:
    if "@" not in s or "." not in s.split("@", 1)[1]:
        return "doesn't look like an email address"
    return None


def install_dependencies() -> None:
    print()
    print("  [1/4] Installing required Python packages...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", "-r", str(REQUIREMENTS)]
        )
        print("        Done.")
    except subprocess.CalledProcessError as e:
        print(f"        ERROR: pip install failed (exit {e.returncode}).")
        print("        Make sure Python is installed and you have internet access.")
        sys.exit(1)


def write_store_config(store_id: str, store_name: str) -> Path:
    print()
    print(f"  [2/4] Creating store config for {store_id}...")
    if not TEMPLATE.exists():
        print(f"        ERROR: template missing at {TEMPLATE}. Reinstall the package.")
        sys.exit(1)
    cfg = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    cfg.pop("_instructions", None)
    cfg["store_id"] = store_id
    cfg["store_name"] = store_name
    if "excel" in cfg and isinstance(cfg["excel"], dict):
        cfg["excel"]["sheet_tab"] = store_id
    if "compliancemate" in cfg and isinstance(cfg["compliancemate"], dict):
        cfg["compliancemate"]["location_id"] = store_id
    if "crunchtime" in cfg and isinstance(cfg["crunchtime"], dict):
        cfg["crunchtime"]["location_id"] = store_id

    out = CONFIG_DIR / f"{store_id}.json"
    if out.exists():
        ans = input(f"    {out.name} already exists. Overwrite? [y/N]: ").strip().lower()
        if ans != "y":
            print("    Keeping existing config.")
            return out
    out.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    print(f"        Wrote {out}")
    return out


def run_oauth(store_id: str) -> None:
    print()
    print("  [3/4] Opening your browser to connect Gmail...")
    print("        - Sign in with the Gmail account where Par Brink reports arrive")
    print("        - You'll see an 'unverified app' warning — click Advanced,")
    print("          then 'Go to Savior Consulting Group Dashboard (unsafe)'")
    print("        - Allow both Gmail permissions, then close the browser tab")
    print()
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scraper" / "parbrink_email_pickup.py"),
        "--store",
        store_id,
        "--setup",
    ]
    rc = subprocess.call(cmd)
    if rc != 0 or not TOKEN_FILE.exists():
        print()
        print("        ERROR: Gmail connection did not finish.")
        print("        You can re-run this wizard to try again.")
        sys.exit(1)
    print(f"        Gmail connected. Token saved to {TOKEN_FILE.name}.")


def verify(store_id: str) -> None:
    print()
    print("  [4/4] Verifying setup...")
    cfg = CONFIG_DIR / f"{store_id}.json"
    checks = [
        (CLIENT_FILE.exists(), f"OAuth client present ({CLIENT_FILE.name})"),
        (TOKEN_FILE.exists(), f"Refresh token saved ({TOKEN_FILE.name})"),
        (cfg.exists(), f"Store config present ({cfg.name})"),
    ]
    for ok, label in checks:
        mark = "OK" if ok else "MISSING"
        print(f"        [{mark}] {label}")
    if not all(ok for ok, _ in checks):
        print()
        print("        ERROR: setup incomplete. Re-run this wizard.")
        sys.exit(1)


def finished(store_id: str, gmail: str) -> None:
    print()
    print("  ===========================================================")
    print("    Setup complete!")
    print("  ===========================================================")
    print()
    print(f"  Store:   {store_id}")
    print(f"  Gmail:   {gmail}")
    print()
    print("  Tomorrow morning at ~2:30 AM the daily Par Brink reports email")
    print(f"  will land in {gmail}, and the dashboard will pick them up")
    print("  automatically.")
    print()
    print("  Test a manual run any time:")
    print(f"    python scraper\\parbrink_email_pickup.py --store {store_id}")
    print()


def main() -> int:
    banner()
    if not CLIENT_FILE.exists():
        print(f"  ERROR: missing OAuth client file at {CLIENT_FILE}")
        print("  This file ships with the SCG Dashboard package. Reinstall.")
        return 1

    store_id = ask("Store number (digits only, e.g., 2065)", validator=validate_store_id)
    store_name = ask(
        "Store display name (e.g., 'KY-2065 Dixie Highway')",
        default=f"Store {store_id}",
    )
    gmail = ask(
        "Gmail address that receives Par Brink reports",
        validator=validate_email,
    )

    install_dependencies()
    write_store_config(store_id, store_name)
    run_oauth(store_id)
    verify(store_id)
    finished(store_id, gmail)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n  Setup cancelled.")
        sys.exit(130)
