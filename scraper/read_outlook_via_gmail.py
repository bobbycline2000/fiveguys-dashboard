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


def build_blackberry_lto_update(today: date) -> list[str]:
    """Blackberry LTO countdown + training reminders. Active until end date."""
    launch = date(2026, 5, 25)
    fgu_due = date(2026, 5, 15)
    pos_active = date(2026, 5, 18)
    force_ship_start = date(2026, 5, 4)
    force_ship_end = date(2026, 5, 15)
    end_date = date(2026, 8, 16)

    if today > end_date:
        return []

    lines: list[str] = []
    lines.append("**🫐 Blackberry LTO — In-Store Prep**")
    days_to_launch = (launch - today).days
    days_to_fgu = (fgu_due - today).days
    days_to_pos = (pos_active - today).days

    if today < launch:
        lines.append(f"- **Launch in {days_to_launch} days** (May 25, 2026). Online ordering activates same day.")
    else:
        days_since = (today - launch).days
        days_remaining = (end_date - today).days
        lines.append(f"- LTO is **LIVE** (launched {days_since} days ago). Ends Aug 16 ({days_remaining} days remaining).")

    if today < fgu_due:
        urgency = "🔴 OVERDUE prep" if days_to_fgu <= 7 else "🟡 do this week"
        lines.append(f"- **FGU course due May 15** ({days_to_fgu} days) — {urgency}. Every shift lead + GM completes.")
    if today < pos_active:
        lines.append(f"- POS activation **May 18** ({days_to_pos} days). Verify menu button placement same day.")
    if today < force_ship_end and today >= force_ship_start - timedelta(days=3):
        lines.append(f"- Product force-shipping **May 4–15**. Two cases per store. Storage prep: clear space at fountainside, beside banana marinade. Shelf life of in-use syrup is **7 days**.")
    elif today < force_ship_start:
        days_to_ship = (force_ship_start - today).days
        lines.append(f"- Product ships starting May 4 ({days_to_ship} days). Make sure walk-in has space.")

    lines.append("- Each store sets its own shake pricing — confirm the price point before launch.")
    lines.append("- Menu board lug-on sign ships Week of May 18 (we get invoiced — expect it).")
    return lines


def build_shift_huddle_plan(today: date, categorized: dict[str, list[dict]] | None = None) -> str:
    """Daily 5-minute shift huddle plan focused on in-store operations.
    Anchors are constant (the fundamentals don't change), but the spotlight
    rotates by day-of-week so the team hears emphasis on different areas
    across the week. Pulled into every brief moving forward."""
    # Day-of-week spotlight rotation — 0=Monday … 6=Sunday
    dow = today.weekday()
    spotlight_by_dow = {
        0: ("Stainless Steel + Handwashing",
            "Hand sinks should sparkle — wipe down stainless steel around hand sinks first thing. "
            "Handwash procedure: 20 seconds, soap to wrists, rinse thoroughly, paper towel only. "
            "Demo the wash for anyone unsure."),
        1: ("Ticket Times + Guest Greeting",
            "TICKET TIMES are huge. Register-to-window under 6 minutes, every order. "
            "Greet at the door AND at the register — eye contact, smile, energy. "
            "Call-back the order on hand-off. Thank every guest leaving."),
        2: ("Dumpster Area + Garbage Cans",
            "Walk the dumpster area before opening — doors CLOSED, area swept, no overflow. "
            "Garbage cans inside: liners straight, lids clean, no overflow. "
            "Lobby cans checked every 30 minutes minimum."),
        3: ("Smiling Faces + Energy + Call-Back",
            "Energy at the register sets the tone for the whole shift. Smile, make eye contact, "
            "call-back the order so the guest knows you heard them. Hand-off with a thank-you."),
        4: ("Secret Shop Review + Friday Reset",
            "Shop scores arrive Thu/Fri. Today we review — what worked, what didn't, what changes. "
            "Reset the lobby, hit the deep-clean items, and walk into the weekend tight."),
        5: ("Saturday Volume + Speed",
            "Saturday is our biggest day. Speed of service matters more than ever. "
            "Pre-position fries, keep buns ahead of the line, second person on register at peak."),
        6: ("Reset + Week Ahead",
            "Sunday close = Monday's open. Deep clean wherever the week was light. "
            "Walk-through with the closing manager — what are we starting Monday with?"),
    }
    spotlight_title, spotlight_body = spotlight_by_dow[dow]

    lines: list[str] = []
    lines.append("## 📋 Shift Huddle Plan — Today's 5-Minute Pre-Shift")
    lines.append(f"*({today.strftime('%A %B %d')} — read this to the team before the shift starts.)*")
    lines.append("")

    lines.append(f"### 🎯 Today's Spotlight: {spotlight_title}")
    lines.append("")
    lines.append(f"> {spotlight_body}")
    lines.append("")

    lines.append("### The Fundamentals — Hit These Every Shift")
    lines.append("")
    lines.append("**1. Guest Experience**")
    lines.append("- Greet at the **door** AND at the **register** — eye contact, smile, energy.")
    lines.append("- **Call-back** every order so the guest knows you heard them.")
    lines.append("- Thank every guest on the way out. No one walks past silent.")
    lines.append("")
    lines.append("**2. Ticket Times — HUGE**")
    lines.append("- Register → window in **under 6 minutes**, every order.")
    lines.append("- If we're slipping, second person on register, somebody bagging, somebody calling out.")
    lines.append("- Watch the screen. Don't let an order sit.")
    lines.append("")
    lines.append("**3. Cleanliness (Steritech-ready every shift)**")
    lines.append("- **Stainless steel around hand sinks** — wipe down, no streaks, no splash marks.")
    lines.append("- **Garbage cans** — lids clean, liners straight, never overflowing.")
    lines.append("- **Dumpster area** — doors CLOSED, area swept, no debris.")
    lines.append("- Lobby sweep every 15 minutes during peak. Tables wiped between guests.")
    lines.append("")
    lines.append("**4. Handwashing**")
    lines.append("- 20 seconds, soap to wrists, paper towel only — no shortcuts.")
    lines.append("- After every register-to-grill transition, every break, every glove change.")
    lines.append("- Hand sinks are for handwashing ONLY — never grill water, never anything else.")
    lines.append("")
    lines.append("**5. Energy & Attitude**")
    lines.append("- Smiles are the cheapest thing we sell and they bring guests back.")
    lines.append("- If you're tired, the guest can hear it. Pick it up.")
    lines.append("- Lead each other — call out wins, fix gaps in the moment.")
    lines.append("")
    lines.append("### What Corporate / The Shop Sees")
    lines.append("- A 100% shop = the team gets paid. **Every shop is real money on the line.**")
    lines.append("- One bad shift can drop a quarter average. Stay sharp every shift.")
    lines.append("")

    # ── Training & Corporate Updates ─────────────────────────────────────────
    training_lines: list[str] = []

    # Blackberry LTO is the active major rollout — surface it every shift
    bb = build_blackberry_lto_update(today)
    if bb:
        training_lines.extend(bb)
        training_lines.append("")

    # Director directives surfaced when present (Brad Davis emails today)
    if categorized:
        director_emails = categorized.get("Director's Corner", [])
        if director_emails:
            training_lines.append("**👔 From the Director (Brad Davis) — today**")
            for em in director_emails[:2]:  # cap at 2 to keep huddle tight
                subj = em.get("subject", "")
                body = (em.get("body", "") or em.get("snippet", "")).strip()
                training_lines.append(f"- **{subj}** — {body[:300]}")
            training_lines.append("")

        # Patty Press / corporate training reminders surfaced when present
        patty = categorized.get("Patty Press", [])
        corp = categorized.get("Corporate Announcements", [])
        if patty or corp:
            training_lines.append("**📺 Training / Corporate this week** — see brief above for full content. "
                                  "Read the relevant Patty Press section before shift; assign FGU courses on a TV/tablet during prep if any are open.")
            training_lines.append("")

    if training_lines:
        lines.append("### Training & Corporate Updates")
        lines.append("")
        lines.extend(training_lines)

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

    # ── Shift Huddle Plan (always — runs every brief) ────────────────────────
    huddle = build_shift_huddle_plan(today, categorized)
    if huddle:
        lines.append(huddle)

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


# ── HTML renderer ────────────────────────────────────────────────────────────

def md_to_html(md: str) -> str:
    """Converts the brief markdown into a styled HTML email — Five Guys brand."""
    RED   = "#DA291C"
    NAVY  = "#1A2744"
    GOLD  = "#F5C518"
    LGRAY = "#F7F7F7"
    MGRAY = "#E0E0E0"

    css = f"""
    <style>
      body {{font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#222;background:#fff;margin:0;padding:0}}
      .wrapper {{max-width:680px;margin:0 auto;background:#fff}}
      .header {{background:{RED};color:#fff;padding:18px 24px;border-radius:4px 4px 0 0}}
      .header h1 {{margin:0;font-size:20px;font-weight:700;letter-spacing:0.5px}}
      .header .meta {{font-size:12px;opacity:0.85;margin-top:4px}}
      .body {{padding:0 24px 24px}}
      h2 {{font-size:15px;font-weight:700;color:{NAVY};border-left:4px solid {RED};
           padding:8px 12px;background:{LGRAY};margin:20px 0 8px;border-radius:0 4px 4px 0}}
      h2.critical {{border-left-color:{RED};background:#FFF0EF;color:{RED}}}
      h2.director {{border-left-color:{NAVY};background:#EEF1F8}}
      h2.shop     {{border-left-color:{GOLD};background:#FFFBEE}}
      h2.huddle   {{border-left-color:#2E7D32;background:#F1F8F1}}
      h3 {{font-size:13px;font-weight:700;color:{NAVY};margin:14px 0 4px;padding-left:4px}}
      p  {{margin:4px 0 10px;line-height:1.55}}
      ul {{margin:4px 0 10px 18px;padding:0;line-height:1.6}}
      li {{margin-bottom:3px}}
      table {{border-collapse:collapse;width:100%;margin:10px 0 14px;font-size:13px}}
      th {{background:{NAVY};color:#fff;padding:7px 10px;text-align:left;font-weight:700}}
      td {{padding:6px 10px;border-bottom:1px solid {MGRAY}}}
      tr:nth-child(even) td {{background:{LGRAY}}}
      blockquote {{border-left:4px solid {GOLD};margin:10px 0;padding:8px 14px;
                   background:#FFFBEE;color:#444;font-style:italic;border-radius:0 4px 4px 0}}
      .pill-red  {{display:inline-block;background:{RED};color:#fff;border-radius:3px;
                   padding:1px 7px;font-size:12px;font-weight:700}}
      .pill-gold {{display:inline-block;background:{GOLD};color:#111;border-radius:3px;
                   padding:1px 7px;font-size:12px;font-weight:700}}
      .footer {{font-size:11px;color:#999;text-align:center;padding:12px;
                border-top:1px solid {MGRAY};margin-top:16px}}
      hr {{border:none;border-top:1px solid {MGRAY};margin:16px 0}}
      strong {{color:#111}}
      code {{background:{LGRAY};padding:1px 5px;border-radius:3px;font-size:12px}}
    </style>"""

    lines = md.split("\n")
    html_lines: list[str] = []
    in_table = False
    table_header_done = False
    in_ul = False

    def flush_ul():
        nonlocal in_ul
        if in_ul:
            html_lines.append("</ul>")
            in_ul = False

    def flush_table():
        nonlocal in_table, table_header_done
        if in_table:
            html_lines.append("</table>")
            in_table = False
            table_header_done = False

    def inline(text: str) -> str:
        """Apply inline markdown: bold, italic, code, emoji passthrough."""
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"\*(.+?)\*",     r"<em>\1</em>",         text)
        text = re.sub(r"`(.+?)`",       r"<code>\1</code>",      text)
        return text

    for raw_line in lines:
        line = raw_line.rstrip()

        # --- horizontal rule ---
        if re.match(r"^-{3,}$", line):
            flush_ul(); flush_table()
            html_lines.append("<hr>")
            continue

        # --- blank line ---
        if line.strip() == "":
            flush_ul(); flush_table()
            html_lines.append("")
            continue

        # --- H1 (title — handled separately in wrapper) ---
        if line.startswith("# ") and not line.startswith("## "):
            flush_ul(); flush_table()
            # Skip — title goes in the header block
            continue

        # --- H2 ---
        if line.startswith("## "):
            flush_ul(); flush_table()
            text = line[3:].strip()
            cls = "critical" if "CRITICAL" in text.upper() else \
                  "director" if "DIRECTOR" in text.upper() else \
                  "shop"     if "SECRET SHOP" in text.upper() else \
                  "huddle"   if "HUDDLE" in text.upper() else ""
            html_lines.append(f'<h2 class="{cls}">{inline(text)}</h2>')
            continue

        # --- H3 ---
        if line.startswith("### "):
            flush_ul(); flush_table()
            html_lines.append(f"<h3>{inline(line[4:].strip())}</h3>")
            continue

        # --- blockquote ---
        if line.startswith("> "):
            flush_ul(); flush_table()
            html_lines.append(f"<blockquote>{inline(line[2:].strip())}</blockquote>")
            continue

        # --- table row ---
        if line.startswith("|"):
            flush_ul()
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(re.match(r"^[-: ]+$", c) for c in cells):
                table_header_done = True
                continue
            if not in_table:
                in_table = True
                table_header_done = False
                html_lines.append("<table>")
            if not table_header_done:
                html_lines.append("<tr>" + "".join(f"<th>{inline(c)}</th>" for c in cells) + "</tr>")
                table_header_done = True
            else:
                html_lines.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells) + "</tr>")
            continue

        flush_table()

        # --- bullet list ---
        m = re.match(r"^(\s*)[*\-]\s+(.+)", line)
        if m:
            if not in_ul:
                html_lines.append("<ul>")
                in_ul = True
            html_lines.append(f"<li>{inline(m.group(2))}</li>")
            continue

        flush_ul()

        # --- plain paragraph ---
        if line.strip():
            html_lines.append(f"<p>{inline(line.strip())}</p>")

    flush_ul()
    flush_table()

    # Extract title from first H1 in md
    title_match = re.search(r"^# (.+)$", md, re.MULTILINE)
    title = title_match.group(1) if title_match else "Daily Brief"

    # Extract pull time
    meta_match = re.search(r"\*\*Pull time:\*\*\s*(.+?)\s*\|", md)
    meta = meta_match.group(1) if meta_match else ""

    body_html = "\n".join(html_lines)

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8">{css}</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>🍔 {title}</h1>
    <div class="meta">Store 2065 — Dixie Highway, Louisville KY &nbsp;|&nbsp; {meta}</div>
  </div>
  <div class="body">
    {body_html}
  </div>
  <div class="footer">Generated by Prometheus &nbsp;·&nbsp; fg2065@estep-co.com</div>
</div>
</body>
</html>"""


# ── Email send ───────────────────────────────────────────────────────────────

def send_brief(service, subject: str, body_md: str) -> bool:
    """Sends the brief from bob.cline2000@gmail.com to fg2065@estep-co.com."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = FROM_ADDRESS
    msg["To"] = TO_ADDRESS

    msg.attach(MIMEText(body_md, "plain"))
    msg.attach(MIMEText(md_to_html(body_md), "html"))

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

    # ── Write team_notes.json for dashboard Team Notes card ──────────────────
    try:
        notes = []
        now_str = datetime.now().strftime("%-I:%M %p")

        # Director messages → red border
        for em in categorized.get("Director's Corner", []):
            body = (em.get("body") or em.get("snippet") or "").strip()
            body = re.sub(r"\s+", " ", body)[:300]
            notes.append({
                "from": "Brad Davis",
                "role": "director",
                "role_label": "Director",
                "time": f"Today {now_str}",
                "body": body,
            })

        # Crystal / DM messages → gold border
        for em in categorized.get("Crystal Hess (DM)", []):
            body = (em.get("body") or em.get("snippet") or "").strip()
            body = re.sub(r"\s+", " ", body)[:300]
            notes.append({
                "from": "Crystal Hess",
                "role": "dm",
                "role_label": "DM",
                "time": f"Today {now_str}",
                "body": body,
            })

        # Critical / new-hire items → plain GM note
        for em in categorized.get("New Hire / Onboarding", []):
            hire = em.get("_hire_info", {})
            names = ", ".join(hire.get("names", [])) or "New hire"
            action = hire.get("action", "review and action")
            notes.append({
                "from": "Prometheus",
                "role": "gm",
                "role_label": "Alert",
                "time": f"Today {now_str}",
                "body": f"🚨 New hire: {names} — {action}",
            })

        team_notes_path = REPO_ROOT / "data" / "team_notes.json"
        team_notes_path.parent.mkdir(parents=True, exist_ok=True)
        team_notes_path.write_text(
            json.dumps({"notes": notes, "new_count": len(notes), "date": today.isoformat()}, indent=2),
            encoding="utf-8"
        )
        log(f"team_notes.json written — {len(notes)} note(s)")
    except Exception as exc:
        log(f"Could not write team_notes.json (non-fatal): {exc}")

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
