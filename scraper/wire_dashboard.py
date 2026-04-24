"""
Wire live data into dashboard.html.

Idempotent: uses regex with structural anchors (class + adjacent label) rather
than exact old values, so it works correctly on any run — even after the
dashboard has already been wired once. This fixes the class of bug where the
dashboard silently stopped updating after the first successful run.
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "dashboard.html"
STORE_ID = "2065"
RAW = ROOT / "data" / "raw"

# ── critical fields — failures here flag the dashboard as stale ─────────
CRITICAL_LABELS = {
    "date-chip",
    "last-updated time",
    "Daily Sales value",
    "Daily Sales sub",
    "Sales / Guest value",
    "Compliance value",
    "footer timestamp",
}

def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))

def load_latest(source, report):
    base = RAW / source / STORE_ID
    if base.exists():
        for d in sorted([x for x in base.iterdir() if x.is_dir()], reverse=True):
            cand = d / report
            if cand.exists():
                return json.loads(cand.read_text(encoding="utf-8")), cand
    return None, None

# ── data ────────────────────────────────────────────────────────────────
latest, _ = load_latest("crunchtime", "perf_metrics.json")
if latest is None:
    latest = load("data/latest.json")

cm, _ = load_latest("compliancemate", "lists.json")
if cm is None:
    cm = load("data/compliancemate.json")

ss, _ = load_latest("marketforce", "shops.json")
if ss is None:
    try:
        ss = load("data/secret_shops.json")
    except FileNotFoundError:
        ss = None

cogs, _ = load_latest("crunchtime", "cogs_variance.json")
if cogs is None:
    try:
        cogs = load("data/cogs_variance.json")
    except FileNotFoundError:
        cogs = None

sched, sched_path = load_latest("parbrink", "weekly_schedule.json")
if sched is None:
    legacy = sorted((ROOT / "data" / "parbrink").glob("*/weekly_schedule_2065.json"))
    if legacy:
        sched_path = legacy[-1]
        sched = json.loads(sched_path.read_text(encoding="utf-8"))

# ── derived values ──────────────────────────────────────────────────────
now = datetime.now()
time_str = now.strftime("%#I:%M %p") if sys.platform == "win32" else now.strftime("%-I:%M %p")
date_display = now.strftime("%B %d %Y").replace(" 0", " ")
card_pill = now.strftime("%B %d").replace(" 0", " ")

# Header date-chip uses the REPORT date (yesterday's business day), not today
report_date_str = latest.get("meta", {}).get("report_date")
if report_date_str:
    rpt_dt = datetime.strptime(report_date_str, "%Y-%m-%d")
    header_date_chip = rpt_dt.strftime("%A, %B %d &nbsp;%Y").replace(" 0", " ")
else:
    header_date_chip = now.strftime("%A, %B %d &nbsp;%Y").replace(" 0", " ")

labor_pct = f"{latest['labor']['pct']:.1f}%" if latest['labor'].get('pct') is not None else "—"
sched_hrs_today = f"{sched['today']['scheduled_hours']:.1f}" if sched else "—"
sales_net = f"${latest['sales']['net']:,.0f}"
sales_ly = f"${latest['sales']['ly']:,.0f}"
sales_forecast = f"${latest['sales']['forecast']:,.0f}"
per_guest = f"${latest['sales']['per_guest']:.2f}"
compliance_pct = f"{cm['overall_pct']}%"
compliance_sub = f"{len([l for l in cm['lists'] if l['pct']==100])}/{len(cm['lists'])} lists at 100%"

if ss:
    ss_quarter = f"{ss['averages']['quarter']['score']:.0f}%"
    ss_latest = f"{ss['latest']['score']:.0f}%"
    ss_date = datetime.strptime(ss['latest']['date'], "%Y-%m-%d").strftime("%b %d").replace(" 0", " ")
    ss_service = f"{ss['latest']['service']}%"
    ss_quality = f"{ss['latest']['quality']}%"
    ss_cleanliness = f"{ss['latest']['cleanliness']}%"
    ss_csat = f"{ss['latest']['customer_satisfaction']}%"

# ── schedule classification ─────────────────────────────────────────────
def end_hour(t):
    dt = datetime.strptime(t, "%I:%M %p")
    return dt.hour + dt.minute / 60.0

def sched_hrs_of(shift):
    s = datetime.strptime(shift['start'], "%I:%M %p")
    e = datetime.strptime(shift['end'], "%I:%M %p")
    hrs = (e - s).total_seconds() / 3600.0
    return round(hrs * 2) / 2.0

def role_short(role):
    if "General Manager" in role: return "GM"
    if "Shift Lead" in role:      return "Shift Lead"
    return "Crew"

def build_shift_rows(shifts):
    rows = []
    total = 0.0
    for sh in shifts:
        hrs = sched_hrs_of(sh)
        total += hrs
        rows.append(
            f'              <tr>\n'
            f'                <td><div class="emp-name">{sh["name"]}</div><div class="emp-role">{role_short(sh["role"])}</div></td>\n'
            f'                <td>{hrs:.1f}</td><td class="pending">In progress</td><td class="pending">—</td>\n'
            f'              </tr>'
        )
    return "\n".join(rows), total

am_shifts, pm_shifts = [], []
if sched:
    for sh in sched['today']['shifts']:
        (am_shifts if end_hour(sh['end']) <= 17.0 else pm_shifts).append(sh)
am_body, am_total = build_shift_rows(am_shifts)
pm_body, pm_total = build_shift_rows(pm_shifts)

# ── load dashboard and wire ─────────────────────────────────────────────
html = DASH.read_text(encoding="utf-8")
applied = []
missed = []

def rep(pattern, replacement, label, count=1, flags=0):
    """Regex-based idempotent replacement. Counts matches, fails loudly on zero."""
    global html
    new_html, n = re.subn(pattern, replacement, html, count=count, flags=flags)
    if n == 0:
        missed.append(label)
        print(f"  [MISS] {label}")
        return False
    html = new_html
    applied.append(label)
    return True

DOTALL = re.DOTALL

# ── Header (date-chip, last-updated, greeting) ──────────────────────────
rep(r'(<div class="date-chip">)[^<]*(</div>)',
    rf'\g<1>{header_date_chip}\g<2>',
    "date-chip")

rep(r'(<div class="last-updated">Last updated <b>)[^<]*(</b>)',
    rf'\g<1>{time_str}\g<2>',
    "last-updated time")

hr = now.hour
greeting = "Good morning" if hr < 12 else "Good afternoon" if hr < 17 else "Good evening"
rep(r'(<div class="page-title">)[^<]*(</div>)',
    rf'\g<1>{greeting}, Bobby.\g<2>',
    "page-title greeting")

# ── Labor controllable (ctrl-card labor) ────────────────────────────────
# Labor % — first ctrl-value inside ctrl-card labor
rep(r'(<div class="ctrl-card labor">.*?<div class="ctrl-value">)[^<]*(</div>)',
    rf'\g<1>{labor_pct}\g<2>',
    "Labor %",
    flags=DOTALL)

# Sched Hrs today — the ctrl-stat-val preceding "Sched Hrs" label
rep(r'(<div class="ctrl-stat-val">)[^<]*(</div>\s*<div class="ctrl-stat-lbl">Sched Hrs</div>)',
    rf'\g<1>{sched_hrs_today}\g<2>',
    "Sched Hrs today",
    flags=DOTALL)

# ── Food Cost top-3 variance items (if cogs data) ──────────────────────
if cogs and cogs.get("items"):
    def trim(n, maxlen=28):
        return n if len(n) <= maxlen else n[:maxlen-1].rstrip(",") + "…"
    top3 = sorted(cogs["items"], key=lambda x: x["over_dollars"], reverse=True)[:3]
    var_new_rows = "\n".join(
        f'          <div class="var-item">\n'
        f'            <span class="var-rank">{i+1}</span>\n'
        f'            <span class="var-name">{trim(it["name"])}</span>\n'
        f'            <span class="var-pct">+${it["over_dollars"]}</span>\n'
        f'          </div>'
        for i, it in enumerate(top3)
    )
    # Replace the whole var-list block (first one — food-cost card)
    rep(r'(<div class="var-list">)(.*?)(</div>\s*<div class="ctrl-divider">)',
        rf'\g<1>\n{var_new_rows}\n        \g<3>',
        "Food Cost top 3 variance items",
        flags=DOTALL)

    week_lbl = f'{cogs["meta"]["week_start"][5:].replace("-","/")}–{cogs["meta"]["week_end"][5:].replace("-","/")}'
    rep(r'(<div class="ctrl-section-lbl"><span>Top 3 Variance Items</span><span class="goal-tag">)[^<]*(</span></div>)',
        rf'\g<1>{week_lbl}\g<2>',
        "variance week label")

# ── KPI row: Daily Sales / Sales per Guest / Compliance ────────────────
# Daily Sales value (kpi-val preceding "Daily Sales" label)
rep(r'(<div class="kpi-val">)[^<]*(</div>\s*<div class="kpi-lbl">Daily Sales</div>)',
    rf'\g<1>{sales_net}\g<2>',
    "Daily Sales value",
    flags=DOTALL)

# Daily Sales sub (kpi-sub after "Daily Sales" label)
rep(r'(<div class="kpi-lbl">Daily Sales</div>\s*<div class="kpi-sub">)[^<]*(</div>)',
    rf'\g<1>LY {sales_ly} &nbsp;&middot;&nbsp; Fcst {sales_forecast}\g<2>',
    "Daily Sales sub",
    flags=DOTALL)

# Sales / Guest value — the kpi-val before "Sales / Guest" label
rep(r'(<div class="kpi-val">)[^<]*(</div>\s*<div class="kpi-lbl">Sales / Guest</div>)',
    rf'\g<1>{per_guest}\g<2>',
    "Sales / Guest value",
    flags=DOTALL)

# Sales / Guest sub
rep(r'(<div class="kpi-lbl">Sales / Guest</div>\s*<div class="kpi-sub">)[^<]*(</div>)',
    rf'\g<1>Week avg ${latest["sales"]["per_guest_week"]:.2f}\g<2>',
    "Sales / Guest sub",
    flags=DOTALL)

# Compliance value
rep(r'(<div class="kpi-val">)[^<]*(</div>\s*<div class="kpi-lbl">Compliance</div>)',
    rf'\g<1>{compliance_pct}\g<2>',
    "Compliance value",
    flags=DOTALL)

# Compliance sub
rep(r'(<div class="kpi-lbl">Compliance</div>\s*<div class="kpi-sub">)[^<]*(</div>)',
    rf'\g<1>{compliance_sub}\g<2>',
    "Compliance sub",
    flags=DOTALL)

# Optional label swap: "Avg Ticket" → "Sales / Guest" (first run only)
rep(r'(<div class="kpi-lbl">)Avg Ticket(</div>)',
    r'\g<1>Sales / Guest\g<2>',
    "Avg Ticket label swap (first run only)",
    count=0)  # unlimited — no-op after first wire

# ── Schedule card pill (in Today's Schedule header) ────────────────────
rep(r'(<div class="card-title">Today\'s Schedule</div>.*?<div class="pill pill-white">)[^<]*(</div>)',
    rf'\g<1>{card_pill}\g<2>',
    "schedule card pill",
    flags=DOTALL)

# ── Schedule AM / PM tables (structural regex replace of whole block) ──
if sched:
    am_section = (
        '        <!-- AM Shift -->\n'
        '        <div id="shift-am">\n'
        '          <table class="sched-table">\n'
        '            <thead>\n'
        '              <tr>\n'
        '                <th>Employee</th>\n'
        '                <th>Sched Hrs</th>\n'
        '                <th>Actual Hrs</th>\n'
        '                <th>Variance</th>\n'
        '              </tr>\n'
        '            </thead>\n'
        '            <tbody>\n'
        f'{am_body}\n'
        '            </tbody>\n'
        '            <tfoot>\n'
        '              <tr class="total-row">\n'
        '                <td>AM Total</td>\n'
        f'                <td>{am_total:.1f} hrs</td>\n'
        '                <td class="pending">Pending</td>\n'
        '                <td class="pending">—</td>\n'
        '              </tr>\n'
        '            </tfoot>\n'
        '          </table>\n'
        '        </div>'
    )
    pm_section = (
        '        <!-- PM Shift -->\n'
        '        <div id="shift-pm" style="display:none">\n'
        '          <table class="sched-table">\n'
        '            <thead>\n'
        '              <tr>\n'
        '                <th>Employee</th>\n'
        '                <th>Sched Hrs</th>\n'
        '                <th>Actual Hrs</th>\n'
        '                <th>Variance</th>\n'
        '              </tr>\n'
        '            </thead>\n'
        '            <tbody>\n'
        f'{pm_body}\n'
        '            </tbody>\n'
        '            <tfoot>\n'
        '              <tr class="total-row">\n'
        '                <td>PM Total</td>\n'
        f'                <td>{pm_total:.1f} hrs</td>\n'
        '                <td class="pending">Pending close</td>\n'
        '                <td class="pending">—</td>\n'
        '              </tr>\n'
        '            </tfoot>\n'
        '          </table>'
    )

    # AM Shift block: from marker comment through its closing </div> before PM marker
    new_am, n_am = re.subn(
        r'        <!-- AM Shift -->.*?</div>(?=\s*\n\s*<!-- PM Shift -->)',
        lambda m: am_section,
        html, count=1, flags=DOTALL,
    )
    if n_am:
        html = new_am
        applied.append("AM Shift table body")
    else:
        missed.append("AM Shift table body")

    # PM Shift block: from marker through its closing </table> before Hourly labor alerts
    new_pm, n_pm = re.subn(
        r'        <!-- PM Shift -->.*?</table>(?=\s*\n\s*</div>\s*\n\s*<!-- Hourly labor alerts -->)',
        lambda m: pm_section,
        html, count=1, flags=DOTALL,
    )
    if n_pm:
        html = new_pm
        applied.append("PM Shift table body")
    else:
        missed.append("PM Shift table body")

# ── Secret Shop card (if ss data) ──────────────────────────────────────
if ss:
    rep(r'(<div class="ss-score">)[^<]*(</div>)',
        rf'\g<1>{ss_quarter}\g<2>',
        "SS score (quarter avg)")

    rep(r'(<div class="ss-goal">).*?(</div>)',
        rf'\g<1>Latest: <b>{ss_latest}</b>\g<2>',
        "SS goal → latest",
        flags=DOTALL)

    rep(r'(<div class="ss-meta">).*?(</div>)',
        rf'\g<1>Last<b>{ss_date}</b>\g<2>',
        "SS last date",
        flags=DOTALL)

    # SS KPI bars — rewrite the full ss-kpi-list block
    def ss_kpi_html(name, pct_str):
        pct_num = int(pct_str.rstrip('%'))
        under = ' under' if pct_num < 88 else ''
        return (f'          <div class="ss-kpi">\n'
                f'            <span class="ss-kpi-name">{name}</span>\n'
                f'            <span class="ss-kpi-bar-bg"><span class="ss-kpi-bar-fill{under}" style="width:{pct_num}%"></span></span>\n'
                f'            <span class="ss-kpi-pct">{pct_str}</span>\n'
                f'          </div>')
    new_kpi_block = "\n".join([
        ss_kpi_html("Service", ss_service),
        ss_kpi_html("Quality", ss_quality),
        ss_kpi_html("Cleanliness", ss_cleanliness),
        ss_kpi_html("Customer Satisfaction", ss_csat),
    ])
    rep(r'(<div class="ss-kpi-list">)(.*?)(</div>\s*</div>\s*<!-- Steritech)',
        rf'\g<1>\n{new_kpi_block}\n        \g<3>',
        "SS KPI list",
        flags=DOTALL)

# ── Footer timestamp ───────────────────────────────────────────────────
rep(r'(<span>CrunchTime Net Chef &nbsp;&middot;&nbsp; Updated <span>)[^<]*(</span> &nbsp;&middot;&nbsp; )[^<]*(</span>)',
    rf'\g<1>{time_str}\g<2>{date_display}\g<3>',
    "footer timestamp")

# ── write ──────────────────────────────────────────────────────────────
DASH.write_text(html, encoding="utf-8")

print(f"\nWired {len(applied)} sections, {len(missed)} missed.")
for r in applied:
    print(f"  ✓ {r}")
for r in missed:
    print(f"  ✗ MISS: {r}")

# ── critical-miss gate: write to debug-log so next session auto-fixes ──
critical_missed = [m for m in missed if m in CRITICAL_LABELS]
if critical_missed:
    log = ROOT / "data" / "debug-log.txt"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as f:
        f.write(f"\n[{now.strftime('%Y-%m-%d %H:%M:%S')}] wire_dashboard.py critical-field miss:\n")
        for m in critical_missed:
            f.write(f"  - {m}\n")
        f.write(f"  Fix: inspect dashboard.html structure; a class name or label may have changed. Re-run scraper/wire_dashboard.py after fix.\n")
    print(f"\n⚠️  {len(critical_missed)} critical fields missed — logged to data/debug-log.txt")
    sys.exit(1)

if sched:
    print(f"\nToday: {len(am_shifts)} AM / {len(pm_shifts)} PM shifts, {sched['today']['scheduled_hours']:.1f} hrs scheduled")
