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


def _load_dash_html() -> str | None:
    """Return dashboard.html contents, or None if file missing."""
    dash = ROOT / "dashboard.html"
    if not dash.exists():
        return None
    return dash.read_text(encoding="utf-8")


def _value_check(label: str, html: str, needle: str, source_desc: str) -> dict | None:
    """Return a FAIL row if `needle` is not present in `html`, else None."""
    if not html or not needle:
        return None
    if needle not in html:
        return {
            "label": f"Value-cross-check: {label}",
            "status": FAIL,
            "age_days": None,
            "message": (
                f"dashboard.html does NOT contain '{needle}' "
                f"(source: {source_desc}) — "
                f"the {label} card may be stale or wiring failed."
            ),
            "kpi": f"expected {needle}",
        }
    return None


def _check_labor_wired() -> dict | None:
    """Cross-check: verify dashboard.html displays the labor % from
    data/labor_today.json (CT API).  Falls back to Par Brink hourly PDF
    if labor_today.json is absent.  Returns a FAIL row on mismatch."""
    html = _load_dash_html()
    if not html:
        return None

    # Primary: CrunchTime API labor_today.json
    ct_labor_path = ROOT / "data" / "labor_today.json"
    if ct_labor_path.exists():
        try:
            ct_labor = json.loads(ct_labor_path.read_text(encoding="utf-8"))
            labor_pct = ct_labor.get("labor_percent")
            labor_dollars = ct_labor.get("labor_dollars")
            if labor_pct is not None:
                needle_pct = f"{labor_pct:.1f}%"
                return _value_check(
                    "Labor %",
                    html,
                    needle_pct,
                    f"labor_today.json (CT API, dated {ct_labor.get('date', '?')})",
                )
        except Exception:
            pass

    # Fallback: Par Brink hourly_sales_labor.json
    _, hl = find_latest("parbrink", "hourly_sales_labor.json")
    if hl is None:
        return None
    totals = hl.get("totals", {}) if isinstance(hl.get("totals"), dict) else hl
    labor_pct = totals.get("labor_percent")
    if labor_pct is None:
        return None
    needle_pct = f"{labor_pct:.1f}%"
    return _value_check(
        "Labor %",
        html,
        needle_pct,
        "hourly_sales_labor.json (Par Brink PDF fallback)",
    )


def _check_sales_wired() -> dict | None:
    """Cross-check: verify dashboard.html shows the net sales from sales_summary.json."""
    html = _load_dash_html()
    if not html:
        return None
    _, ss = find_latest("parbrink", "sales_summary.json")
    if ss is None:
        return None
    net = ss.get("net_sales") or ss.get("totals", {}).get("net_sales")
    if net is None:
        return None
    needle = f"${net:,.0f}"
    return _value_check("Daily Net Sales", html, needle,
                        f"sales_summary.json (Par Brink, net_sales={net})")


def _check_food_cost_wired() -> dict | None:
    """Cross-check: verify dashboard.html shows the COGS % from cogs_variance.json."""
    html = _load_dash_html()
    if not html:
        return None
    _, cogs = find_latest("crunchtime", "cogs_variance.json")
    if cogs is None:
        return None
    pct = cogs.get("cogs_pct_week")
    if pct is None:
        return None
    needle = f"{float(pct):.1f}%"
    return _value_check("Food Cost %", html, needle,
                        f"cogs_variance.json (cogs_pct_week={pct})")


def _check_compliance_wired() -> dict | None:
    """Cross-check: verify dashboard.html shows ComplianceMate required-list %.

    wire_dashboard.py computes required-only average (not raw overall_pct) using
    the REQUIRED_SRC set below.  We must match that logic here or we'll always
    false-alarm when optional checklists (Closing, Weekly Inspection, etc.) are 0%.
    """
    html = _load_dash_html()
    if not html:
        return None
    _, cm = find_latest("compliancemate", "compliance.json")
    if cm is None:
        _, cm = find_latest("compliancemate", "lists.json")
    if cm is None:
        cm_path = ROOT / "data" / "compliancemate.json"
        if cm_path.exists():
            try:
                cm = json.loads(cm_path.read_text(encoding="utf-8"))
            except Exception:
                pass
    if cm is None:
        return None

    # Mirror the REQUIRED_SRC set from wire_dashboard.py so the check is aligned.
    _REQUIRED_SRC = {
        "AM Pre-Shift Check", "11AM: Time and Temp", "Shift Change",
        "3PM: Time and Temp", "5PM: Time and Temp", "PM Pre-Shift Check",
        "7PM: Time and Temp", "9PM: Time and Temp", "Closing Checklist",
    }
    req_lists = [l for l in cm.get("lists", []) if l.get("name") in _REQUIRED_SRC]
    if req_lists:
        computed_pct = round(sum(l["pct"] for l in req_lists) / len(req_lists))
        needle = f"{computed_pct}%"
        source_note = f"compliance.json (required-only computed={computed_pct}%, raw overall_pct={cm.get('overall_pct')})"
    else:
        # No required lists found — fall back to raw overall_pct
        pct = cm.get("overall_pct")
        if pct is None:
            return None
        needle = f"{pct}%"
        source_note = f"compliance.json (overall_pct={pct}, no required lists found)"

    return _value_check("ComplianceMate %", html, needle, source_note)


def _check_shops_wired() -> dict | None:
    """Cross-check: verify dashboard.html shows latest secret shop score."""
    html = _load_dash_html()
    if not html:
        return None
    _, ss = find_latest("marketforce", "shops.json")
    if ss is None:
        return None
    latest_shop = ss.get("latest", {})
    score = latest_shop.get("score")
    if score is None:
        return None
    needle = f"{score:.0f}%"
    return _value_check("Secret Shop score", html, needle,
                        f"shops.json (latest score={score})")


def _check_100pct_participation() -> dict | None:
    """
    Warn if any 100% shop has zero names in participation.json.
    A missing name list means the payout email draft has a blank roster —
    Bobby cannot process the payout without knowing who was on shift.
    """
    _, shops_data = find_latest("marketforce", "shops.json")
    if shops_data is None:
        return None
    shops = shops_data.get("shops", [])
    perfect = [s for s in shops if float(s.get("score", 0)) == 100.0]
    if not perfect:
        return None

    # Load participation.json from the marketforce store folder (not date-bucketed)
    part_path = RAW / "marketforce" / STORE_ID / "participation.json"
    by_shop: dict = {}
    if part_path.exists():
        try:
            by_shop = json.loads(part_path.read_text(encoding="utf-8")).get("by_shop", {})
        except Exception:
            pass

    missing = [
        s for s in perfect
        if not by_shop.get(s.get("job_id"), [])
    ]
    if not missing:
        return None

    job_ids = ", ".join(s.get("job_id", "?") for s in missing)
    return {
        "label": "100% Shop — participation gap",
        "status": WARN,
        "age_days": None,
        "message": (
            f"{len(missing)} 100% shop(s) have zero names in participation.json "
            f"(job_id(s): {job_ids}) — payout draft will have blank roster. "
            f"Check debug-log.txt for ZERO_NAMES_100PCT_SHOP or PARTICIPATION_RETRY_FAILED."
        ),
        "kpi": f"{len(missing)} shop(s) missing names",
    }


def gather_sections() -> list[dict]:
    rows = [
        section("Sales / Transactions / Per Guest", 2,
                "parbrink", "sales_summary.json", kpi_sales),
        section("Hourly Sales & Labor (Par Brink)",  2,
                "parbrink", "hourly_sales_labor.json", kpi_hourly),
        section("CrunchTime Labor API",              2,
                "crunchtime", "labor_today.json",  # placeholder path; checked directly below
                None),
        section("Comps & Discounts",                2,
                "parbrink", "discount_summary.json", kpi_discounts),
        section("Today's Schedule",                 8,
                "parbrink", "weekly_schedule.json", kpi_schedule),
        section("CrunchTime Performance Metrics",   2,
                "crunchtime", "perf_metrics.json", kpi_perf),
        section("Food Cost (COGS Flash Report)",    8,
                "crunchtime", "cogs_variance.json", kpi_cogs),
        section("ComplianceMate",                   2,
                "compliancemate", "compliance.json", kpi_compliance),
        section("Secret Shops (KnowledgeForce)",   14,
                "marketforce", "shops.json", kpi_shops),
    ]

    # ── Replace CrunchTime Labor API row with a direct file check ───────────
    # data/labor_today.json lives in ROOT/data/, not in data/raw/crunchtime/
    # so the generic section() helper can't find it. Swap it out.
    rows = [r for r in rows if r["label"] != "CrunchTime Labor API"]
    ct_labor_path = ROOT / "data" / "labor_today.json"
    if ct_labor_path.exists():
        try:
            ct_labor = json.loads(ct_labor_path.read_text(encoding="utf-8"))
            clt_date = ct_labor.get("date")
            age = days_old(clt_date)
            labor_pct = ct_labor.get("labor_percent")
            labor_dol = ct_labor.get("labor_dollars")
            kpi_str = ""
            if labor_pct is not None:
                kpi_str = f"{labor_pct:.1f}%"
                if labor_dol is not None:
                    kpi_str += f" / ${labor_dol:,.0f}"
            if age is None:
                status = WARN
                msg = "labor_today.json: date field missing"
            elif age > 1:
                status = WARN
                msg = f"stale: {age} days old (dated {clt_date})"
            else:
                status = OK
                msg = f"fresh ({age}d old, dated {clt_date}) — CT API"
            rows.insert(1, {"label": "CrunchTime Labor API", "status": status,
                            "age_days": age, "message": msg, "kpi": kpi_str})
        except Exception as e:
            rows.insert(1, {"label": "CrunchTime Labor API", "status": WARN,
                            "age_days": None,
                            "message": f"labor_today.json parse error: {e}", "kpi": ""})
    else:
        rows.insert(1, {"label": "CrunchTime Labor API", "status": FAIL,
                        "age_days": None,
                        "message": "labor_today.json not found — scrape_labor_ct.py may have failed",
                        "kpi": ""})

    # ── Value cross-checks (Change B) ────────────────────────────────────────
    # Each check extracts the key metric from the source JSON and greps
    # dashboard.html for that exact formatted value. If not found → FAIL.
    for check_fn in (
        _check_labor_wired,
        _check_sales_wired,
        _check_food_cost_wired,
        _check_compliance_wired,
        _check_shops_wired,
        _check_100pct_participation,
    ):
        result = check_fn()
        if result:
            rows.append(result)

    return rows


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
    # Graph path only when the Azure app secrets exist (they don't in CI —
    # Bobby is not tenant admin). Otherwise send via the SCG Gmail token,
    # which CI restores every run for Par Brink pickup and which carries
    # gmail.send scope. Before 2026-07-05 the missing secrets meant this
    # email silently never sent.
    if TENANT_ID and CLIENT_ID and CLIENT_SECRET:
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
        return

    from notify_gmail import send as gmail_send
    gmail_send(TO_ADDR, subject, html)
    print(f"Sent confirmation to {TO_ADDR} via SCG Gmail (Graph secrets not set)")


def main():
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
