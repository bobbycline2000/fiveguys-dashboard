"""Short daily brief (Tue-Sun). Monday keeps the full long brief.

Bobby, 2026-11-21: "I need email brief short and sweet except for on Mondays...
less info but more pertinent info. List of employees working, sales and labor,
deposits, count sheets safe, shop averages, shop focus, pillars, training new
hires, sales calendar, Steritech is a big one... my 20 point checklist."

Every section reads a data file the daily CI run already produces. A section
whose data is missing or stale says so in one line instead of disappearing, so
a broken feed is visible.
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
SITE = "https://bobbycline2000.github.io/fiveguys-dashboard"

# Steritech Morning Manager Walk (Steritech-Morning-Manager-Walk.docx), all 21 items.
STERITECH_WALK = [
    "Salad station: no expired product",
    "Milkshake station: no expired product",
    "Walk-in: no expired product",
    "Milkshake machine + cabinet fully wiped down",
    "No milkshake splatter on walls / baseboards",
    "Every trash can cleaned inside and out",
    "Stainless clean: fryers, grill, bread cart, salad + fry station, expo table, hot shelf",
    "Hood, walls behind grill/fryers, and the backs of them clean",
    "Drain under the hot table clean",
    "Drain under the wash sink clean",
    "Mop sink clean",
    "Dishes staggered, no wet stacking",
    "Clean dishes",
    "Fry scoops + skimmer clean and in good repair",
    "Walk-in floor + corners clean",
    "No condensation leaking from walk-in pipe by the fan",
    "Bug guard by back door clean",
    "Dumpster doors closed, no trash around dumpster",
    "Spatulas, patty press, fry baskets checked",
    "ALL BLADES clean + in repair: knives, tomato slicers, potato block",
    "All walls + floors clean (white walls too)",
]


def _load(name: str):
    try:
        return json.loads((DATA / name).read_text(encoding="utf-8"))
    except Exception:
        return None


def _money(v) -> str:
    return f"${v:,.0f}" if isinstance(v, (int, float)) else "—"


def _hhmm(t: str) -> str:
    try:
        return datetime.strptime(t, "%H:%M").strftime("%I:%M").lstrip("0")
    except Exception:
        return t


def _section_yesterday(today: date) -> list[str]:
    y = today - timedelta(days=1)
    out = [f"## 📊 Yesterday ({y.strftime('%a %m/%d')})", ""]
    dn = _load("daily_numbers.json") or {}
    row = next((r for r in dn.get("rows", []) if r.get("date") == y.isoformat() and not r.get("empty")), None)
    if row and row.get("net_sales") is None:
        # Partial row (cash posted, DSR not yet): never print "None%" (audit 2026-11-22).
        os_ = row.get("cash_os")
        os_txt = "" if os_ is None else (" Cash O/S so far: EVEN." if abs(os_) < 1 else f" Cash O/S so far: 🔴 {_money(abs(os_))} OFF.")
        out.append("_Sales/labor for yesterday not posted yet. Check CrunchTime before the lunch rush._" + os_txt)
    elif row:
        lab = row.get("labor_pct")
        lab_flag = "🟢" if isinstance(lab, (int, float)) and lab <= 20 else "🔴"
        os_ = row.get("cash_os")
        os_txt = "EVEN" if not os_ or abs(os_) < 1 else f"🔴 {_money(abs(os_))} OFF"
        out.append(f"**Sales {_money(row.get('net_sales'))}** · **Labor {lab_flag} {lab}%** (goal 20%) · "
                   f"Guests {row.get('guests', '—')} · Cash O/S {os_txt}")
    else:
        out.append("_Sales/labor for yesterday not posted yet._")
    out.append("")

    ar = _load("active_roster.json") or {}
    crew = ar.get("yesterday") if ar.get("yesterday_date") == y.isoformat() else None
    if crew:
        mgr = [c for c in crew if "leader" in c["position"].lower() or "manager" in c["position"].lower()]
        rest = [c for c in crew if c not in mgr]
        fmt = lambda c: f"{c['name']} ({_hhmm(c['shifts'][0].split('-')[0])}–{_hhmm(c['shifts'][-1].split('-')[-1])}, {c['hours']:.1f}h)"
        out.append(f"**Managers:** " + "; ".join(fmt(c) for c in mgr))
        out.append("")
        out.append(f"**Crew:** " + "; ".join(fmt(c) for c in rest))
        out.append("")
        # Punch problems: overlapping punches (double clock-in), >10h days, missing clock-out.
        flags = []
        for c in crew:
            spans = []
            for s in c["shifts"]:
                a, _, b = s.partition("-")
                spans.append((a, b))
            spans.sort()
            for (a1, b1), (a2, b2) in zip(spans, spans[1:]):
                if a2 < b1:
                    flags.append(f"**{c['name']}** double clock-in ({a1}–{b1} and {a2}–{b2}): fix in CrunchTime")
                    break
            if any(b in ("on", "?") for _, b in spans):
                flags.append(f"**{c['name']}** missing clock-out")
            if c["hours"] > 10:
                flags.append(f"**{c['name']}** worked {c['hours']:.1f}h: check breaks / overtime")
        if flags:
            out.append("⚠️ **Fix these punches:** " + " · ".join(flags))
            out.append("")
    else:
        out.append("_Crew punches for yesterday not pulled yet._")
        out.append("")
    return out


def _section_today_schedule(today: date) -> list[str]:
    files = sorted((DATA / "raw" / "parbrink" / "2065").glob("*/weekly_schedule.json"))
    for f in reversed(files):
        try:
            day = json.loads(f.read_text(encoding="utf-8")).get("schedule", {}).get(today.isoformat())
        except Exception:
            day = None
        if day and day.get("shifts"):
            shifts = sorted(day["shifts"], key=lambda s: datetime.strptime(s["start"], "%I:%M %p"))
            lead = [s for s in shifts if "lead" in s["role"].lower() or "manager" in s["role"].lower()]
            crew = [s for s in shifts if s not in lead]
            t_ = lambda x: x.replace(":00", "").replace(" AM", "a").replace(" PM", "p").lstrip("0")
            f_ = lambda s: f"{s['name']} {t_(s['start'])}–{t_(s['end'])}"
            return [f"## 👥 Today's Schedule ({day.get('scheduled_hours', '—')} hrs)", "",
                    "**Leads:** " + "; ".join(f_(s) for s in lead), "",
                    "**Crew:** " + "; ".join(f_(s) for s in crew), ""]
    return ["## 👥 Today's Schedule", "", "_This week's schedule isn't loaded. Check Teamworx._", ""]


def _section_cash(today: date) -> list[str]:
    out = ["## 💰 Deposits & Safe", ""]
    out.append("Banks: **Safe $700 · Drawer 1 $200 · Drawer 2 $200**. Count at open + close, deposit nightly, "
               f"log it on the [Safe & Drawer page]({SITE}/safe_drawer.html), enter it in CrunchTime.")
    log = _load("safe_drawer_log.json") or []
    y = (today - timedelta(days=1)).isoformat()
    ent = next((e for e in reversed(log) if e.get("date") == y), None)
    if ent:
        safe = ent.get("safe_close") or ent.get("safe_open")
        out.append(f"- Yesterday's counts logged by **{ent.get('mgr', '?')}**. Safe {_money(safe)}"
                   + ("" if safe in (700, None) else " 🔴 (should be $700)")
                   + (f". Note: {ent['notes']}" if ent.get("notes") else ""))
    else:
        out.append(f"- 🔴 **No counts logged for {y}.** Closing manager: log them today.")
    hist = _load("cash_overshort_history.json") or []
    # Prefer newer full-day recaptures (5 AM capture can predate late deposit
    # entry -- 11/20 read $646.86 over, later $0.00). 2026-11-23 audit.
    _ss = {r.get("business_date"): r for r in (_load("ct_sales_summary_history.json") or [])
           if (r.get("captured_at") or "")[:10] > (r.get("business_date") or "")}
    for h in hist:
        s = _ss.get(h.get("business_date"))
        if s and (s.get("captured_at") or "") > (h.get("captured_at") or "") \
                and s.get("over_short") is not None:
            h["over_short"] = s["over_short"]
    misses = [h for h in hist[-7:] if abs(h.get("over_short") or 0) >= 1]
    if misses:
        out.append("- 🔴 Cash off in the last 7 days: " + ", ".join(
            f"{h['business_date'][5:]} {_money(abs(h['over_short']))} off"
            for h in misses) + ". Recount, find it, log it.")
    out.append("")
    return out


def _section_shops() -> list[str]:
    sp = _load("shop_performance.json") or {}
    out = ["## 🛒 Secret Shops", ""]
    ls = (sp.get("latest_shops") or [None])[0]
    if ls:
        out.append(f"Latest: **{ls['date'][5:]} {ls['meal_period']} — {ls['score']:.0f}%** · "
                   f"Month avg **{sp.get('store_avg_month', '—')}%** ({sp.get('shop_count_month', 0)}) · "
                   f"YTD **{sp.get('store_avg_ytd', '—')}%**")
        out.append("")
    mg = [m for m in sp.get("managers", []) if m.get("ytd_n")]
    if mg:
        out.append("**Managers (month / YTD):** " + " · ".join(
            f"{m['name'].split()[0]} {('%.0f%%' % m['month_avg']) if m.get('month_avg') is not None else '—'} / {m['ytd_avg']:.0f}%"
            for m in sorted(mg, key=lambda m: -(m.get("ytd_avg") or 0))))
        out.append("")
    out.append("**Focus:** 4 of 6 shops are at DINNER. Tickets under 6 minutes. Offer fries, a drink AND a shake to every guest. "
               "Greet at the door, thank them on the way out.")
    out.append("")
    return out


def _section_steritech(today: date) -> list[str]:
    n = len(STERITECH_WALK)
    start = (today.toordinal() * 4) % n
    picks = [STERITECH_WALK[(start + i) % n] for i in range(4)]
    out = ["## 🧼 Steritech: Today's Walk Focus", "",
           "Do the full 21-point **Morning Manager Walk** before doors open. Today, double-check these 4:", ""]
    out += [f"- ☐ {p}" for p in picks]
    out += ["", f"[Full 21-point checklist (print)]({SITE}/Steritech-Morning-Manager-Walk.pdf) · "
                "Lids on mushrooms, onions + lettuce · Bread bags dated in 2 spots · No standing water at close", ""]
    return out


PILLARS = [
    "💰 **COGS:** portion fries + toppings, every employee meal rung in",
    "🔍 **Shops:** greet, upsell, tickets under 6 minutes, meat on early",
    "🧼 **Steritech:** walk signed before doors, cleaning items assigned",
    "⏱️ **Labor:** check hourly, cut on a lull (never the close), 30-minute breaks",
]


def _section_new_hires(today: date) -> list[str]:
    hires = _load("employee_hire_dates.json") or {}
    fgu = _load("fgu_training.json") or {}
    rates = {(l.get("full_name") or l.get("name")): l.get("completion_rate") for l in fgu.get("learners", [])}
    ar = _load("active_roster.json") or {}
    team = {e["name"].split()[0].lower() + " " + e["name"].split()[-1].lower() for e in ar.get("employees", [])}
    try:
        src = (REPO / "scripts" / "build_employee_directory.py").read_text(encoding="utf-8")
        for n in re.findall(r'\("([^"]+)",\s*"[^"]*",\s*"Starting"\)', src):
            team.add(n.split()[0].lower() + " " + n.split()[-1].lower())
    except Exception:
        pass
    rows = []
    for name, d in hires.items():
        if name.startswith("_") or len(name.split()) < 2:
            continue
        if team and (name.split()[0].lower() + " " + name.split()[-1].lower()) not in team:
            continue  # hired on paper but never worked / not on the team
        try:
            hd = date.fromisoformat(d)
        except Exception:
            continue
        age = (today - hd).days
        if age < 0 or age > 45:
            continue
        due = hd + timedelta(days=30)
        first = name.split()[0].lower()
        rate = next((v for k, v in rates.items() if k and k.split()[0].lower() == first), None)
        status = f"FGU {rate}%" if rate is not None else "NOT on our FGU roster yet (get them added)"
        flag = "🔴" if (due - today).days < 0 and (rate or 0) < 100 else ("🟡" if (due - today).days <= 7 else "")
        rows.append(f"- {flag} **{name}**: hired {hd.strftime('%m/%d')}, {status}, training due {due.strftime('%m/%d')}".replace("-  **", "- **"))
    out = ["## 🎓 New Hires: Training", ""]
    out += rows or ["- No one in their first 45 days."]
    out += ["", "_Pair new crew with a strong partner on the board. FGU videos on a tablet during prep._", ""]
    return out


def _section_coming_up(today: date) -> list[str]:
    try:
        txt = (DATA / "brief_coming_up.md").read_text(encoding="utf-8").strip()
    except Exception:
        txt = ""
    return (["## 📅 Coming Up", "", txt, ""] if txt else [])


def _section_action(categorized: dict) -> list[str]:
    items = []
    for em in categorized.get("New Hire / Onboarding", []):
        items.append(f"🚨 **New hire / HR:** {em.get('subject', '')}")
    for label, who in (("Director's Corner", "Brad"), ("District Manager — Jeff Reiss", "Jeff"),
                       ("District Manager", "Andrew"), ("Crystal Hess (DM)", "Crystal")):
        for em in categorized.get(label, []):
            body = re.sub(r"\s+", " ", em.get("body", "")).strip()
            body = re.split(r"(Brad Davis|Jeff Reiss|Andrew Campbell|Crystal Hess) ", body)[0]
            body = re.sub(r"\[(image|cid:)[^\]]*\]", "", body).strip()
            if not body:
                body = "sent as a picture only. Open the email in fg2065 and read it (post KPI rankings in the office)."
            items.append(f"**{who} — {em.get('subject', '')}:** {body[:220]}{'…' if len(body) > 220 else ''}")
    for em in categorized.get("Finance / Deposits", []):
        items.append(f"💵 **Deposits:** {em.get('subject', '')}")
    for em in categorized.get("Secret Shop", []):
        items.append(f"🛒 {em.get('subject', '')}")
    # FoodLogiQ / Steritech land in other categories; managers must see them (audit 2026-11-22).
    for cat, ems in categorized.items():
        if cat.startswith("_"):
            continue
        for em in ems:
            who = (em.get("from") or em.get("sender") or "").lower()
            subj = em.get("subject", "")
            if re.search(r"foodlogiq|steritech", who + " " + subj.lower()):
                inc = re.search(r"#\s?\d{2}-\d{4,6}", em.get("body", "") + " " + subj)
                items.append(f"🧾 **{'FoodLogiQ' if 'foodlogiq' in who + subj.lower() else 'Steritech'}"
                             f"{' ' + inc.group(0).replace(' ', '') if inc else ''}:** {subj[:140]}. "
                             "Log in and answer it today so it doesn't close against us.")
    if not items:
        return []
    return ["## ✅ Action Needed Today", ""] + [f"- {i}" for i in items] + [""]


def build_short_brief(categorized: dict, today: date) -> str:
    L = [f"# Daily Brief — {today.strftime('%A %m/%d')}", "",
         f"Short version. The full brief comes Monday. [Live dashboard]({SITE}/dashboard.html)", "", "---", ""]
    try:
        standing = (DATA / "brief_standing_orders.md").read_text(encoding="utf-8").strip()
    except Exception:
        standing = ""
    for part in (_section_action(categorized), [standing, ""] if standing else [], _section_yesterday(today), _section_today_schedule(today),
                 _section_cash(today), _section_shops(), _section_steritech(today),
                 ["## 🏛️ The Four Pillars", ""] + [f"- {p}" for p in PILLARS] + [""],
                 _section_new_hires(today), _section_coming_up(today)):
        if part:
            L += part + ["---", ""]
    L += ["**Manager on duty (sign):** ____________________   **Crew initials:** [  ] [  ] [  ] [  ] [  ]"]
    return "\n".join(L)
