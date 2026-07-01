"""
Par Brink scheduled-report email pickup.

Reads the latest 'Promethus Reports' (daily) or 'Prometheus Weekly reports' (weekly)
email from the customer's Gmail inbox, validates it, and downloads all PDF
attachments to data/raw/parbrink/{store_id}/{business-date}/.

Designed as a sellable / install-anywhere component of the Savior Consulting
Group dashboard:

  - One OAuth client (secrets/scg_oauth_client.json) ships with the product.
  - Each customer install runs this script's --setup mode once. That triggers
    a browser OAuth flow against the customer's own Gmail account and saves
    a per-machine refresh token at secrets/scg_refresh_token.json.
  - Daily runs reuse the saved refresh token. No password, no app password,
    no user interaction.

Usage:
  python scraper/parbrink_email_pickup.py --store 2065 [--mode daily|weekly] [--setup]

Exit codes:
  0  success (PDFs downloaded, validated)
  1  no matching email found
  2  validation failure (wrong location, date mismatch, missing attachments)
  3  auth failure (need to re-run --setup)
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]
REPO_ROOT = Path(__file__).resolve().parent.parent
SECRETS_DIR = REPO_ROOT / "secrets"
CLIENT_FILE = SECRETS_DIR / "scg_oauth_client.json"
TOKEN_FILE = SECRETS_DIR / "scg_refresh_token.json"
CONFIG_DIR = REPO_ROOT / "config"
DATA_ROOT = REPO_ROOT / "data" / "raw" / "parbrink"

DAILY_SUBJECT = "dixie sales summary"
WEEKLY_SUBJECT = "dixie sales summary"   # as of ~2026-06-02, no separate weekly email
SENDER = "noreply@parpos.com"

# Legacy subject lines — kept as fallback search terms for backfill / format rollback.
LEGACY_SUBJECTS = [
    "Promethus Reports",           # original daily (typo intentional on Brink side)
    "Prometheus Weekly reports",   # original weekly
]

# Required reports for validation.  Brink's "dixie sales summary" format ships
# a variable attachment set depending on store config, so these are *soft* —
# we warn on missing but still write whatever PDFs arrived (no hard exit-2 for
# missing reports; only true errors like wrong location are hard failures).
DAILY_REPORTS = {
    "Audit Business Date",
    "Discount Summary",
    "Hourly Sales And Labor",
    "Hourly Sales And Labor By Section",
    "Sales And Labor Summary By Location",
    "Sales By Destination",
    "Sales Summary",
    "Sales Summary By Location",
    "Weekly Labor Schedule",
}

WEEKLY_REPORTS = {
    "Discount Summary",
    "Employee Timecard",
    "Hourly Sales And Labor",
    "Labor Cost By Job",
    "Product Mix",
    "Sales And Labor Summary By Location",
    "Sales By Day",
    "Sales Summary",
    "Weekly Labor Schedule",
}


def log(msg: str) -> None:
    print(f"[parbrink-pickup] {msg}", flush=True)


def load_store_config(store_id: str) -> dict:
    cfg_path = CONFIG_DIR / f"{store_id}.json"
    if not cfg_path.exists():
        raise SystemExit(f"Store config not found: {cfg_path}")
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def get_credentials(setup_mode: bool = False) -> Credentials:
    """Returns valid Gmail API credentials.

    On first run (or when --setup is passed), opens a browser for the customer
    to grant access. Subsequent runs reuse the saved refresh token.
    """
    if not CLIENT_FILE.exists():
        raise SystemExit(
            f"Missing OAuth client file: {CLIENT_FILE}\n"
            "This file ships with the SCG Dashboard product. Reinstall or contact support."
        )

    creds: Credentials | None = None

    if TOKEN_FILE.exists() and not setup_mode:
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception as exc:
            log(f"Saved token unreadable ({exc}); will re-run OAuth flow.")
            creds = None

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
            return creds
        except Exception as exc:
            log(f"Refresh failed ({exc}); falling back to full OAuth flow.")

    SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_FILE), SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")
    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    log(f"Saved refresh token to {TOKEN_FILE}")
    return creds


def find_latest_email(service, subject: str, target_date: date | None) -> dict | None:
    """Returns the newest matching message metadata, or None.

    Searches the primary subject first, then legacy subject lines as fallback.
    If target_date is given, returns the newest message whose Business Date
    matches; otherwise falls back to the absolute most-recent message.

    As of ~2026-06-02, Par Brink changed their email subject from
    "Promethus Reports" / "Prometheus Weekly reports" to "dixie sales summary".
    Both daily and weekly modes now use the same subject; mode=weekly identifies
    the right email by matching the week-ending Sunday business date.
    """
    # Build candidate subject list: primary first, then legacy fallbacks.
    subjects_to_try = [subject] + [s for s in LEGACY_SUBJECTS if s != subject]

    all_messages: list[dict] = []
    for subj in subjects_to_try:
        base_query = f'from:{SENDER} subject:"{subj}"'
        try:
            resp = service.users().messages().list(
                userId="me", q=base_query, maxResults=20
            ).execute()
        except HttpError as e:
            raise SystemExit(f"Gmail list failed: {e}")
        msgs = resp.get("messages", [])
        if msgs:
            all_messages.extend(msgs)
            break  # found messages with this subject; don't also search legacy

    if not all_messages:
        return None

    if target_date is not None:
        for m in all_messages:
            full = service.users().messages().get(
                userId="me", id=m["id"], format="full"
            ).execute()
            body = extract_plain_body(full)
            biz = parse_business_date(body)
            if biz == target_date:
                return full
        # No exact date match — fall through to return most recent
        return None

    return service.users().messages().get(
        userId="me", id=all_messages[0]["id"], format="full"
    ).execute()


def extract_plain_body(message: dict) -> str:
    """Walks message parts and returns the concatenated text/plain body."""
    payload = message.get("payload", {})
    chunks: list[str] = []

    def walk(part):
        mt = part.get("mimeType", "")
        if mt.startswith("text/plain"):
            data = part.get("body", {}).get("data", "")
            if data:
                try:
                    chunks.append(base64.urlsafe_b64decode(data + "===").decode("utf-8", errors="replace"))
                except Exception:
                    pass
        for sub in part.get("parts", []) or []:
            walk(sub)

    walk(payload)
    return "\n".join(chunks)


def parse_business_date(body: str) -> date | None:
    """Extract the business date from a Par Brink email body.

    Handles multiple label variants and date formats:
      "Business Date: 6/30/2026"    (new "dixie" format — single-digit month/day, NO leading zero)
      "Business Date: 06/22/2026"   (original zero-padded format)
      "Business Date  06/22/2026"   (no colon, extra spaces)
      "Business Date:\n06/22/2026"  (value on next line)
      "Week Ending: 06/22/2026"     (weekly label variant)
      "Week End Date: June 22, 2026" (written-out month)
      "Business Date: June 22, 2026" (written-out month, daily label)

    IMPORTANT: As of ~2026-06-02 Brink sends "Business Date: 6/30/2026" with NO
    leading zero on month or day.  strptime's %m/%d/%Y is lenient about this on
    CPython (it accepts "6/30/2026"), but the pre-pad step below handles any
    platform that is strict, and also normalises hyphen-separated variants.
    """
    # Patterns to try in order of specificity.
    # Group 1 captures the raw date string (digits/slashes/hyphens or written month).
    PATTERNS = [
        # "dixie" format (current): "Business Date: 6/30/2026" — single-digit month/day
        r"Business Date:\s*(\d{1,2}/\d{1,2}/\d{4})",
        # Original: "Business Date: 06/22/2026" — zero-padded, same line
        r"Business Date:\s*([\d/\-]+)",
        # No-colon or extra-space variant: "Business Date  06/22/2026"
        r"Business Date\s*:?\s+([\d/\-]+)",
        # Value on next line: "Business Date:\n06/22/2026"
        r"Business Date\s*:\s*\n\s*([\d/\-]+)",
        # Weekly label "Week Ending" / "Week End Date" — numeric
        r"Week\s+End(?:ing)?\s+(?:Date\s*)?:?\s*(\d{1,2}/\d{1,2}/\d{4})",
        r"Week\s+End(?:ing)?\s+(?:Date\s*)?:?\s*([\d/\-]+)",
        # Written-out month variants: "June 22, 2026" or "Jun 22 2026"
        r"Business Date\s*:?\s*([A-Za-z]+ \d{1,2},?\s+\d{4})",
        r"Week\s+End(?:ing)?\s+(?:Date\s*)?:?\s*([A-Za-z]+ \d{1,2},?\s+\d{4})",
    ]

    WRITTEN_FMTS = ("%B %d, %Y", "%B %d %Y", "%b %d, %Y", "%b %d %Y")

    for pattern in PATTERNS:
        m = re.search(pattern, body, re.IGNORECASE)
        if not m:
            continue
        raw = m.group(1).strip().rstrip(",")

        # ── Numeric formats ───────────────────────────────────────────────────
        # Normalise separator to "/" so we only need one set of formats.
        normalised = raw.replace("-", "/")
        parts = normalised.split("/")
        if len(parts) == 3:
            # Zero-pad month and day so strptime %m/%d/%Y always succeeds,
            # even on platforms that are strict about leading zeros.
            try:
                if len(parts[2]) == 4:
                    # M/D/YYYY or MM/DD/YYYY → zero-pad to MM/DD/YYYY
                    padded = f"{int(parts[0]):02d}/{int(parts[1]):02d}/{parts[2]}"
                else:
                    # YYYY/MM/DD → zero-pad to YYYY/MM/DD
                    padded = f"{parts[0]}/{int(parts[1]):02d}/{int(parts[2]):02d}"
                for fmt in ("%m/%d/%Y", "%Y/%m/%d"):
                    try:
                        return datetime.strptime(padded, fmt).date()
                    except ValueError:
                        continue
            except (ValueError, IndexError):
                pass

        # ── Written-out month formats ─────────────────────────────────────────
        for fmt in WRITTEN_FMTS:
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                continue

    return None


def parse_locations(body: str) -> list[str]:
    """Extract the store location(s) from the email body.

    Handles both singular "Location:" (new "dixie" format) and plural
    "Locations:" (original format), and multi-line location values where
    the value runs onto the next line.
    """
    # Match "Location: KY-2065 Dixie Highway" or "Locations: ..."
    # Also handles value on next line: "Location:\nKY-2065 ..."
    m = re.search(r"Locations?\s*:\s*(.+?)(?:\n\n|\Z)", body, re.DOTALL | re.IGNORECASE)
    if not m:
        return []
    raw = m.group(1).strip()
    # Flatten newlines within the location block (multi-line location values)
    raw = re.sub(r"\s*\n\s*", " ", raw).strip()
    return [x.strip() for x in re.split(r"[,;]", raw) if x.strip()]


def get_attachments(service, message: dict) -> list[tuple[str, bytes]]:
    """Returns [(filename, bytes), ...] for every PDF attachment."""
    out: list[tuple[str, bytes]] = []
    msg_id = message["id"]

    def walk(part):
        filename = part.get("filename") or ""
        body = part.get("body", {})
        att_id = body.get("attachmentId")
        if filename.lower().endswith(".pdf") and att_id:
            att = service.users().messages().attachments().get(
                userId="me", messageId=msg_id, id=att_id
            ).execute()
            data = base64.urlsafe_b64decode(att["data"] + "===")
            out.append((filename, data))
        for sub in part.get("parts", []) or []:
            walk(sub)

    walk(message.get("payload", {}))
    return out


def report_name_from_filename(fn: str) -> str:
    return Path(fn).stem.strip()


def validate(
    business_date: date | None,
    locations: list[str],
    attachments: list[tuple[str, bytes]],
    expected_location_substr: str,
    mode: str,
) -> list[str]:
    errors: list[str] = []
    if business_date is None:
        errors.append("Could not parse Business Date from email body.")
    if not locations:
        errors.append("Could not parse Locations line from email body.")
    elif not any(expected_location_substr.lower() in loc.lower() for loc in locations):
        errors.append(
            f"Location mismatch: expected '{expected_location_substr}' in {locations}."
        )

    if not attachments:
        errors.append("No PDF attachments found.")
        return errors  # no point checking report names without any attachments

    # As of ~2026-06-02 "dixie sales summary" format sends a variable attachment
    # set (often just Sales Summary.pdf) rather than the full legacy report bundle.
    # Missing reports are now WARNINGS logged to debug-log but are NOT hard errors
    # that block writing PDFs.  Only a complete absence of attachments is hard.
    expected = DAILY_REPORTS if mode == "daily" else WEEKLY_REPORTS
    found_names = {report_name_from_filename(fn) for fn, _ in attachments}
    missing = []
    for exp in expected:
        hit = any(
            exp.lower().replace(" ", "") in got.lower().replace(" ", "")
            for got in found_names
        )
        if not hit:
            missing.append(exp)
    if missing:
        # Soft warning only — do NOT append to errors so validation still passes
        log(f"[warn] {len(missing)}/{len(expected)} expected reports absent (store may not send them): {missing}")

    return errors


def write_attachments(attachments: list[tuple[str, bytes]], dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for filename, data in attachments:
        safe = re.sub(r'[<>:"/\\|?*]', "_", filename).strip()
        (dest / safe).write_bytes(data)


def mark_read(service, message_id: str) -> None:
    try:
        service.users().messages().modify(
            userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
        ).execute()
    except HttpError as e:
        log(f"Could not mark email read (non-fatal): {e}")


def write_debug(store_id: str, business_date: date | None, mode: str, errors: list[str]) -> None:
    debug = REPO_ROOT / "data" / "debug-log.txt"
    debug.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bd = business_date.isoformat() if business_date else "?"
    with debug.open("a", encoding="utf-8") as f:
        f.write(f"\n[{stamp}] parbrink_email_pickup store={store_id} mode={mode} business_date={bd}\n")
        for e in errors:
            f.write(f"  - {e}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", required=True, help="Store ID (matches config/{id}.json)")
    parser.add_argument("--mode", choices=["daily", "weekly"], default="daily")
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Force re-running the OAuth browser flow (first install / reauth).",
    )
    parser.add_argument(
        "--date",
        help="Expected business date (YYYY-MM-DD). Defaults to yesterday for daily, last Mon for weekly.",
    )
    args = parser.parse_args()

    store = load_store_config(args.store)
    store_id = str(store.get("store_id", args.store))
    expected_loc = store.get("store_name", store_id)

    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    elif args.mode == "daily":
        target_date = date.today() - timedelta(days=1)
    else:
        # Weekly mode: look for the most recent Sunday (week-ending date).
        # Par Brink's week runs Mon–Sun; the weekly email reports through Sunday.
        # weekday(): Mon=0 … Sun=6.  Days since last Sunday = (weekday+1) % 7,
        # but if today IS Sunday (weekday=6) we want 7 days back (last week's end).
        today = date.today()
        days_since_sunday = (today.weekday() + 1) % 7
        if days_since_sunday == 0:
            days_since_sunday = 7  # Sunday → go back a full week so we don't pick today
        target_date = today - timedelta(days=days_since_sunday)

    log(f"store={store_id} mode={args.mode} target_business_date={target_date}")

    try:
        creds = get_credentials(setup_mode=args.setup)
    except Exception as e:
        log(f"AUTH FAILURE: {e}")
        return 3

    if args.setup:
        log("Setup complete. Refresh token saved. Re-run without --setup to fetch reports.")
        return 0

    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    subject = DAILY_SUBJECT if args.mode == "daily" else WEEKLY_SUBJECT

    message = find_latest_email(service, subject, target_date)
    if not message:
        log(f"No email matching from:{SENDER} subject:'{subject}' for {target_date}.")
        return 1

    body = extract_plain_body(message)
    business_date = parse_business_date(body)
    locations = parse_locations(body)
    log(f"email Business Date: {business_date}, Locations: {locations}")

    attachments = get_attachments(service, message)
    log(f"found {len(attachments)} PDF attachment(s)")

    errors = validate(business_date, locations, attachments, expected_loc, args.mode)

    if args.mode == "daily":
        folder = DATA_ROOT / store_id / (business_date.isoformat() if business_date else target_date.isoformat())
    else:
        end = business_date if business_date else target_date
        folder = DATA_ROOT / store_id / f"week-ending-{end.isoformat()}"

    if errors:
        log("VALIDATION FAILURES:")
        for e in errors:
            log(f"  - {e}")
        write_debug(store_id, business_date, args.mode, errors)

    if attachments:
        write_attachments(attachments, folder)
        log(f"wrote {len(attachments)} PDF(s) to {folder}")

    if not errors:
        mark_read(service, message["id"])
        log("marked email read")
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
