"""read_outlook_via_gmail.py

Reads fg2065@estep-co.com emails that arrive in bob.cline2000@gmail.com
via Outlook server-side forwarding, then generates and sends a daily brief.

Runs headlessly in GitHub Actions at 8:05 AM ET — no browser, no laptop required.

Usage:
  python scraper/read_outlook_via_gmail.py            # normal daily run
  python scraper/read_outlook_via_gmail.py --setup    # first-time / reauth
  python scraper/read_outlook_via_gmail.py --dry-run  # generate brief, skip send
  python scraper/read_outlook_via_gmail.py --hours 48 # expand lookback window

Exit codes:
  0  success
  1  no work emails found in the lookback window
  2  send failed
  3  auth failed
"""

from __future__ import annotations

import argparse
import base64
import email as email_lib
import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pypdf import PdfReader
import io

# ── Auth / paths ────────────────────────────────────────────────────────────

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]

REPO_ROOT = Path(__file__).resolve().parent.parent
SECRETS_DIR = REPO_ROOT / "secrets"
CLIENT_FILE = SECRETS_DIR / "scg_oauth_client.json"
TOKEN_FILE = SECRETS_DIR / "scg_refresh_token.json"
DATA_DIR = REPO_ROOT / "data" / "daily-brief"
DEBUG_LOG = REPO_ROOT / "data" / "debug-log.txt"

FROM_ADDRESS = "bob.cline2000@gmail.com"
TO_ADDRESS = "fg2065@estep-co.com"
WORK_INBOX = "fg2065@estep-co.com"

# ── Email classification rules ──────────────────────────────────────────────

SKIP_SENDERS = {
    "noreply@parpos.com",           # Par Brink — handled by parbrink_email_pickup.py
    "noreply@net-chef.com",         # CrunchTime automated reports
    "noreply@crunchtime.com",
    "bob.cline2000@gmail.com",      # Bobby's own sends
    "bobby.cline2000@gmail.com",
}

SKIP_SUBJECT_PATTERNS = [
    r"adobe acrobat",
    r"unsubscribe",
    r"microsoft account security",
]

PRIORITY_SENDERS = {
    "bdavis@estep-co.com": "Director's Corner",
    "chess@estep-co.com": "Crystal Hess (DM)",
    "acampbell@estep-co.com": "District Manager",
}

CATEGORY_RULES = [
    # (pattern_type, pattern, category)
    # pattern_type: "sender" matches From address, "subject" matches subject text
    ("subject", r"patty press",          "Patty Press"),
    ("subject", r"onboard|new hire|background check|cleared to start|hire",  "New Hire / Onboarding"),
    ("sender",  r"marketforce\.com",     "Secret Shop"),
    ("subject", r"secret shop",          "Secret Shop"),
    ("subject", r"deposit|receipts|missing.*deposit", "Finance / Deposits"),
    ("sender",  r"tonya|ttucker|737 ventures", "Finance / Deposits"),
    ("subject", r"compliance|audit",     "Compliance"),
    ("subject", r"five guys|fiveguys|lto|announcement|brand update|5th gear", "Corporate Announcements"),
    ("sender",  r"fiveguys\.com|fiveguysenterprises\.com", "Corporate Announcements"),
    ("sender",  r"estep-co\.com",        "Estep Corporate / Admin"),
]

DOW_ABBREV = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


# ── Logging ─────────────────────────────────────────────────────────────────

def log(msg: str) -> None:
    print(f"[outlook-gmail] {msg}", flush=True)


def write_debug(reason: str, detail_path: str = "") -> None:
    DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    suffix = f" — see {detail_path}" if detail_path else ""
    with DEBUG_LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{stamp}] outlook-daily-pull-7am: {reason}{suffix}\n")


# ── Gmail auth ───────────────────────────────────────────────────────────────

def get_credentials(setup_mode: bool = False) -> Credentials:
    if not CLIENT_FILE.exists():
        raise SystemExit(
            f"Missing OAuth client file: {CLIENT_FILE}\n"
            "Run with --setup on Bobby's laptop first."
        )

    creds: Credentials | None = None
    if TOKEN_FILE.exists() and not setup_mode:
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception as exc:
            log(f"Saved token unreadable ({exc}); will reauth.")
            creds = None

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
            return creds
        except Exception as exc:
            log(f"Token refresh failed ({exc}); falling back to full OAuth flow.")

    SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_FILE), SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")
    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    log(f"Saved new token to {TOKEN_FILE}")
    return creds


# ── Email fetching ───────────────────────────────────────────────────────────

def fetch_work_emails(service, lookback_hours: int) -> list[dict]:
    """Returns full message objects addressed to fg2065 in the lookback window."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    # Gmail after: filter uses Unix epoch seconds
    after_ts = int(cutoff.timestamp())
    query = f"to:{WORK_INBOX} after:{after_ts}"
    log(f"Gmail query: {query}")

    try:
        resp = service.users().messages().list(
            userId="me", q=query, maxResults=100
        ).execute()
    except HttpError as e:
        raise SystemExit(f"Gmail list failed: {e}")

    messages = resp.get("messages", [])
    log(f"Found {len(messages)} candidate messages")

    full_messages = []
    for m in messages:
        try:
            full = service.users().messages().get(
                userId="me", id=m["id"], format="full"
            ).execute()
            full_messages.append(full)
        except HttpError as e:
            log(f"Could not fetch message {m['id']}: {e}")

    return full_messages


# ── Parsing helpers ──────────────────────────────────────────────────────────

def get_header(message: dict, name: str) -> str:
    headers = message.get("payload", {}).get("headers", [])
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def extract_plain_body(message: dict) -> str:
    payload = message.get("payload", {})
    chunks: list[str] = []

    def walk(part):
        mt = part.get("mimeType", "")
        if mt == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                try:
                    chunks.append(
                        base64.urlsafe_b64decode(data + "===").decode("utf-8", errors="replace")
                    )
                except Exception:
                    pass
        for sub in part.get("parts", []) or []:
            walk(sub)

    walk(payload)
    return "\n".join(chunks).strip()


def extract_html_body(message: dict) -> str:
    payload = message.get("payload", {})
    chunks: list[str] = []

    def walk(part):
        mt = part.get("mimeType", "")
        if mt == "text/html":
            data = part.get("body", {}).get("data", "")
            if data:
                try:
                    chunks.append(
                        base64.urlsafe_b64decode(data + "===").decode("utf-8", errors="replace")
                    )
                except Exception:
                    pass
        for sub in part.get("parts", []) or []:
            walk(sub)

    walk(payload)
    return "\n".join(chunks).strip()


def get_pdf_attachments(service, message: dict) -> list[tuple[str, bytes]]:
    """Returns [(filename, bytes)] for every PDF attachment."""
    out: list[tuple[str, bytes]] = []
    msg_id = message["id"]

    def walk(part):
        filename = part.get("filename") or ""
        body = part.get("body", {})
        att_id = body.get("attachmentId")
        if filename.lower().endswith(".pdf") and att_id:
            try:
                att = service.users().messages().attachments().get(
                    userId="me", messageId=msg_id, id=att_id
                ).execute()
                data = base64.urlsafe_b64decode(att["data"] + "===")
                out.append((filename, data))
            except HttpError as e:
                log(f"Could not download attachment {filename}: {e}")
        for sub in part.get("parts", []) or []:
            walk(sub)

    walk(message.get("payload", {}))
    return out


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Returns plain text from a PDF (best-effort)."""
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n".join(pages).strip()
    except Exception as e:
        return f"[PDF text extraction failed: {e}]"


def format_date(internal_date_ms: str) -> str:
    """Converts Gmail internalDate (ms since epoch) to readable ET string."""
    try:
        ts = int(internal_date_ms) / 1000
        dt = datetime.fromtimestamp(ts)
        return dt.strftime("%a %m/%d/%Y %-I:%M %p")
    except Exception:
        return "unknown date"


# ── Classification ───────────────────────────────────────────────────────────

def classify_email(sender: str, subject: str) -> str | None:
    """Returns category string, or None if this email should be skipped."""
    sender_lower = sender.lower()
    subject_lower = subject.lower()

    # Hard skip
    for skip in SKIP_SENDERS:
        if skip in sender_lower:
            return None
    for pat in SKIP_SUBJECT_PATTERNS:
        if re.search(pat, subject_lower):
            return None

    # Priority sender override
    for addr, label in PRIORITY_SENDERS.items():
        if addr in sender_lower:
            return label

    # Category rules in priority order
    for pattern_type, pat, category in CATEGORY_RULES:
        if pattern_type == "sender" and re.search(pat, sender_lower):
            return category
        if pattern_type == "subject" and re.search(pat, subject_lower):
            return category

    return "Other Work Email"


def extract_phones(text: str) -> list[str]:
    """Finds phone numbers in text."""
    phones = re.findall(r"\(?\d{3}\)?[\s\-\.]\d{3}[\s\-\.]\d{4}", text)
    return list(set(phones))


def extract_new_hire_info(body: str, subject: str) -> dict:
    """Extracts name and phone from onboarding/HR emails."""
    info: dict = {"names": [], "phones": [], "action": ""}

    # Try to find a name — look for "Name:" pattern or capitalized names near keywords
    name_matches = re.findall(
        r"(?:employee|hire|new hire|candidate|name)[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)",
        body, re.IGNORECASE
    )
    if not name_matches:
        # Fall back: look for "FirstName LastName has been" pattern
        name_matches = re.findall(
            r"([A-Z][a-z]+ [A-Z][a-z]+)\s+(?:has been|is|was)\s+(?:cleared|hired|processed|approved)",
            body
        )
    info["names"] = list(set(name_matches))
    info["phones"] = extract_phones(body)

    if re.search(r"cleared to start|approved|processed", body, re.IGNORECASE):
        info["action"] = "call to give start date / schedule first shift"
    elif re.search(r"background check sent|pending", body, re.IGNORECASE):
        info["action"] = "wait for background check clearance"
    elif re.search(r"offer", body, re.IGNORECASE):
        info["action"] = "confirm offer accepted"

    return info


# ── Brief generation ─────────────────────────────────────────────────────────

def build_secret_shop_corner() -> str:
    """Reads latest shops.json from KnowledgeForce pipeline and produces the
    Secret Shop Corner section: latest shop, KPI focus areas, and team rallying
    message. Returns empty string if shops.json not found."""
    marketforce_root = REPO_ROOT / "data" / "raw" / "marketforce" / "2065"
    if not marketforce_root.exists():
        return ""

    latest_dir = None
    for d in sorted(marketforce_root.iterdir(), reverse=True):
        if d.is_dir() and (d / "shops.json").exists():
            latest_dir = d
            break
    if not latest_dir:
        return ""

    try:
        data = json.loads((latest_dir / "shops.json").read_text(encoding="utf-8"))
    except Exception:
        return ""

    shops = data.get("shops", []) or []
    if not shops:
        return ""

    latest = data.get("latest", shops[0])
    avg = data.get("averages", {})

    # Compute per-KPI averages across all shops
    def _avg(field: str) -> float | None:
        vals = [s.get(field) for s in shops if s.get(field) is not None]
        return round(sum(vals) / len(vals), 1) if vals else None

    svc_avg   = _avg("service")
    qual_avg  = _avg("quality")
    clean_avg = _avg("cleanliness")
    csat_avg  = _avg("customer_satisfaction")

    # Lunch vs Dinner split — surfaces shift-level pattern
    lunch_scores  = [s["score"] for s in shops if "lunch" in (s.get("meal_period","").lower())]
    dinner_scores = [s["score"] for s in shops if "dinner" in (s.get("meal_period","").lower())]
    lunch_avg  = round(sum(lunch_scores)/len(lunch_scores), 1) if lunch_scores else None
    dinner_avg = round(sum(dinner_scores)/len(dinner_scores), 1) if dinner_scores else None

    # Identify weakest KPI
    kpi_avgs = {
        "Service": svc_avg, "Quality": qual_avg,
        "Cleanliness": clean_avg, "Customer Satisfaction": csat_avg,
    }
    weakest = sorted(((v, k) for k, v in kpi_avgs.items() if v is not None))
    weakest_kpi, weakest_score = (weakest[0][1], weakest[0][0]) if weakest else (None, None)

    lines: list[str] = []
    lines.append("## 🛒 Secret Shop Corner — Team Focus")
    lines.append("")
    lines.append("**Where we stand right now:**")
    lines.append("")
    lines.append(f"- **Latest shop:** {latest.get('date','?')} {latest.get('meal_period','?')} — **{latest.get('score','?')}%**")
    lines.append(f"  - Service {latest.get('service','?')}% · Quality {latest.get('quality','?')}% · "
                 f"Cleanliness {latest.get('cleanliness','?')}% · CSAT {latest.get('customer_satisfaction','?')}%")
    if avg.get("month", {}).get("score") is not None:
        lines.append(f"- **Month average:** {avg['month']['score']}% (n={avg['month']['n']})")
    if avg.get("quarter", {}).get("score") is not None:
        lines.append(f"- **Quarter average:** {avg['quarter']['score']}% (n={avg['quarter']['n']})")
    lines.append(f"- **Total shops on file:** {len(shops)}")
    lines.append("")

    lines.append("**KPI averages across all shops on record:**")
    lines.append("")
    lines.append("| KPI | Avg | Status |")
    lines.append("|---|---|---|")
    for k, v in kpi_avgs.items():
        if v is None:
            continue
        status = "🟢 Strong" if v >= 95 else ("🟡 Watch" if v >= 90 else "🔴 Focus area")
        lines.append(f"| {k} | {v}% | {status} |")
    lines.append("")

    if lunch_avg is not None and dinner_avg is not None:
        lines.append(f"**Shift pattern:** Lunch avg **{lunch_avg}%** · Dinner avg **{dinner_avg}%**")
        if lunch_avg < dinner_avg - 3:
            lines.append("> Lunch shift is dragging the score. Most sub-100 shops happen at lunch.")
        elif dinner_avg < lunch_avg - 3:
            lines.append("> Dinner shift is dragging the score. Reinforce evening standards.")
        lines.append("")

    # Team focus + rally
    lines.append("**Where we focus this week:**")
    lines.append("")
    if weakest_kpi == "Service":
        lines.append("- 🎯 **SERVICE** is our #1 drag. Greeting at the door, eye contact, "
                     "thank-you on the way out — every guest, every order. No exceptions.")
        lines.append("- Speed of service: register → window in under 6 minutes target.")
    elif weakest_kpi == "Cleanliness":
        lines.append("- 🎯 **CLEANLINESS** is our #1 drag. Lobby sweeps every 15 minutes, "
                     "tables wiped between guests, restrooms checked hourly with sign-off sheet.")
    elif weakest_kpi == "Quality":
        lines.append("- 🎯 **QUALITY** is our drag. Build-to-spec on every burger. "
                     "Buns toasted, lettuce crisp, no shortcuts on toppings.")
    elif weakest_kpi == "Customer Satisfaction":
        lines.append("- 🎯 **CSAT** is our drag. Recovery moments matter — if a guest hesitates, ask. "
                     "If something's wrong, fix it before they leave.")

    # Always reinforce the secondary KPIs that show up below 100
    secondary = [k for k, v in kpi_avgs.items() if v is not None and v < 95 and k != weakest_kpi]
    for s in secondary:
        lines.append(f"- Secondary watch: **{s}** is also showing gaps — keep eyes on it.")

    lines.append("")
    lines.append("**Team message:**")
    lines.append("")
    lines.append("> We must improve these scores **dramatically**. Every shop is a snapshot "
                 "of what a real guest sees on a real shift. Two perfect shops in a row don't "
                 "cancel out a 47% — corporate sees the average and the trend. The fundamentals "
                 "win this: greet, speed, clean, build to spec. Lock it in shift by shift.")
    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def build_brief(categorized: dict[str, list[dict]], today: date) -> str:
    """Builds the daily brief markdown string."""
    lines: list[str] = []
    pull_time = datetime.now().strftime("%Y-%m-%d %H:%M ET")

    lines.append(f"# Outlook Pull — {today.strftime('%Y-%m-%d')}")
    lines.append("")
    lines.append("## Session Status")
    total_emails = sum(len(v) for v in categorized.values())
    categories_found = [k for k, v in categorized.items() if v]
    lines.append(f"- **Status:** COMPLETE")
    lines.append(f"- **Date Range:** last 28 hours as of {pull_time}")
    lines.append(f"- **Account:** fg2065@estep-co.com (Store 2065 — Louisville, KY)")
    lines.append(f"- **Emails Processed:** {total_emails}")
    lines.append(f"- **Categories Found:** {', '.join(categories_found) if categories_found else 'none'}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── CRITICAL section ─────────────────────────────────────────────────────
    critical_items: list[str] = []

    # New hires always go critical
    for em in categorized.get("New Hire / Onboarding", []):
        hire_info = em.get("_hire_info", {})
        names = hire_info.get("names", [])
        phones = hire_info.get("phones", [])
        action = hire_info.get("action", "review and action")
        name_str = ", ".join(names) if names else "name not parsed — check email"
        phone_str = ", ".join(phones) if phones else "phone not found"
        subj = em.get("subject", "")
        sent = em.get("sent", "")
        critical_items.append(
            f"**🚨 NEW HIRE: {name_str}** ({sent})\n"
            f"   - Phone: {phone_str}\n"
            f"   - Subject: {subj}\n"
            f"   - Action: {action}\n"
            f"   - Proposed directory edit: `Add to EMPLOYEES list: (\"{name_str.split()[0] if names else 'FirstName'}\", \"{phone_str}\", \"Active\")`"
        )

    # Finance/deposit flags
    for em in categorized.get("Finance / Deposits", []):
        subj = em.get("subject", "")
        sent = em.get("sent", "")
        snippet = em.get("snippet", "")[:200]
        critical_items.append(
            f"**⚠️ FINANCE: {subj}** ({sent})\n   {snippet}"
        )

    if critical_items:
        lines.append("## CRITICAL — Action Required (Act on These First)")
        lines.append("")
        for i, item in enumerate(critical_items, 1):
            lines.append(f"{i}. {item}")
            lines.append("")
        lines.append("---")
        lines.append("")

    # ── Director's Corner ────────────────────────────────────────────────────
    director_emails = categorized.get("Director's Corner", [])
    if director_emails:
        lines.append("## Director's Corner — Brad Davis (bdavis@estep-co.com)")
        lines.append("")
        for i, em in enumerate(director_emails, 1):
            lines.append(f"### Email {i} — {em.get('sent', '')} | Subject: \"{em.get('subject', '')}\"")
            body = em.get("body", "").strip()
            if body:
                # Limit to first 1500 chars to keep brief readable
                lines.append(body[:1500])
                if len(body) > 1500:
                    lines.append("*[body truncated — see original email for full text]*")
            lines.append("")
        lines.append("---")
        lines.append("")

    # ── Crystal Hess / DM ───────────────────────────────────────────────────
    crystal_emails = categorized.get("Crystal Hess (DM)", [])
    if crystal_emails:
        lines.append("## Crystal Hess / DM")
        lines.append("")
        for em in crystal_emails:
            lines.append(f"### {em.get('sent', '')} — \"{em.get('subject', '')}\"")
            body = em.get("body", "").strip()
            if body:
                lines.append(body[:1000])
            lines.append("")
        lines.append("---")
        lines.append("")

    # ── Patty Press ──────────────────────────────────────────────────────────
    patty_emails = categorized.get("Patty Press", [])
    if patty_emails:
        lines.append("## Patty Press")
        lines.append("")
        for em in patty_emails:
            lines.append(f"### {em.get('sent', '')} — \"{em.get('subject', '')}\"")
            body = em.get("body", "").strip()
            if body:
                lines.append(body[:2000])
            # PDF text
            for pdf_name, pdf_text in em.get("pdf_texts", []):
                lines.append(f"\n**PDF: {pdf_name}**")
                lines.append(pdf_text[:3000])
                if len(pdf_text) > 3000:
                    lines.append("*[PDF truncated]*")
            lines.append("")
        lines.append("---")
        lines.append("")

    # ── Corporate Announcements ──────────────────────────────────────────────
    corp_emails = categorized.get("Corporate Announcements", [])
    if corp_emails:
        lines.append("## Corporate Announcements")
        lines.append("")
        for em in corp_emails:
            lines.append(f"### {em.get('sent', '')} — \"{em.get('subject', '')}\"")
            body = em.get("body", "").strip()
            if body:
                lines.append(body[:1000])
            lines.append("")
        lines.append("---")
        lines.append("")

    # ── Secret Shop ──────────────────────────────────────────────────────────
    shop_emails = categorized.get("Secret Shop", [])
    if shop_emails:
        lines.append("## Secret Shop")
        lines.append("")
        for em in shop_emails:
            lines.append(f"### {em.get('sent', '')} — \"{em.get('subject', '')}\"")
            body = em.get("body", "").strip()
            if body:
                lines.append(body[:1500])
            for pdf_name, pdf_text in em.get("pdf_texts", []):
                lines.append(f"\n**PDF: {pdf_name}**")
                lines.append(pdf_text[:3000])
            lines.append("")
        lines.append("---")
        lines.append("")

    # ── Secret Shop Corner (KnowledgeForce data — runs every brief) ──────────
    corner = build_secret_shop_corner()
    if corner:
        lines.append(corner)

    # ── Estep Corporate / Admin ──────────────────────────────────────────────
    estep_emails = categorized.get("Estep Corporate / Admin", [])
    if estep_emails:
        lines.append("## Estep Corporate / Admin")
        lines.append("")
        for em in estep_emails:
            lines.append(f"### {em.get('sent', '')} — \"{em.get('subject', '')}\"")
            snippet = em.get("snippet", "")[:300]
            if snippet:
                lines.append(snippet)
            lines.append("")
        lines.append("---")
        lines.append("")

    # ── Other Work Email ─────────────────────────────────────────────────────
    other_emails = categorized.get("Other Work Email", [])
    if other_emails:
        lines.append("## Other Work Email")
        lines.append("")
        for em in other_emails:
            sender = em.get("sender", "")
            subj = em.get("subject", "")
            sent = em.get("sent", "")
            snippet = em.get("snippet", "")[:200]
            lines.append(f"- **{sent}** | {sender} | *{subj}*")
            if snippet:
                lines.append(f"  {snippet}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # ── Skipped ──────────────────────────────────────────────────────────────
    skipped = categorized.get("_skipped", [])
    if skipped:
        lines.append("## Skipped (Filter Sanity Check)")
        lines.append("")
        lines.append("| Source | Subject | Reason |")
        lines.append("|---|---|---|")
        for em in skipped:
            sender = em.get("sender", "")[:40]
            subj = em.get("subject", "")[:50]
            reason = em.get("skip_reason", "filtered")
            lines.append(f"| {sender} | {subj} | {reason} |")
        lines.append("")

    return "\n".join(lines)


# ── Email send ───────────────────────────────────────────────────────────────

def send_brief(service, subject: str, body_md: str) -> bool:
    """Sends the brief from bob.cline2000@gmail.com to fg2065@estep-co.com."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = FROM_ADDRESS
    msg["To"] = TO_ADDRESS

    # Plain text version
    msg.attach(MIMEText(body_md, "plain"))

    # Simple HTML version — wrap in pre for readability
    html_body = f"<html><body><pre style='font-family:monospace;font-size:13px;white-space:pre-wrap'>{body_md}</pre></body></html>"
    msg.attach(MIMEText(html_body, "html"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    try:
        service.users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()
        log(f"Brief sent to {TO_ADDRESS}")
        return True
    except HttpError as e:
        log(f"Send failed: {e}")
        return False


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--setup", action="store_true", help="Run OAuth flow (first time / reauth)")
    parser.add_argument("--dry-run", action="store_true", help="Generate brief but don't send email")
    parser.add_argument("--hours", type=int, default=28, help="Lookback window in hours (default 28)")
    args = parser.parse_args()

    today = date.today()
    dow = DOW_ABBREV[today.weekday()]
    monday = today - timedelta(days=today.weekday())

    try:
        creds = get_credentials(setup_mode=args.setup)
    except Exception as e:
        log(f"AUTH FAILURE: {e}")
        write_debug(f"auth failure: {e}")
        return 3

    if args.setup:
        log("Setup complete. Re-run without --setup to generate a brief.")
        return 0

    service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    # ── Fetch emails ─────────────────────────────────────────────────────────
    raw_messages = fetch_work_emails(service, args.hours)
    if not raw_messages:
        log("No messages matched the query — nothing to brief.")
        write_debug("no fg2065 emails found in lookback window")
        return 1

    # ── Categorize ───────────────────────────────────────────────────────────
    categorized: dict[str, list[dict]] = {}
    skipped: list[dict] = []

    for msg in raw_messages:
        sender = get_header(msg, "From")
        subject = get_header(msg, "Subject")
        sent = format_date(msg.get("internalDate", "0"))
        snippet = msg.get("snippet", "")

        category = classify_email(sender, subject)
        if category is None:
            skipped.append({"sender": sender, "subject": subject, "skip_reason": "auto-filtered"})
            continue

        body = extract_plain_body(msg)
        if not body:
            body = re.sub(r"<[^>]+>", " ", extract_html_body(msg))  # strip HTML tags

        entry: dict = {
            "sender": sender,
            "subject": subject,
            "sent": sent,
            "snippet": snippet,
            "body": body,
            "pdf_texts": [],
        }

        # Deep-read: pull PDF attachments for these categories
        if category in ("Patty Press", "Secret Shop", "New Hire / Onboarding"):
            pdfs = get_pdf_attachments(service, msg)
            log(f"  {category}: {len(pdfs)} PDF attachment(s) for '{subject}'")
            for pdf_name, pdf_bytes in pdfs:
                pdf_text = extract_pdf_text(pdf_bytes)
                entry["pdf_texts"].append((pdf_name, pdf_text))
                # Save PDF to newsletter assets
                assets_dir = (
                    REPO_ROOT
                    / "_drafts"
                    / "newsletter"
                    / f"week-of-{monday.isoformat()}"
                    / "assets"
                )
                try:
                    assets_dir.mkdir(parents=True, exist_ok=True)
                    safe_name = re.sub(r'[<>:"/\\|?*]', "_", pdf_name).strip()
                    (assets_dir / safe_name).write_bytes(pdf_bytes)
                    log(f"  Saved PDF: {assets_dir / safe_name}")
                except Exception as exc:
                    log(f"  Could not save PDF {pdf_name}: {exc}")

        # Extra parsing for new hire emails
        if category == "New Hire / Onboarding":
            entry["_hire_info"] = extract_new_hire_info(body, subject)

        categorized.setdefault(category, []).append(entry)

    categorized["_skipped"] = skipped

    total_work = sum(len(v) for k, v in categorized.items() if not k.startswith("_"))
    log(f"Categorized {total_work} work emails across {len([k for k in categorized if not k.startswith('_') and categorized[k]])} categories")

    if total_work == 0:
        log("No actionable work emails found.")
        write_debug("no actionable work emails after filtering")
        return 1

    # ── Build brief ───────────────────────────────────────────────────────────
    brief_md = build_brief(categorized, today)

    # ── Write brief file ──────────────────────────────────────────────────────
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    brief_path = DATA_DIR / f"{today.isoformat()}.md"
    brief_path.write_text(brief_md, encoding="utf-8")
    log(f"Brief written to {brief_path}")

    # Also write to _drafts for local access (best-effort, path may not exist in CI)
    drafts_path = REPO_ROOT / "_drafts" / f"outlook-pull-{today.isoformat()}.md"
    try:
        drafts_path.parent.mkdir(parents=True, exist_ok=True)
        drafts_path.write_text(brief_md, encoding="utf-8")
        log(f"Brief also written to {drafts_path}")
    except Exception as exc:
        log(f"Could not write to _drafts (non-fatal): {exc}")

    # Newsletter rollup feeder
    rollup_dir = REPO_ROOT / "_drafts" / "newsletter" / f"week-of-{monday.isoformat()}"
    try:
        rollup_dir.mkdir(parents=True, exist_ok=True)
        (rollup_dir / f"raw-content-{dow}.md").write_text(brief_md, encoding="utf-8")
        log(f"Newsletter rollup written to {rollup_dir}/raw-content-{dow}.md")
    except Exception as exc:
        log(f"Could not write newsletter rollup (non-fatal): {exc}")

    # ── Send ──────────────────────────────────────────────────────────────────
    if args.dry_run:
        log("--dry-run: skipping email send. Brief preview:")
        print(brief_md[:500])
        return 0

    subject_line = f"Daily Brief — {today.strftime('%Y-%m-%d')}"
    sent_ok = send_brief(service, subject_line, brief_md)
    if not sent_ok:
        write_debug("brief generated but send failed", str(brief_path))
        return 2

    log("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
