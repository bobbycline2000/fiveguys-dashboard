#!/usr/bin/env python3
"""
Daily dashboard-update confirmation email.

Verifies the freshness of every dashboard data section, builds an HTML
status report, and sends it from fg2065@estep-co.com to a configurable
recipient (defaults to fg2065@estep-co.com per Bobby's request).

Reads (env / GitHub Secrets):
    MS_TENANT_ID, MS_CLIENT_ID, MS_CLIENT_SECRET
    CONFIRMATION_FROM       (default: fg2065@estep-co.com)
    CONFIRMATION_TO         (default: fg2065@estep-co.com)
    CONFIRMATION_RUN_LABEL  (e.g. "primary 8:05 AM" or "backup 8:45 AM")
    STORE_ID                (default: 2065)

Exit codes:
    0  email sent successfully (with status of each section in the body)
    1  Graph auth failure
    2  Send mail API failure
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, date, timedelta, timezone
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
RAW  = ROOT / "data" / "raw"

STORE_ID = os.environ.get("STORE_ID", "2065")
TENANT_ID  = os.environ.get("MS_TENANT_ID", "")
CLIENT_ID  = os.environ.get("MS_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("MS_CLIENT_SECRET", "")
FROM_ADDR  = os.environ.get("CONFIRMATION_FROM", "fg2065@estep-co.com")
TO_ADDR    = os.environ.get("CONFIRMATION_TO",   "fg2065@estep-co.com")
RUN_LABEL  = os.environ.get("CONFIRMATION_RUN_LABEL", "primary 8:05 AM ET")

ET = timezone(timedelta(hours=-4))   # EDT; switches to -5 in winter
NOW_ET = datetime.now(tz=ET)
TODAY  = NOW_ET.date()

# Status icons
OK    = "✅"
WARN  = "⚠️"
FAIL  = "❌"


def latest_dated_folder(source: str, prefer_iso_day: bool = True) -> Path | None:
    base = RAW / source / STORE_ID
    if not base.exists():
        return None
    import re as _re
    dirs = [x for x in base.iterdir() if x.is_dir()]
    def keydate(p: Path) -> str:
        m = _re.match(r'^(?:week-ending-)?(\d{4}-\d{2}-\d{2})$', p.name)
        return m.group(1) if m else "0000-00-00"
    dirs.sort(key=keydate, reverse=True)
    if prefer_iso_day:
        # Prefer plain YYYY-MM-DD over week-ending-* if both exist on same date
        daily = [d for d in dirs if _re.match(r'^\d{4}-\d{2}-\d{2}$', d.name)]
        if daily:
            return daily[0]
    return dirs[0] if dirs else None


def find_latest(source: str, filename: str) -> tuple[Path | None, dict | None]:
    base = RAW / source / STORE_ID
    if not base.exists():
        return None, None
    import re as _re
    def keydate(p: Path) -> str:
        m = _re.match(r'^(?:week-ending-)?(\d{4}-\d{2}-\d{2})$', p.name)
        return m.group(1) if m else "0000-00-00"
    for d in sorted([x for x in base.iterdir() if x.is_dir()], key=keydate, reverse=True):
        cand = d / filename
        if cand.exists():
            try:
                return cand, json.loads(cand.read_text(encoding="utf-8"))
            except Exception:
                return cand, None
    return None, None


def folder_iso(p: Path | None) -> str | None:
    if not p:
        return None
    import re as _re
    m = _re.match(r'^(?:week-ending-)?(\d{4}-\d{2}-\d{2})$', p.parent.name)
    return m.group(1) if m else None


def days_old(iso_str: str | None) -> int | None:
    if not iso_str:
        return None
    try:
        d = datetime.strptime(iso_str, "%Y-%m-%d").date()
        return (TODAY - d).days
    except ValueError:
        return None


def section(label: str, max_age_days: int, source: str, filename: str, kpi_fn=None) -> dict:
    """Return {label, status, age_days, message, kpi}."""
    path, data = find_latest(source, filename)
    iso = folder_iso(path)
    age = days_old(iso)
    if path is None:
        return {"label": label, "status": FAIL, "age_days": None,
                "message": f"no data file found at data/raw/{source}/{STORE_ID}/", "kpi": ""}
    kpi = ""
    if kpi_fn and data is not None:
        try:
            kpi = kpi_fn(data) or ""
        except Exception as e:
            kpi = f"(kpi error: {e})"
    if age is None:
        return {"label": label, "status": WARN, "age_days": None,
                "message": f"data found at {path.relative_to(ROOT)} but date unparseable",
                "kpi": kpi}
    if age > max_age_days:
        return {"label": label, "status": WARN, "age_days": age,
                "message": f"stale: {age} days old (file dated {iso}, threshold {max_age_days}d)",
                "kpi": kpi}
    return {"label": label, "status": OK, "age_days": age,
            "message": f"fresh ({age}d old, dated {iso})", "kpi": kpi}


def kpi_sales(d: dict) -> str:
    net = d.get("net_sales") or d.get("totals", {}).get("net_sales")
    orders = d.get("order_count") or d.get("orders") or d.get("totals", {}).get("orders")
    guests = d.get("guest_count") or d.get("guests") or d.get("totals", {}).get("guests")
    if net is None:
        return ""
    return f"${net:,.2f} net • {orders or '?'} orders • {guests or '?'} guests"

def kpi_hourly(d: dict) -> str:
    t = d.get("totals", {}) if isinstance(d.get("totals"), dict) else d
    net = t.get("net_sales") or t.get("net")
    lab = t.get("labor_dollars") or t.get("labor")
    pct = t.get("labor_percent") or t.get("labor_pct")
    if net is None:
        return ""
    return f"${net:,.2f} net • ${lab:,.2f} labor • {pct}% labor"

def kpi_perf(d: dict) -> str:
    sales = (d.get("sales") or {}).get("today")
    labor_pct = (d.get("labor") or {}).get("pct")
    wtd_pct = (d.get("labor") or {}).get("pct_week")
    parts = []
    if sales is not None:
        parts.append(f"${sales:,.2f} sales")
    if labor_pct is not None:
        parts.append(f"{labor_pct}% labor today")
    if wtd_pct is not None:
        parts.append(f"{wtd_pct}% WTD")
    return " • ".join(parts)

def kpi_cogs(d: dict) -> str:
    pct = d.get("cogs_pct_week")
    goal = d.get("cogs_goal_pct")
    vtg = d.get("variance_to_goal_week")
    if pct is None:
        return ""
    return f"{pct}% (goal {goal}%, var {vtg:+.1f}%)"

def kpi_discounts(d: dict) -> str:
    total = d.get("total_amount") or d.get("total_dollars")
    count = d.get("total_count") or d.get("redemptions")
    comps = d.get("comps_total")
    discs = d.get("discounts_total")
    if total is None:
        return ""
    parts = [f"${total:,.2f} on {count or '?'} redemptions"]
    if comps is not None or discs is not None:
        parts.append(f"comps ${comps or 0:,.2f} / discounts ${discs or 0:,.2f}")
    return " • ".join(parts)

def kpi_schedule(d: dict) -> str:
    today_iso = TODAY.isoformat()
    sched = d.get("schedule", {})
    if today_iso in sched:
        s = sched[today_iso]
        return f"{len(s.get('shifts', []))} shifts • {s.get('scheduled_hours', '?')}h scheduled today"
    week_total = (d.get("totals_by_day") or {}).get("week_total")
    if week_total:
        return f"week total {week_total}h (today's date not in this schedule)"
    return ""

def kpi_compliance(d: dict) -> str:
    pct = d.get("overall_pct")
    if pct is None:
        return ""
    return f"{pct}% overall"

def kpi_shops(d: dict) -> str:
    score = d.get("latest_score") or d.get("score")
    return f"{score}" if score is not None else ""


def gather_sections() -> list[dict]:
    return [
        section("Sales / Transactions / Per Guest", 2,
                "parbrink", "sales_summary.json", kpi_sales),
        section("Hourly Sales & Labor",             2,
                "parbrink", "hourly_sales_labor.json", kpi_hourly),
        section("Comps & Discounts",                2,
                "parbrink", "discount_summary.json", kpi_discounts),
        section("Today's Schedule",                 8,
                "parbrink", "weekly_schedule.json", kpi_schedule),
        section("CrunchTime Performance Metrics",   2,
                "crunchtime", "perf_metrics.json", kpi_perf),
        section("Food Cost (COGS Flash Report)",    8,
                "crunchtime", "cogs_variance.json", kpi_cogs),
        section("ComplianceMate",                   2,
                "compliancemate", "lists.json", kpi_compliance),
        section("Secret Shops (KnowledgeForce)",   14,
                "marketforce", "shops.json", kpi_shops),
    ]


def overall_status(rows: list[dict]) -> str:
    if any(r["status"] == FAIL for r in rows):
        return FAIL
    if any(r["status"] == WARN for r in rows):
        return WARN
    return OK


def get_token() -> str:
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    resp = requests.post(url, data={
        "grant_type":    "client_credentials",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope":         "https://graph.microsoft.com/.default",
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()["access_token"]


def build_html(rows: list[dict], overall: str) -> str:
    pulled = NOW_ET.strftime("%A, %B %d %Y at %I:%M %p ET")
    overall_text = {OK: "All sections up to date",
                    WARN: "Updated — some sections stale",
                    FAIL: "Update incomplete — sections missing"}[overall]
    rows_html = "".join(
        f"<tr>"
        f"<td style='padding:8px 12px;font-size:18px;'>{r['status']}</td>"
        f"<td style='padding:8px 12px;font-weight:600;'>{r['label']}</td>"
        f"<td style='padding:8px 12px;color:#444;'>{r['kpi'] or '—'}</td>"
        f"<td style='padding:8px 12px;color:#888;font-size:13px;'>{r['message']}</td>"
        f"</tr>"
        for r in rows
    )
    return f"""
<!doctype html>
<html><body style="font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;color:#222;background:#f4f4f4;margin:0;padding:0;">
  <div style="max-width:760px;margin:0 auto;background:#fff;">
    <div style="background:#DA291C;color:#fff;padding:18px 24px;">
      <div style="font-size:22px;font-weight:700;">Five Guys Dashboard — Daily Update</div>
      <div style="font-size:14px;opacity:.9;margin-top:4px;">Store {STORE_ID} • {RUN_LABEL} • {pulled}</div>
    </div>
    <div style="padding:18px 24px;border-bottom:1px solid #eee;">
      <div style="font-size:18px;">{overall} <strong>{overall_text}</strong></div>
      <div style="font-size:13px;color:#666;margin-top:6px;">
        Live dashboard: <a href="https://bobbycline2000.github.io/fiveguys-dashboard/dashboard.html">bobbycline2000.github.io/fiveguys-dashboard/dashboard.html</a>
      </div>
    </div>
    <table style="border-collapse:collapse;width:100%;font-size:14px;">
      <thead>
        <tr style="background:#f8f8f8;text-align:left;">
          <th style="padding:8px 12px;width:36px;"></th>
          <th style="padding:8px 12px;">Section</th>
          <th style="padding:8px 12px;">Latest values</th>
          <th style="padding:8px 12px;">Freshness</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
    <div style="padding:14px 24px;color:#888;font-size:12px;border-top:1px solid #eee;">
      Generated automatically by daily_dashboard.yml. Reply to this email is not monitored — corrections go in #phil-bobby.
    </div>
  </div>
</body></html>
""".strip()


def send_mail(html: str, subject: str) -> None:
    token = get_token()
    url = f"https://graph.microsoft.com/v1.0/users/{FROM_ADDR}/sendMail"
    payload = {
        "message": {
            "subject": subject,
            "body": {"contentType": "HTML", "content": html},
            "toRecipients": [{"emailAddress": {"address": TO_ADDR}}],
        },
        "saveToSentItems": True,
    }
    resp = requests.post(url, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }, data=json.dumps(payload), timeout=30)
    if not resp.ok:
        print(f"sendMail failed: {resp.status_code} {resp.text[:500]}")
        sys.exit(2)
    print(f"Sent confirmation to {TO_ADDR} from {FROM_ADDR}")


def main():
    if not (TENANT_ID and CLIENT_ID and CLIENT_SECRET):
        print("MS_TENANT_ID / MS_CLIENT_ID / MS_CLIENT_SECRET not set — skipping confirmation email.")
        sys.exit(0)
    rows = gather_sections()
    overall = overall_status(rows)
    subject_prefix = {OK: "[OK]", WARN: "[STALE]", FAIL: "[FAIL]"}[overall]
    subject = f"{subject_prefix} Dashboard Updated — {TODAY.isoformat()} ({RUN_LABEL})"
    html = build_html(rows, overall)
    print(f"Overall: {overall}")
    for r in rows:
        print(f"  {r['status']} {r['label']:40s} {r['message']}")
    send_mail(html, subject)


if __name__ == "__main__":
    main()
