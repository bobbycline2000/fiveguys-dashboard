#!/usr/bin/env python3
"""
Build the weekly Food Cost Plan of Action from the latest CrunchTime
Actual-vs-Theoretical variance items (data/cogs_variance.json).

For each over-budget item it attaches concrete, Five-Guys-specific action
steps so the GM/managers know exactly what to attack. Writes
data/food_cost_plan.json -> rendered by food_cost_plan.html.

Run weekly (Monday) after scrape_cogs.py.
"""
import json, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

def latest_variance():
    f = DATA / "cogs_variance.json"
    if f.exists():
        return json.loads(f.read_text())
    base = DATA / "raw" / "crunchtime" / "2065"
    if base.exists():
        for d in sorted([x for x in base.iterdir() if x.is_dir()], reverse=True):
            c = d / "cogs_variance.json"
            if c.exists():
                return json.loads(c.read_text())
    return None

# Bobby's Big Six focus items (where the money is) + bread
BIG_SIX = ("meat","beef","cheese","bacon","hot dog bun","hamburger bun","bun","hot dog","hotdog")

# keyword -> action steps (Bobby's playbook, 2026-05-24). First match wins.
ACTIONS = [
    # Ground beef / patties / burgers
    (("cheeseburger","hamburger","burger","beef","patty","patties","ground beef"), [
        "Spot-check patty weight — patties must be rolled at 3.5 oz.",
        "Reduce waste — drop patties off the register callbacks, don't pre-drop.",
        "Audit comps & employee meals — every free build has to be rung.",
    ]),
    # Bacon
    (("bacon",), [
        "Variance = over-cooking. Too much cooked and wasted at close, or someone's eating it.",
        "Cook in smaller batches through the day — aim to run out around 8 PM, not over-cook in the morning.",
        "Lock down end-of-night bacon waste and account for it.",
    ]),
    # Produce / toppings
    (("lettuce","tomato","tomatoes","green pepper","pepper","jalapeno","jalapenos","onion","pickle","mushroom","relish"), [
        "Employee meals aren't being rung right and product is being over-portioned — watch portioning.",
        "Confirm prep specs are correct.",
        "Submit a Product Issue form for yield loss from bad quality off the truck.",
        "Account for waste.",
    ]),
    # Drinks / cups / straws
    (("soda","drink","bottle"," cup","straw","beverage","coke","iced tea","fountain"), [
        "This is a miscount — the inventory wasn't counted correctly. Recount it.",
    ]),
    # Bread / buns
    (("bread","bun","buns"), [
        "Variance is employee meals not being entered, waste, or a miscount.",
        "Verify every employee meal is rung and recount on-hand.",
    ]),
    # Cheese / hot dog (Big Six, miscount/portion)
    (("cheese",), [
        "Big Six item — watch it. Count cheese slices per build; verify receiving count vs invoice.",
        "Recount on-hand — a miscount is the usual cause of a big swing.",
    ]),
    (("hot dog","hotdog"), [
        "Big Six item. Variance = employee meals not rung, waste, or miscount. Recount and check comps.",
    ]),
]
DEFAULT = [
    "Watch portioning and confirm the build/prep spec.",
    "Verify employee meals are being rung and review waste.",
    "Recount on-hand — check for a miscount or receiving error.",
]

def actions_for(name):
    n = (name or "").lower()
    for keys, steps in ACTIONS:
        if any(k in n for k in keys):
            return steps
    return DEFAULT

def is_big_six(name):
    n = (name or "").lower()
    return any(k in n for k in BIG_SIX)

def main():
    d = latest_variance()
    if not d:
        print("no cogs_variance.json found — nothing to build"); return
    m = d.get("meta", {})
    # Food cost %: prefer this week's; else fall back to the most recent non-null
    # snapshot (the FP% from the daily COGS email).
    cogs_pct = d.get("cogs_pct_week")
    pct_week_label = m.get("week_end")
    if cogs_pct is None:
        base = DATA / "raw" / "crunchtime" / "2065"
        if base.exists():
            for dd in sorted([x for x in base.iterdir() if x.is_dir()], reverse=True):
                c = dd / "cogs_variance.json"
                if c.exists():
                    try:
                        snap = json.loads(c.read_text())
                        if snap.get("cogs_pct_week") is not None:
                            cogs_pct = snap["cogs_pct_week"]
                            pct_week_label = snap.get("meta", {}).get("week_end")
                            break
                    except Exception:
                        continue
    # Variance items: use the INGREDIENT-level Actual-vs-Theoretical report
    # (cogs_avt_live.json) — the real theoretical food-cost report. Falls back to
    # cogs_variance.json items only if that file is missing.
    items_src = []
    avt = DATA / "cogs_avt_live.json"
    if avt.exists():
        try:
            ls = json.loads(avt.read_text()).get("listSummary", [])
            for it in ls:
                a = (it.get("actual") or {}).get("value")
                t = (it.get("theoretical") or {}).get("value")
                if a is None or t is None:
                    continue
                items_src.append({
                    "name": it.get("name"),
                    "actual": round(a, 2), "theoretical": round(t, 2),
                    "over_dollars": round(a - t, 2),
                    "variance_pct": (it.get("variancePercentage") or {}).get("value"),
                })
        except Exception:
            items_src = []
    if not items_src:
        items_src = d.get("items", [])

    over = [it for it in items_src if (it.get("over_dollars") or 0) > 0]
    over.sort(key=lambda x: x.get("over_dollars", 0), reverse=True)
    over = over[:3]   # Bobby: top 3 variance items only
    plan = [{
        "rank": i+1, "name": it.get("name"),
        "over_dollars": it.get("over_dollars"),
        "actual": it.get("actual"), "theoretical": it.get("theoretical"),
        "variance_pct": it.get("variance_pct"),
        "big_six": is_big_six(it.get("name")),
        "actions": actions_for(it.get("name")),
    } for i, it in enumerate(over)]
    out = {
        "store": m.get("store", "2065"),
        "week_start": m.get("week_start"), "week_end": m.get("week_end"),
        "variance_week_start": m.get("variance_week_start"),
        "variance_week_end": m.get("variance_week_end"),
        "cogs_pct_week": cogs_pct,
        "cogs_pct_week_label": pct_week_label,
        "cogs_goal_pct": d.get("cogs_goal_pct") or 27.5,
        "total_over": round(sum(it["over_dollars"] for it in plan), 2),
        "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M ET"),
        "items": plan,
    }
    (DATA / "food_cost_plan.json").write_text(json.dumps(out, indent=2))
    print(f"food_cost_plan.json: {len(plan)} over-budget items, total over ${out['total_over']:,.0f}, week {out['week_start']}–{out['week_end']}")

if __name__ == "__main__":
    main()
