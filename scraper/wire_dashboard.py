"""
Wire live data into dashboard_bobby_2026-04-22.html.

Reads JSON data from data/ and performs targeted string replacements.
Preserves design exactly. No HTML regeneration.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "dashboard.html"
STORE_ID = "2065"
RAW = ROOT / "data" / "raw"

def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))

def load_latest(source, report):
    """
    Resolve newest file at data/raw/{source}/{STORE_ID}/<date>/{report}.
    Falls back to legacy top-level paths. Returns (dict, path) or (None, None).
    """
    base = RAW / source / STORE_ID
    if base.exists():
        dated = sorted([d for d in base.iterdir() if d.is_dir()], reverse=True)
        for d in dated:
            cand = d / report
            if cand.exists():
                return json.loads(cand.read_text(encoding="utf-8")), cand
    return None, None

# Primary reads from data/raw/... with legacy fallback
latest, _ = load_latest("crunchtime", "perf_metrics.json")
if latest is None:
    latest = load("data/latest.json")

cm, _ = load_latest("compliancemate", "lists.json")
if cm is None:
    cm = load("data/compliancemate.json")

ss, _ = load_latest("marketforce", "shops.json")
if ss is None:
    ss = load("data/secret_shops.json")

cogs, _ = load_latest("crunchtime", "cogs_variance.json")
if cogs is None:
    try:
        cogs = load("data/cogs_variance.json")
    except FileNotFoundError:
        cogs = None

# schedule: new raw path first, then legacy parbrink path
sched, sched_path = load_latest("parbrink", "weekly_schedule.json")
if sched is None:
    legacy = sorted((ROOT / "data" / "parbrink").glob("*/weekly_schedule_2065.json"))
    if legacy:
        sched_path = legacy[-1]
        sched = json.loads(sched_path.read_text(encoding="utf-8"))

# ── derived values ────────────────────────────────────────────────
now = datetime.now()
time_str = now.strftime("%-I:%M %p") if sys.platform != "win32" else now.strftime("%#I:%M %p")
date_display = now.strftime("%B %d %Y").replace(" 0", " ")  # "April 23 2026"
date_pill = now.strftime("%b %d").replace(" 0", " ")        # "Apr 23"
# Card pill format matches original "April 21" (month name + day)
card_pill = now.strftime("%B %d").replace(" 0", " ")

labor_pct = f"{latest['labor']['pct']:.1f}%"         # "24.9%"
sched_hrs_today = f"{sched['today']['scheduled_hours']:.1f}" if sched else "—"
sales_net = f"${latest['sales']['net']:,.0f}"        # "$3,566"
sales_ly  = f"${latest['sales']['ly']:,.0f}"
sales_forecast = f"${latest['sales']['forecast']:,.0f}"
per_guest = f"${latest['sales']['per_guest']:.2f}"
compliance_pct = f"{cm['overall_pct']}%"             # "70%"
ss_quarter = f"{ss['averages']['quarter']['score']:.0f}%"  # "86%"
ss_latest = f"{ss['latest']['score']:.0f}%"
ss_date = datetime.strptime(ss['latest']['date'], "%Y-%m-%d").strftime("%b %d").replace(" 0", " ")
ss_service = f"{ss['latest']['service']}%"
ss_quality = f"{ss['latest']['quality']}%"
ss_cleanliness = f"{ss['latest']['cleanliness']}%"
ss_csat = f"{ss['latest']['customer_satisfaction']}%"

# ── schedule classification: AM if shift ends ≤ 5 PM ──────────────
def end_hour(t):
    # "09:00 PM" → 21
    dt = datetime.strptime(t, "%I:%M %p")
    return dt.hour + dt.minute / 60.0

def sched_hrs_of(shift):
    s = datetime.strptime(shift['start'], "%I:%M %p")
    e = datetime.strptime(shift['end'],   "%I:%M %p")
    hrs = (e - s).total_seconds() / 3600.0
    return round(hrs * 2) / 2.0  # nearest 0.5

am_shifts, pm_shifts = [], []
if sched:
    for sh in sched['today']['shifts']:
        (am_shifts if end_hour(sh['end']) <= 17.0 else pm_shifts).append(sh)

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

am_body, am_total = build_shift_rows(am_shifts)
pm_body, pm_total = build_shift_rows(pm_shifts)

# ── read dashboard ─────────────────────────────────────────────────
html = DASH.read_text(encoding="utf-8")
replacements = []

def sub(old, new, label):
    global html
    if old not in html:
        print(f"  [MISS] {label}")
        return
    count = html.count(old)
    if count > 1:
        print(f"  [AMBIG x{count}] {label} — using replace once at first occurrence")
        idx = html.index(old)
        html = html[:idx] + new + html[idx+len(old):]
    else:
        html = html.replace(old, new)
    replacements.append(label)

# header timestamp
sub("Last updated <b>8:12 AM</b>", f"Last updated <b>{time_str}</b>", "header last-updated")

# Food Cost top-3 variance items (ranked by $ over theoretical)
if cogs and cogs.get("items"):
    top3 = sorted(cogs["items"], key=lambda x: x["over_dollars"], reverse=True)[:3]
    # trim long names for the card
    def trim(n, maxlen=28):
        return n if len(n) <= maxlen else n[:maxlen-1].rstrip(",") + "…"
    var_old = """        <div class="var-list">
          <div class="var-item">
            <span class="var-rank">1</span>
            <span class="var-name">Fresh Ground Beef</span>
            <span class="var-pct">+$187</span>
          </div>
          <div class="var-item">
            <span class="var-rank">2</span>
            <span class="var-name">French Fries</span>
            <span class="var-pct">+$94</span>
          </div>
          <div class="var-item">
            <span class="var-rank">3</span>
            <span class="var-name">American Cheese</span>
            <span class="var-pct">+$52</span>
          </div>
        </div>"""
    var_new_rows = "\n".join(
        f'          <div class="var-item">\n'
        f'            <span class="var-rank">{i+1}</span>\n'
        f'            <span class="var-name">{trim(it["name"])}</span>\n'
        f'            <span class="var-pct">+${it["over_dollars"]}</span>\n'
        f'          </div>'
        for i, it in enumerate(top3)
    )
    var_new = f'        <div class="var-list">\n{var_new_rows}\n        </div>'
    sub(var_old, var_new, "Food Cost top 3 variance items ($ over theoretical)")

    # also swap "Today" tag to the CrunchTime week range
    week_lbl = f'{cogs["meta"]["week_start"][5:].replace("-","/")}–{cogs["meta"]["week_end"][5:].replace("-","/")}'
    sub('<div class="ctrl-section-lbl"><span>Top 3 Variance Items</span><span class="goal-tag">Today</span></div>',
        f'<div class="ctrl-section-lbl"><span>Top 3 Variance Items</span><span class="goal-tag">{week_lbl}</span></div>',
        "variance week label")

# Labor controllable
sub('<div class="ctrl-value">19.8%</div>', f'<div class="ctrl-value">{labor_pct}</div>', "Labor %")
sub('<div class="ctrl-stat-val">44.0</div>', f'<div class="ctrl-stat-val">{sched_hrs_today}</div>', "Sched Hrs today")

# KPI row
sub('<div class="kpi-val">$8,452</div>', f'<div class="kpi-val">{sales_net}</div>', "Daily Sales")
sub('<div class="kpi-sub">Goal $8,200 &nbsp;&middot;&nbsp; +$252 ahead</div>',
    f'<div class="kpi-sub">LY {sales_ly} &nbsp;&middot;&nbsp; Fcst {sales_forecast}</div>', "Sales sub")
sub('<div class="kpi-val">$27.10</div>', f'<div class="kpi-val">{per_guest}</div>', "Avg Ticket → Per Guest")
sub('<div class="kpi-lbl">Avg Ticket</div>', '<div class="kpi-lbl">Sales / Guest</div>', "Avg Ticket label")
sub('<div class="kpi-sub">Goal $26.50 &nbsp;&middot;&nbsp; On track</div>',
    f'<div class="kpi-sub">Week avg ${latest["sales"]["per_guest_week"]:.2f}</div>', "Per Guest sub")
sub('<div class="kpi-val">96%</div>', f'<div class="kpi-val">{compliance_pct}</div>', "Compliance %")
sub('<div class="kpi-sub">Goal 90% &nbsp;&middot;&nbsp; Passed</div>',
    f'<div class="kpi-sub">{len([l for l in cm["lists"] if l["pct"]==100])}/{len(cm["lists"])} lists at 100%</div>',
    "Compliance sub")

# Schedule card pill + AM/PM tables
sub('<div class="pill pill-white">April 21</div>', f'<div class="pill pill-white">{card_pill}</div>', "schedule card pill")

# AM shift body
am_old_start = '        <!-- AM Shift -->'
am_section = f"""        <!-- AM Shift -->
        <div id="shift-am">
          <table class="sched-table">
            <thead>
              <tr>
                <th>Employee</th>
                <th>Sched Hrs</th>
                <th>Actual Hrs</th>
                <th>Variance</th>
              </tr>
            </thead>
            <tbody>
{am_body}
            </tbody>
            <tfoot>
              <tr class="total-row">
                <td>AM Total</td>
                <td>{am_total:.1f} hrs</td>
                <td class="pending">Pending</td>
                <td class="pending">—</td>
              </tr>
            </tfoot>
          </table>
        </div>"""

# capture existing AM block (from "<!-- AM Shift -->" to its closing </div> before "<!-- PM Shift -->")
am_marker_start = html.index('<!-- AM Shift -->')
pm_marker = html.index('<!-- PM Shift -->')
# back up to the indent before PM marker
cut_end = html.rfind('</div>', am_marker_start, pm_marker)
cut_end = html.rfind('\n', am_marker_start, cut_end) + 1
# find the line start of AM marker
cut_start = html.rfind('\n', 0, am_marker_start) + 1
# build indent-preserving replacement
html = html[:cut_start] + am_section + "\n\n" + html[cut_end:]
replacements.append("AM Shift table body")

# PM shift body — same approach
pm_marker_start = html.index('<!-- PM Shift -->')
# find end: next "</div>" that precedes "</div><!-- /ops-row -->" area. PM block ends before closing of schedule card.
# Easier: PM block ends at "</div>\n      </div><!-- /..." — find "      <!-- Hourly labor alerts -->"
hourly_marker = html.index('<!-- Hourly labor alerts -->')
cut_end2 = html.rfind('</div>', pm_marker_start, hourly_marker)
cut_end2 = html.rfind('\n', pm_marker_start, cut_end2) + 1
cut_start2 = html.rfind('\n', 0, pm_marker_start) + 1

pm_section = f"""        <!-- PM Shift -->
        <div id="shift-pm" style="display:none">
          <table class="sched-table">
            <thead>
              <tr>
                <th>Employee</th>
                <th>Sched Hrs</th>
                <th>Actual Hrs</th>
                <th>Variance</th>
              </tr>
            </thead>
            <tbody>
{pm_body}
            </tbody>
            <tfoot>
              <tr class="total-row">
                <td>PM Total</td>
                <td>{pm_total:.1f} hrs</td>
                <td class="pending">Pending close</td>
                <td class="pending">—</td>
              </tr>
            </tfoot>
          </table>
"""
html = html[:cut_start2] + pm_section + html[cut_end2:]
replacements.append("PM Shift table body")

# Secret Shop
sub('<div class="ss-score">84%</div>', f'<div class="ss-score">{ss_quarter}</div>', "SS score (quarter avg)")
sub('<div class="ss-goal">Goal: <b>88%</b></div>', f'<div class="ss-goal">Latest: <b>{ss_latest}</b></div>', "SS goal → latest")
sub('<div class="ss-meta">Last<b>Apr 18</b></div>', f'<div class="ss-meta">Last<b>{ss_date}</b></div>', "SS last date")

# SS KPIs → map to live service/quality/cleanliness/customer satisfaction (latest shop)
# Replace the 6 mock kpis with 4 real ones
ss_kpi_old_start = html.index('<div class="ss-kpi-list">')
ss_kpi_old_end = html.index('</div>', ss_kpi_old_start)
# actually need the closing of ss-kpi-list, find next </div> after last ss-kpi
# Simpler: find "Speed of Service" block's closing
if 'Speed of Service' in html:
    after_speed = html.index('</div>\n        </div>', html.index('Speed of Service'))
    ss_list_close = after_speed + len('</div>\n        </div>')
elif 'Customer Satisfaction' in html:
    # already-wired state — find end of last ss-kpi before closing </div>
    csat_idx = html.index('Customer Satisfaction')
    after_csat = html.index('</div>\n        </div>', csat_idx)
    ss_list_close = after_csat + len('</div>\n        </div>')
else:
    ss_list_close = None
ss_list_open_end = html.index('\n', ss_kpi_old_start) + 1

def ss_kpi_html(name, pct_str):
    pct_num = int(pct_str.rstrip('%'))
    under = ' under' if pct_num < 88 else ''
    return (f'          <div class="ss-kpi">\n'
            f'            <span class="ss-kpi-name">{name}</span>\n'
            f'            <span class="ss-kpi-bar-bg"><span class="ss-kpi-bar-fill{under}" style="width:{pct_num}%"></span></span>\n'
            f'            <span class="ss-kpi-pct">{pct_str}</span>\n'
            f'          </div>\n')

if ss_list_close is not None:
    new_kpi_block = (ss_kpi_html("Service", ss_service)
                     + ss_kpi_html("Quality", ss_quality)
                     + ss_kpi_html("Cleanliness", ss_cleanliness)
                     + ss_kpi_html("Customer Satisfaction", ss_csat)
                     + '        </div>')
    html = html[:ss_list_open_end] + new_kpi_block + html[ss_list_close:]
    replacements.append("SS KPI list (live service/quality/cleanliness/csat)")

# Footer
sub('<span>CrunchTime Net Chef &nbsp;&middot;&nbsp; Updated <span>8:12 AM</span> &nbsp;&middot;&nbsp; April 21 2026</span>',
    f'<span>CrunchTime Net Chef &nbsp;&middot;&nbsp; Updated <span>{time_str}</span> &nbsp;&middot;&nbsp; {date_display}</span>',
    "footer timestamp")

# Good morning → Good {morning|afternoon|evening}
hr = now.hour
greeting = "Good morning" if hr < 12 else "Good afternoon" if hr < 17 else "Good evening"
sub('<div class="page-title">Good morning, Bobby.</div>',
    f'<div class="page-title">{greeting}, Bobby.</div>', "greeting")

# ── write ─────────────────────────────────────────────────────────
DASH.write_text(html, encoding="utf-8")
print(f"\nWired {len(replacements)} sections into {DASH.name}")
for r in replacements:
    print(f"  ✓ {r}")
print(f"\nToday: {len(am_shifts)} AM / {len(pm_shifts)} PM shifts, {sched['today']['scheduled_hours']:.1f} hrs scheduled")
