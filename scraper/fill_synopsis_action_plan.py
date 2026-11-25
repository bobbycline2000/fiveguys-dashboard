#!/usr/bin/env python3
"""
Weekly GM Synopsis ACTION PLAN — fills the "2065 Dixie Hwy" tab of Jeff Reiss's
"Weekly_GM_Synopsis_Action_Plan Copy.xlsx" (bdavis SharePoint) — pure API.

    python scraper/fill_synopsis_action_plan.py                # last completed week, DRY RUN
    python scraper/fill_synopsis_action_plan.py 11/22/2026     # week ending that Sunday, DRY RUN
    python scraper/fill_synopsis_action_plan.py 11/22/2026 --write

Runs every Monday RIGHT AFTER fill_weekly_synopsis.py --write (that script chains
into this one). Bobby, 2026-11-25: "make tab at bottom with 2065 dixie hwy and
execute the plan of action every Monday after synopsis is filled out. Any items
in red need addressed in plan of action."

"RED" = what the FG2065 synopsis column shows red / misses its GOALS column:
  sheet conditional formats  COGS% > 27.5%, SUPPLIES > 1.5%, HOURLY LABOR% > 20%
  GOALS column               Variances < -0.5%, QTD Labor > 22%, QTD COGS > 29%,
                             OT > 0, Labor all-in > 24%, Steritech < 97, Criticals > 0,
                             Cmate < 100%, Short completions > 0, checklists < 100%,
                             Shops < 87%, FGU overdue > 0, CSP > 0
Every red item gets a specific action, owner, due date. Green items are marked
"On Track — maintain".

SAFETY: only the worksheet named exactly "2065 Dixie Hwy" is created/written.
The template tabs ("Weekly Action Plan", "How to Complete") are never touched.
The synopsis workbook is READ ONLY here.

Sources (all already in this repo):
  FG2065 synopsis column        fill_weekly_synopsis.sheet_base / week_column
  top 3 food variances          data/food_cost_plan.json (build_food_cost_plan.py)
  OT by employee                CT /resource/nc/employee/timedetail/summary rows
  secret shop + missed points   latest data/raw/marketforce/2065/*/shops.json +
                                KnowledgeForce assignment view "(0 / N)" questions
  roster count                  scripts/build_employee_directory.py EMPLOYEES
History of each week's plan:    data/synopsis_action_plan_history.json (feeds FOLLOW-UP row)
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import subprocess
import sys
import urllib.parse as up
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scraper"))
import api_enter_tips as T              # noqa: E402
import fill_weekly_synopsis as SYN      # noqa: E402
import update_excel as UX               # noqa: E402

TAB = "2065 Dixie Hwy"                  # the ONLY tab this script may write
PLAN_URL = ("https://estepcompany-my.sharepoint.com/:x:/g/personal/bdavis_estep-co_com/"
            "IQBaA-1aQhsiQ41928aH2BAUASzDyA-VNcbcvgM90G7auyc?e=ySC5YS")
HIST = ROOT / "data" / "synopsis_action_plan_history.json"
GM = "Bobby Cline"
MF = ROOT / "data" / "raw" / "marketforce" / "2065"


def pct(x, d=2):
    return "—" if x in (None, "") else f"{float(x) * 100:.{d}f}%"


# ─── sources ─────────────────────────────────────────────────────────────────
def synopsis_column(H, sun):
    col, n = SYN.week_column(sun)
    if col is None:
        raise SystemExit(f"Week {n} of the month — synopsis has no column for it")
    cur = UX.read_range(H, SYN.sheet_base(H), "A1:G40")["values"]
    ci = ord(col) - 65
    row = {r: cur[r - 1][ci] for r in range(8, 40)}
    goal = {r: cur[r - 1][6] for r in range(8, 40)}
    dm = cur[3][1] or ""
    if row[9] in ("", None):
        raise SystemExit(f"Synopsis column {col} (Week {n}) is empty — fill the synopsis first")
    return row, goal, dm, col, n


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def red_items(v):
    """(row, label, value, target) for every synopsis cell that is red / misses goal."""
    rules = [  # row, label, test, target text, fmt
        (12, "COGS %", lambda x: x > 0.275, "27.5%", pct),
        (13, "Variances", lambda x: x < -0.005, "-0.50% or better", pct),
        (14, "Supplies", lambda x: x > 0.015, "1.5%", pct),
        (16, "QTD Labor", lambda x: x > 0.22, "22%", pct),
        (17, "QTD COGS", lambda x: x > 0.29, "29%", pct),
        (19, "Hourly Labor %", lambda x: x > 0.20, "20%", pct),
        (21, "OT Hours", lambda x: x > 0, "ZERO", lambda x: f"{x:g}"),
        (22, "Labor all in with tax", lambda x: x > 0.24, "24%", pct),
        (26, "Steritech", lambda x: x < 97, "97+", lambda x: f"{x:g}"),
        (27, "Criticals", lambda x: x > 0, "0", lambda x: f"{x:g}"),
        (28, "Cmate completion", lambda x: x < 1, "100%", pct),
        (29, "Short completions", lambda x: x > 0, "ZERO", lambda x: f"{x:g}"),
        (30, "Milkshake pics", lambda x: x < 1, "100%", pct),
        (31, "Midshift Checklist", lambda x: x < 1, "100%", pct),
        (32, "AM / PM Checklist", lambda x: x < 1, "100%", pct),
        (34, "Shops — current week", lambda x: x < 0.87, "87%", pct),
        (35, "Shops QTD", lambda x: x < 0.87, "87%", pct),
        (36, "Shops previous Q", lambda x: x < 0.87, "87%", pct),
        (38, "FGU Overdue Rate", lambda x: x > 0, "0", pct),
        (39, "CSP", lambda x: x > 0, "0", lambda x: f"{x:g}"),
    ]
    out = []
    for r, label, test, tgt, fmt in rules:
        x = num(v.get(r))
        if x is not None and test(x):
            out.append((r, label, fmt(x), tgt))
    return out


def food_cost_items(sun):
    p = ROOT / "data" / "food_cost_plan.json"
    d = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    if d.get("variance_week_end") != sun.isoformat():
        subprocess.run([sys.executable, str(ROOT / "scraper" / "build_food_cost_plan.py")], cwd=ROOT, check=False)
        d = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    if d.get("variance_week_end") != sun.isoformat():
        return []
    return d.get("items", [])[:3]


def ot_by_employee(jar, mon):
    body = {"pagingInfo": {"page": 1, "start": 0, "limit": 3000},
            "extraCriteriaMap": {"includeAltLocations": False, "excludeManagers": False, "summarizeBy": "",
                                 "startDate": f"{SYN.f(mon)} 00:00:00",
                                 "weekEndingDate": f"{SYN.f(mon + dt.timedelta(6))} 00:00:00"}}
    r = requests.post(f"{SYN.NETCHEF}/resource/nc/employee/timedetail/summary",
                      json=body, cookies=jar, headers=T.HDR, timeout=90)
    r.raise_for_status()
    tot = {}
    for x in (r.json().get("contentMap") or {}).get("gridList") or []:
        if (x.get("overtimeHours") or 0) > 0:
            last, _, first = (x.get("employeeName") or "").partition(", ")
            nm = f"{first} {last}".strip()
            tot[nm] = tot.get(nm, 0) + x["overtimeHours"]
    return sorted(tot.items(), key=lambda kv: -kv[1])


def week_shops(mon, sun):
    files = sorted(MF.glob("*/shops.json"))
    if not files:
        return []
    shops = json.loads(files[-1].read_text(encoding="utf-8")).get("shops", [])
    return [s for s in shops if mon.isoformat() <= s.get("date", "") <= sun.isoformat()]


def shop_missed(shop):
    """Questions that lost points — '(0 / 8)' style — from the KF assignment view."""
    try:
        for l in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            if "=" in l and not l.lstrip().startswith("#"):
                k, val = l.split("=", 1)
                os.environ.setdefault(k.strip(), val.strip().strip('"'))
        import scrape_visit_time as V
        s = requests.Session(); s.headers.update({"User-Agent": V.UA})
        if not V.login(s, os.environ.get("KNOWLEDGEFORCE_USERNAME", ""), os.environ.get("KNOWLEDGEFORCE_PASSWORD", "")):
            return [], ""
        ds = json.dumps({"jid": int(shop["job_id"]), "period2": [shop["period2"]]})
        t = s.get(V.BASE + "/reporting/assignment/view?dataset=" + up.quote(ds), timeout=60).text
    except Exception as e:  # shop detail is a nice-to-have; never block the plan
        print(f"[plan] shop detail skipped: {e}")
        return [], ""
    missed, cashier = [], ""
    for b in re.split(r'<div class="question">', t)[1:]:
        q = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", b.split("</div>")[0]))).strip()
        m = re.search(r"\((\d+(?:\.\d+)?) / (\d+(?:\.\d+)?)\)", q)
        if m and float(m.group(1)) < float(m.group(2)):
            missed.append(re.sub(r"^\d+\.\s*", "", q))
        if q.lower().startswith("64. cashier") or q.lower().endswith("cashier:"):
            c = re.search(r'class="comments">(.*?)</div>', b, re.S)
            cashier = html.unescape(re.sub(r"\s+", " ", c.group(1))).strip().strip('"').strip() if c else ""
    return missed, cashier


def roster_count():
    try:
        src = (ROOT / "scripts" / "build_employee_directory.py").read_text(encoding="utf-8")
        m = re.search(r"EMPLOYEES\s*=\s*\[(.*?)\n\]", src, re.DOTALL)
        rows = re.findall(r'\(\s*"([^"]+)"\s*,\s*"[^"]*"\s*,\s*"([^"]+)"\s*\)', m.group(1)) if m else []
        return len(rows), sum(1 for _, st in rows if st.lower().startswith("starting"))
    except Exception:
        return None, 0


# ─── build the plan ──────────────────────────────────────────────────────────
def build(sun, H, jar):
    mon = sun - dt.timedelta(6)
    v, goal, dm, col, n = synopsis_column(H, sun)
    reds = red_items(v)
    red_rows = {r for r, *_ in reds}
    nxt_mon, nxt_sun = sun + dt.timedelta(1), sun + dt.timedelta(7)
    due_wk = SYN.f(nxt_sun)
    due_mid = SYN.f(nxt_mon + dt.timedelta(3))      # Thursday check
    net = num(v[9]) or 0
    status = lambda bad: "Not Started" if bad else "On Track — maintain"
    rows = []

    # COGS
    cogs, var = num(v[12]), num(v[13])
    bad = bool(red_rows & {12, 13, 14, 17})
    rows.append(["COST OF GOODS",
                 f"Actual COGS %: {pct(cogs)}  | Target: 27.5%  | Variance: {pct(var)} (goal -0.50% or better)  | Supplies {pct(v[14])}  | QTD COGS {pct(v[17])}",
                 ("Red: " + ", ".join(f"{l} {x} vs {t}" for r, l, x, t in reds if r in {12, 13, 14, 17}) +
                  ". Work the top 3 variance items below daily; MOD recounts Big Six on Thursday; verify every truck invoice vs received."
                  if bad else "COGS at/under target. Keep daily Big Six counts and portion checks on every shift."),
                 GM, due_wk, status(bad)])
    items = food_cost_items(sun)
    for i in range(3):
        if i < len(items):
            it = items[i]
            rows.append([f"COGS — TOP VARIANCE ITEM #{i + 1}",
                         f"Item: {it['name']}  | Variance: ${it['over_dollars']:,.2f} over ({it['variance_pct']}%)  | Actual ${it['actual']:,.2f} vs theo ${it['theoretical']:,.2f}",
                         " ".join(it.get("actions", [])) + f" Re-check variance on the {SYN.f(nxt_sun)} count.",
                         GM, due_wk, "Not Started"])
        else:
            rows.append([f"COGS — TOP VARIANCE ITEM #{i + 1}", "Item: none over theoretical", "—", GM, due_wk, "On Track — maintain"])

    # LABOR
    lab_all, hr = num(v[22]), num(v[19])
    bad = bool(red_rows & {16, 19, 22})
    gap_dollars = max(0.0, ((lab_all or 0) - 0.24) * net)
    rows.append(["LABOR",
                 f"Actual labor %: all-in {pct(lab_all)} | hourly {pct(hr)} | QTD {pct(v[16])}  | Budget / target: all-in 24%, hourly 19-20%, QTD 22%  | Variance: {pct((lab_all or 0) - 0.24)} (~${gap_dollars:,.0f})",
                 (f"Red: " + ", ".join(f"{l} {x} vs {t}" for r, l, x, t in reds if r in {16, 19, 22}) +
                  f". Cut ~${gap_dollars:,.0f} (~{gap_dollars / 14:.0f} crew hrs at ~$14/hr) from next week's Teamworx schedule against forecast. "
                  "MOD sends early cuts in slow hours (2-4 PM, after 8 PM). GM checks labor vs sales daily in CT."
                  if bad else "Labor on target. Keep schedule built to forecast; cut early on slow shifts."),
                 GM, due_wk, status(bad)])

    # OVERTIME
    ot = ot_by_employee(jar, mon)
    bad = 21 in red_rows
    who = ", ".join(f"{nm} {h:.2f} hrs" for nm, h in ot) or "none"
    rows.append(["OVERTIME",
                 f"Hours / team members affected: {num(v[21]) or 0:g} hrs total — {who}",
                 (f"Schedule {', '.join(nm for nm, _ in ot)} at or under 38 hrs. GM checks Time Detail on Thursday and sends anyone near 40 home early. Target ZERO OT."
                  if bad else "Zero OT. Keep Thursday hours check."),
                 GM, due_mid if bad else due_wk, status(bad)])

    # COMPLIANCE MATE
    bad = bool(red_rows & {26, 27, 28, 29, 30})
    rows.append(["COMPLIANCE MATE",
                 f"Completion / outstanding items: Cmate {pct(v[28], 1)}, short completions {num(v[29]) or 0:g}, milkshake pics {pct(v[30], 0)}, Steritech {v[26] or '—'}, criticals {v[27] if v[27] not in ('', None) else '—'}",
                 ("Red: " + ", ".join(f"{l} {x} vs {t}" for r, l, x, t in reds if r in {26, 27, 28, 29, 30}) +
                  ". MOD closes every CM task before shift end; GM reviews CM each morning."
                  if bad else "All CM tasks complete. GM spot-checks CM each morning."),
                 GM, due_wk, status(bad)])

    # SHOPS
    shops = week_shops(mon, sun)
    bad = bool(red_rows & {34, 35, 36})
    opp, cashier_txt = [], ""
    for s in shops:
        if (s.get("score") or 100) < 100:
            m, c = shop_missed(s)
            opp += m
            if c:
                cashier_txt = f" Cashier: {c}."
    shop_txt = "; ".join(f"{s['date'][5:].replace('-', '/')} {s['meal_period']} {s['score']:g}%" for s in shops) or "no shop this week"
    opp_txt = "; ".join(opp) or "none"
    acts = []
    if opp:
        acts.append(f"Coach every shift on the missed point(s): {opp_txt}.{cashier_txt} MOD covers it in every pre-shift huddle this week.")
    if 34 in red_rows or 35 in red_rows:
        acts.append("Shop score under 87% — full SMART plan per shop (build_shop_action_plan.py).")
    if 36 in red_rows:
        acts.append(f"Previous quarter shops {pct(v[36])} vs 87% — closed quarter; hold QTD above 87% to recover.")
    rows.append(["SHOPPER / SECRET SHOP",
                 f"Latest score: {shop_txt}  | Opportunities: {opp_txt}  | Week {pct(v[34], 0)}, QTD {pct(v[35])}, prev Q {pct(v[36])}",
                 " ".join(acts) or "Shops on target. Keep greeting + upsell focus.",
                 GM, due_wk, status(bad or bool(opp))])

    # AMM
    bad = bool(red_rows & {31, 32})
    rows.append(["AMM CHECKLIST",
                 f"Completion: AM/PM {pct(v[32], 0)}, Midshift {pct(v[31], 0)}  | Open items: {'see red' if bad else 'none'}",
                 ("Red: " + ", ".join(f"{l} {x} vs {t}" for r, l, x, t in reds if r in {31, 32}) +
                  ". Opening manager completes AMM before doors; GM verifies daily." if bad
                  else "AMM complete. Opening manager keeps it done before open."),
                 GM, due_wk, status(bad)])

    # STAFFING
    rc, starting = roster_count() or (None, 0)
    bad = bool(red_rows & {38, 39})
    rows.append(["STAFFING / TEAM READINESS",
                 f"Open positions / attendance concerns: roster {rc if rc is not None else '—'} ({starting} new hires not on the clock yet); FGU overdue {pct(v[38], 0)}; CSP {v[39] if v[39] not in ('', None) else '—'}",
                 ("Red: " + ", ".join(f"{l} {x} vs {t}" for r, l, x, t in reds if r in {38, 39}) +
                  ". Assign overdue FGU modules; follow up each shift until complete." if bad
                  else "Confirm weekend coverage Friday; keep FGU at 0 overdue."),
                 GM, SYN.f(nxt_mon + dt.timedelta(4)), status(bad)])

    # FOLLOW-UP
    hist = json.loads(HIST.read_text(encoding="utf-8")) if HIST.exists() else {}
    prev = hist.get((mon - dt.timedelta(1)).isoformat())
    if prev:
        before = set(prev.get("red", []))
        now = {l for _, l, _, _ in reds}
        fixed = sorted(before - now); still = sorted(before & now); new = sorted(now - before)
        fu = (f"Last week red: {', '.join(sorted(before)) or 'none'}. Fixed: {', '.join(fixed) or 'none'}. "
              f"Still red: {', '.join(still) or 'none'}. New: {', '.join(new) or 'none'}.")
    else:
        fu = "First week of the plan — baseline set."
    rows.append(["FOLLOW-UP / WEEK-END REVIEW", f"Results vs. plan: {fu}",
                 f"Review this plan with {dm or 'the DM'} on the Monday call; carry anything still red into next week with a new owner/date.",
                 GM, SYN.f(nxt_sun + dt.timedelta(1)), "Not Started"])

    header = {"store": "2065 — Dixie Hwy (KY-2065)", "gm": GM, "week_ending": SYN.f(sun), "dm": dm}
    return header, rows, reds, col, n


# ─── write ───────────────────────────────────────────────────────────────────
def plan_base(H):
    import base64
    sid = "u!" + base64.urlsafe_b64encode(PLAN_URL.encode()).decode().rstrip("=")
    r = UX.graph_call("GET", f"{UX.GRAPH}/shares/{sid}/driveItem", H)
    r.raise_for_status()
    it = r.json()
    return f"{UX.GRAPH}/drives/{it['parentReference']['driveId']}/items/{it['id']}/workbook"


def write(H, header, rows):
    base = plan_base(H)
    names = [w["name"] for w in UX.graph_call("GET", base + "/worksheets", H).json()["value"]]
    if TAB not in names:
        r = UX.graph_call("POST", base + "/worksheets/add", H, json={"name": TAB})
        r.raise_for_status()
    ws = f"{base}/worksheets('{up.quote(TAB)}')"
    UX.graph_call("POST", ws + "/range(address='A1:F30')/clear", H, json={"applyTo": "Contents"})
    grid = [["ESTEP & COMPANY", "", "", "FIVE GUYS", "", ""],
            ["", "", "", "", "", ""],
            ["WEEKLY GENERAL MANAGER SYNOPSIS & ACTION PLAN", "", "", "", "", ""],
            ["Restaurant # / Location:", header["store"], "", "General Manager:", header["gm"], ""],
            ["Week Ending:", header["week_ending"], "", "District Manager:", header["dm"], ""],
            ["", "", "", "", "", ""],
            ["FOCUS AREA", "CURRENT RESULT / GAP", "ACTION PLAN & STEPS TO COMPLETE", "OWNER", "DUE DATE", "STATUS / RESULT"]]
    grid += rows
    grid += [["", "", "", "", "", ""],
             ["EXPECTATION: Be specific and measurable. Every gap needs an action, a responsible owner, a due date, and a verification step. Update status throughout the week.", "", "", "", "", ""],
             [f"Auto-filled from the FG2065 Weekly Synopsis + CrunchTime / ComplianceMate / KnowledgeForce on {dt.date.today().strftime('%m/%d/%Y')}.", "", "", "", "", ""]]
    end = len(grid)
    r = UX.graph_call("PATCH", ws + f"/range(address='A1:F{end}')", H,
                      json={"values": [[str(c) for c in row] for row in grid], "numberFormat": [["@"] * 6] * end})
    r.raise_for_status()
    # light formatting — Five Guys red header row, bold labels, wrap, widths
    fmt = lambda a, body: UX.graph_call("PATCH", ws + f"/range(address='{a}')/format{body[0]}", H, json=body[1])
    fmt("A1:F3", ("/font", {"bold": True, "size": 13}))
    fmt("A7:F7", ("/fill", {"color": "#DA291C"})); fmt("A7:F7", ("/font", {"bold": True, "color": "#FFFFFF"}))
    fmt(f"A8:A{7 + len(rows)}", ("/font", {"bold": True}))
    fmt(f"A7:F{7 + len(rows)}", ("", {"wrapText": True, "verticalAlignment": "Top"}))
    for c, w in zip("ABCDEF", (170, 330, 420, 90, 80, 120)):
        fmt(f"{c}:{c}", ("", {"columnWidth": w}))
    for i, row in enumerate(rows, start=8):
        fmt(f"F{i}", ("/fill", {"color": "#F4CCCC" if row[5] == "Not Started" else "#D9EAD3"}))
    return UX.read_range(H, ws, f"A1:F{end}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("week_ending", nargs="?", help="Sunday MM/DD/YYYY (default: last completed)")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    today = dt.date.today()
    sun = (dt.datetime.strptime(a.week_ending, "%m/%d/%Y").date() if a.week_ending
           else today - dt.timedelta(days=today.weekday() + 1))
    if sun.weekday() != 6:
        sys.exit(f"{sun} is not a Sunday")
    jar = T.ensure_session()
    H = {"Authorization": f"Bearer {UX.graph_token()}", "Content-Type": "application/json"}
    header, rows, reds, col, n = build(sun, H, jar)
    print(f"Action plan — week ending {SYN.f(sun)} (synopsis Week {n}, col {col})")
    print("RED:", "; ".join(f"{l} {x} vs {t}" for _, l, x, t in reds) or "none")
    for r in rows:
        print(f"\n[{r[0]}]  {r[5]}  due {r[4]}\n  {r[1]}\n  -> {r[2]}")
    if not a.write:
        print("\nDRY RUN — nothing written. Re-run with --write.")
        return 0
    after = write(H, header, rows)
    hist = json.loads(HIST.read_text(encoding="utf-8")) if HIST.exists() else {}
    hist[sun.isoformat()] = {"red": [l for _, l, _, _ in reds], "rows": rows, "written": dt.datetime.now().isoformat(timespec="minutes")}
    HIST.write_text(json.dumps(hist, indent=1), encoding="utf-8")
    print(f"\nWROTE '{TAB}' ({len(after['values'])} rows). History -> {HIST.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
