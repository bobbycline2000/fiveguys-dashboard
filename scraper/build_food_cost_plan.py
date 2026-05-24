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

# keyword -> action steps (checked in order; first match wins)
ACTIONS = [
    (("cheeseburger","hamburger","burger"), [
        "Re-weigh patties on a calibrated scale — confirm 3.2 oz per patty, no double-stacking.",
        "Count cheese slices per build; one extra slice per burger across a week is real money.",
        "Audit comps & employee meals for this item — verify every free build is logged.",
        "Watch the line build it during a rush — over-portioning lettuce/sauce/bacon adds up.",
    ]),
    (("bacon",), [
        "Verify bacon strip count per build matches spec — weigh a sample.",
        "Check bacon waste/over-cook in the kitchen; log dropped or burnt strips.",
        "Confirm receiving count vs invoice on the last bacon delivery.",
    ]),
    (("fry","fries","potato","idaho"), [
        "Re-check fry scoop weight — level the scoop, no heaping; overfilling cups is the #1 fry leak.",
        "Log dropped/dumped fry batches and end-of-night waste.",
        "Confirm potato case count on receiving vs invoice.",
        "Spot-check 'Little vs Regular vs Large' ring accuracy at the register.",
    ]),
    (("milkshake","shake","cup, shake"), [
        "Measure shake mix portion per cup against spec.",
        "Count topping/mix-in scoops — extra scoops drive cost.",
        "Track wasted/remade shakes in the waste log.",
    ]),
    (("soda","drink"), [
        "Watch for oversized/extra cups and un-rung refills.",
        "Reconcile cup inventory count vs cups rung at POS.",
    ]),
    (("peanut butter","oreo","peppermint","topping","cheese"), [
        "Recount this item — a count/receiving error is the most likely cause of a big swing.",
        "Verify the last receiving matched the invoice and was entered correctly.",
        "Check prep waste and over-portioning on builds that use it.",
    ]),
]
DEFAULT = [
    "Recount on-hand and verify the last receiving was entered correctly.",
    "Check portioning/build spec for this item with the line.",
    "Review waste log and comps for this item this week.",
]

def actions_for(name):
    n = (name or "").lower()
    for keys, steps in ACTIONS:
        if any(k in n for k in keys):
            return steps[:3]
    return DEFAULT

def main():
    d = latest_variance()
    if not d:
        print("no cogs_variance.json found — nothing to build"); return
    m = d.get("meta", {})
    over = [it for it in d.get("items", []) if (it.get("over_dollars") or 0) > 0]
    over.sort(key=lambda x: x.get("over_dollars", 0), reverse=True)
    plan = [{
        "rank": i+1, "name": it.get("name"),
        "over_dollars": it.get("over_dollars"),
        "actual": it.get("actual"), "theoretical": it.get("theoretical"),
        "variance_pct": it.get("variance_pct"),
        "actions": actions_for(it.get("name")),
    } for i, it in enumerate(over)]
    out = {
        "store": m.get("store", "2065"),
        "week_start": m.get("week_start"), "week_end": m.get("week_end"),
        "variance_week_start": m.get("variance_week_start"),
        "variance_week_end": m.get("variance_week_end"),
        "cogs_pct_week": d.get("cogs_pct_week"),
        "cogs_goal_pct": d.get("cogs_goal_pct"),
        "total_over": round(sum(it["over_dollars"] for it in plan), 2),
        "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M ET"),
        "items": plan,
    }
    (DATA / "food_cost_plan.json").write_text(json.dumps(out, indent=2))
    print(f"food_cost_plan.json: {len(plan)} over-budget items, total over ${out['total_over']:,.0f}, week {out['week_start']}–{out['week_end']}")

if __name__ == "__main__":
    main()
