"""
Build data/synopsis_2065.json — the FG2065 column of Crystal Hess's weekly
Market Synopsis (new format, template: Synopsis.xlsx from Crystal, 2026-03).

Week convention: last completed Mon–Sun relative to the run date.
Runs Monday morning via .github/workflows/monday_synopsis.yml, after the
daily dashboard run (Brink pickup + food cost plan) and the Monday tips run
(tips snapshot), so every source file below is fresh.

Sources (all already produced by existing pipelines — no live scraping here):
  data/forecast_history.json                       forecast + actual by day (CT forecast, Brink actual)
  data/raw/parbrink/2065/<date>/sales_summary.json net sales, labor cost/hours per day
  data/food_cost_plan.json                         weekly COGS %, goal, top variance items
  data/tips_we_<sunday>_snapshot.json              charged tips + per-employee pool hours (OT calc)
  data/shop_performance.json                       secret shop month avg / latest shops
  data/fgu_training.json                           FGU overdue rate + learner completion
  data/compliance_rollups.json                     ComplianceMate weekly completion %

Fields Crystal fills that have no automated source yet are emitted as null —
synopsis.html renders them as blank manual cells.
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
STORE = "2065"


def load(name):
    p = DATA / name
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def last_completed_week(today: datetime.date) -> tuple[datetime.date, datetime.date]:
    """Most recent fully completed Mon–Sun week."""
    last_sunday = today - datetime.timedelta(days=today.weekday() + 1)
    return last_sunday - datetime.timedelta(days=6), last_sunday


def week_dates(mon: datetime.date) -> list[str]:
    return [(mon + datetime.timedelta(days=i)).isoformat() for i in range(7)]


def rnd(v, n=2):
    return None if v is None else round(v, n)


def main() -> None:
    today = datetime.date.today()
    mon, sun = last_completed_week(today)
    dates = week_dates(mon)
    quarter_start = datetime.date(today.year, 3 * ((today.month - 1) // 3) + 1, 1)

    out = {
        "meta": {
            "store": STORE,
            "week_start": mon.isoformat(),
            "week_end": sun.isoformat(),
            "week_label": f"{mon.month}/{mon.day}-{sun.month}/{sun.day}",
            "month": mon.strftime("%B"),
            "generated": datetime.datetime.now().isoformat(timespec="seconds"),
            "notes": [],
        }
    }
    notes = out["meta"]["notes"]

    # ── SALES: forecast (CT) vs net sales (Brink) ────────────────────────
    hist = load("forecast_history.json") or {}
    fc_days = [hist[d]["forecast"] for d in dates if hist.get(d, {}).get("forecast") is not None]
    forecast = round(sum(fc_days)) if len(fc_days) == 7 else (round(sum(fc_days)) if fc_days else None)
    if 0 < len(fc_days) < 7:
        notes.append(f"forecast covers {len(fc_days)}/7 days")

    net = labor_cost = labor_hours = None
    brink_days = 0
    for d in dates:
        js = load(f"raw/parbrink/{STORE}/{d}/sales_summary.json")
        if not js:
            continue
        brink_days += 1
        net = (net or 0) + (js.get("net_sales") or 0)
        labor_cost = (labor_cost or 0) + (js.get("labor_cost") or 0)
        labor_hours = (labor_hours or 0) + (js.get("labor_hours") or 0)
    if 0 < brink_days < 7:
        notes.append(f"Brink sales cover {brink_days}/7 days")

    out["sales"] = {
        "forecast": forecast,
        "net_sales": rnd(net),
        "over_under": rnd(net - forecast) if (net is not None and forecast is not None) else None,
    }

    # ── FOOD COST ────────────────────────────────────────────────────────
    fcp = load("food_cost_plan.json") or {}
    cogs_pct = fcp.get("cogs_pct_week")
    cogs_goal = fcp.get("cogs_goal_pct")
    if fcp.get("week_start") and fcp["week_start"] != mon.isoformat():
        notes.append(f"COGS week is {fcp.get('week_start')}–{fcp.get('week_end')} (source lag)")
    out["food_cost"] = {
        "cogs_pct": cogs_pct,                       # percent, e.g. 23.4
        "supplies_pct": None,                       # manual — no automated source yet
        "total_pct": None,                          # needs supplies
        "qtd_cogs_pct": None,                       # manual — no QTD source yet
        "var_to_goal": rnd(cogs_pct - cogs_goal) if (cogs_pct is not None and cogs_goal is not None) else None,
        "goal_pct": cogs_goal,
        "top_var_items": [i.get("name") for i in (fcp.get("items") or [])[:3]],
    }

    # ── LABOR ────────────────────────────────────────────────────────────
    hourly_labor_pct = rnd(100 * labor_cost / net) if (labor_cost and net) else None

    # OT from the Monday tips snapshot (per-employee pooled hours)
    tips = load(f"tips_we_{sun.strftime('%Y_%m_%d')}_snapshot.json")
    ot_hours = charged_tips = None
    if tips:
        charged_tips = tips.get("chargedTips")
        payouts = tips.get("payouts") or {}
        if isinstance(payouts, dict):
            ot_hours = rnd(sum(max(0.0, (v.get("hours") or 0) - 40.0) for v in payouts.values()))
    else:
        notes.append(f"tips snapshot for w/e {sun.isoformat()} not found")

    out["labor"] = {
        "hourly_labor_pct": hourly_labor_pct,
        "labor_all_in_pct": None,       # manual — payroll/tax data not automated
        "labor_no_salary_pct": None,    # manual
        "ot_hours": ot_hours,
        "qtd_labor_pct": None,          # manual
        "qtd_labor_no_salary_pct": None,
        "labor_hours": rnd(labor_hours),
    }
    out["labor"]["cogs_labor_all_in_pct"] = None  # needs labor all-in
    out["tips"] = {"charged_tips": charged_tips}

    # ── FOOD SAFETY ──────────────────────────────────────────────────────
    shops = load("shop_performance.json") or {}
    latest = shops.get("latest_shops") or []
    qtd_scores = [s["score"] for s in latest
                  if s.get("score") is not None and s.get("date", "") >= quarter_start.isoformat()]
    out["food_safety"] = {
        "steritech_pct": None,          # manual — no automated Steritech pull yet
        "criticals": None,              # manual
        "shops_month_pct": shops.get("store_avg_month"),
        "shops_month_label": shops.get("current_month_label"),
        "shops_qtd_pct": rnd(sum(qtd_scores) / len(qtd_scores), 1) if qtd_scores else None,
        "shops_qtd_count": len(qtd_scores),
        "shops_ytd_pct": shops.get("store_avg_ytd"),
    }

    # ── FGU ──────────────────────────────────────────────────────────────
    fgu = load("fgu_training.json") or {}
    stats = fgu.get("stats") or {}
    learners = fgu.get("learners") or []
    behind = sorted(
        (l for l in learners if (l.get("completion_rate") or 0) < 100),
        key=lambda l: l.get("completion_rate") or 0,
    )
    out["fgu"] = {
        "overdue_rate_pct": stats.get("coursesOverdueRate"),
        "completion_rate_pct": stats.get("coursesCompletionRate"),
        "behind_learners": [
            {"name": l.get("full_name"), "completion_pct": l.get("completion_rate")} for l in behind[:12]
        ],
        "behind_count": len(behind),
    }

    # ── COMPLIANCEMATE ───────────────────────────────────────────────────
    cr = load("compliance_rollups.json") or {}
    wk = cr.get("week") or {}
    out["compliancemate"] = {
        "completion_pct": wk.get("required_pct_avg"),
        "shake_pct": None,          # manual — per-list weekly rollup not built yet
        "short_completions": None,  # manual
        "am_pm_pct": None,          # manual
        "shift_change_pct": None,   # manual
        "pump_pct": None,           # manual
    }

    out_path = DATA / "synopsis_2065.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"[ok] wrote {out_path} for week {out['meta']['week_label']}")
    for n in notes:
        print(f"  [note] {n}")


if __name__ == "__main__":
    main()
