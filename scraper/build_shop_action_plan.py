"""
Build a SMART action plan email body for a sub-100% secret shop.

Usage:
    python scraper/build_shop_action_plan.py <job_id>

Reads from:
- data/raw/marketforce/2065/<latest>/shops.json   (the shop record)
- data/raw/marketforce/2065/participation.json    (who was on shift)
- data/employee_name_map.json                     (first → "First Last")

Writes to:
- data/drafts/shop-action-plan-<job_id>.md  (audit copy of the body)

Prints to stdout: the email body (so caller can pipe into Outlook draft).
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
DASH = HERE.parent
DATA = DASH / "data"
MF = DATA / "raw" / "marketforce" / "2065"
DRAFTS = DATA / "drafts"
DRAFTS.mkdir(parents=True, exist_ok=True)


def latest_shops():
    folders = sorted(MF.glob("*/shops.json"))
    if not folders:
        raise FileNotFoundError("No shops.json")
    return folders[-1]


def load_all():
    with open(latest_shops()) as f:
        shops_doc = json.load(f)
    with open(MF / "participation.json") as f:
        part = json.load(f).get("by_shop", {})
    with open(DATA / "employee_name_map.json") as f:
        name_map = json.load(f)
    return shops_doc.get("shops", []), part, name_map


# SMART action plan templates keyed to which sub-score was lowest.
# Each plan must hit all 5 SMART parts: Specific / Measurable / Achievable / Relevant / Time-bound.
PLAN_TEMPLATES = {
    "service": {
        "headline": "SERVICE — points lost on greeting, attentiveness, or order accuracy",
        "specific": "Re-train every shift on the FG greet within 5 seconds rule and the order-back-read at the register. MOD names the greeter at clock-in and verifies they greet the next 10 guests.",
        "measurable": "Zero missed greetings on a 30-guest spot-check. Cashier reads back 100% of orders for 14 consecutive days.",
        "achievable": "MOD on every shift owns the greet-check during pre-shift huddle. Cashier read-back is policy — no extra training needed, just enforcement.",
        "relevant": "Service is FG Pillar #2. A missed greet costs us guests and shop points.",
        "time_bound": "Start the day this brief is signed. Review at the next 5-minute pre-shift huddle each day for 14 days. MOD reports compliance daily.",
    },
    "quality": {
        "headline": "QUALITY — points lost on food temp, build accuracy, or fry hold time",
        "specific": "Tighten the line: portion fries every 3 minutes (no exceptions), patty temp checked at every changeover, build sheets posted at every station.",
        "measurable": "Fry timer hits 3:00 on every drop. Patty temp logged at every changeover. Build sheet on every station every shift.",
        "achievable": "Already part of the line setup — this is enforcement, not new training. MOD walks the line every 30 minutes and corrects in the moment.",
        "relevant": "Quality is FG Pillar #1 (along with COGS — they're tied). Cold fries and wrong builds are the #1 reason guests don't come back.",
        "time_bound": "In effect the next shift. MOD documents the line walk on the back-of-house clipboard for 14 days; review at end-of-week huddle.",
    },
    "cleanliness": {
        "headline": "CLEANLINESS — points lost on lobby, dining, restroom, or line condition",
        "specific": "Lobby + dining + restroom touch-ups at the 30 / 60 / 90 minute marks of every shift. MOD owns the walk; assigned crew member completes the touch-up and signs the sheet.",
        "measurable": "Touch-up sheet signed 3x per shift, every shift. Zero customer complaints on lobby or restroom for 14 consecutive days.",
        "achievable": "Already a Steritech expectation — this is daily discipline, not new training. Add the sheet to the MOD clipboard tomorrow.",
        "relevant": "Cleanliness is FG Pillar #3 and is tested on every shop AND every Steritech audit. Two birds, one routine.",
        "time_bound": "Effective tomorrow's first shift. Review at next 5-minute pre-shift huddle every day for 14 days.",
    },
    "customer_satisfaction": {
        "headline": "CUSTOMER SATISFACTION — points lost on overall guest experience or recovery",
        "specific": "When a guest looks unhappy, the MOD goes to the table within 60 seconds. Train every crew member to flag the MOD on any visible guest concern. Comp policy review at next shift huddle.",
        "measurable": "MOD logs every table-touch on the back-of-house clipboard. Target: 5 proactive table-touches per shift. Zero unaddressed complaint emails for 14 days.",
        "achievable": "Just discipline — table-touching is already part of the GM/MOD role. Crew flagging is a 30-second huddle teach.",
        "relevant": "Customer Satisfaction directly drives shop scores AND repeat business. The scoring rubric weighs recovery heavily.",
        "time_bound": "Starting tomorrow's lunch shift. Review proactive-touch counts at end-of-week huddle.",
    },
}


def build_body(shop, on_shift_full, job_id):
    score = shop.get("score") or 0
    points_lost = round(100 - score, 1)
    date_str = shop.get("date", "?")
    meal = shop.get("meal_period", "?")

    subs = {
        "service": shop.get("service"),
        "quality": shop.get("quality"),
        "cleanliness": shop.get("cleanliness"),
        "customer_satisfaction": shop.get("customer_satisfaction"),
    }

    # If sub-scores aren't available yet, fall back to a generic plan.
    available = {k: v for k, v in subs.items() if v is not None}
    if available:
        # Lowest-scoring categories (any below 100, sorted ascending).
        focus = sorted([(k, v) for k, v in available.items() if v < 100], key=lambda x: x[1])
        if not focus:
            focus = [(min(available, key=available.get), available[min(available, key=available.get)])]
    else:
        focus = [("customer_satisfaction", None)]  # safe default

    header = f"""\
KY-2065 Secret Shop — Action Plan
Shop date: {date_str} ({meal})
Final score: {score}%   Points lost: {points_lost}
Job #: {job_id}

On shift during the meal period:
"""
    for name in on_shift_full:
        header += f"  - {name}\n"

    if available:
        header += "\nSub-score breakdown:\n"
        for cat in ("service", "quality", "cleanliness", "customer_satisfaction"):
            v = subs.get(cat)
            label = cat.replace("_", " ").title()
            if v is None:
                header += f"  - {label}: (not reported)\n"
            else:
                tag = "[OK]" if v >= 100 else "[LOSS]"
                header += f"  - {label}: {v}%   {tag}\n"
    else:
        header += "\nSub-score breakdown not yet available — plan covers the most-common loss area.\n"

    body = header + "\n" + "=" * 56 + "\nS.M.A.R.T. ACTION PLAN\n" + "=" * 56 + "\n"
    for cat, val in focus:
        plan = PLAN_TEMPLATES[cat]
        loss_line = f" (scored {val}%)" if val is not None else ""
        body += f"\n--- {plan['headline']}{loss_line} ---\n"
        body += f"Specific:    {plan['specific']}\n"
        body += f"Measurable:  {plan['measurable']}\n"
        body += f"Achievable:  {plan['achievable']}\n"
        body += f"Relevant:    {plan['relevant']}\n"
        body += f"Time-bound:  {plan['time_bound']}\n"

    body += "\n" + "=" * 56 + "\n"
    body += "ACCOUNTABILITY:\n"
    body += "- MOD on shift signs the back-of-house clipboard each day this plan is active.\n"
    body += "- Every crew member who reads this plan initials below.\n"
    body += "- Bobby reviews progress at the end-of-week huddle.\n"
    body += "\nThis is a coaching opportunity, not a punishment. Hit the plan, win the next shop.\n"
    body += "\n— Bobby Cline\nGeneral Manager — Store 2065\n"
    return body


def main():
    if len(sys.argv) != 2:
        print("Usage: python build_shop_action_plan.py <job_id>", file=sys.stderr)
        sys.exit(2)
    job_id = sys.argv[1]

    shops, part, name_map = load_all()
    shop = next((s for s in shops if str(s.get("job_id")) == job_id), None)
    if not shop:
        print(f"Job {job_id} not found in shops.json", file=sys.stderr)
        sys.exit(1)

    if (shop.get("score") or 0) >= 100:
        print(f"Job {job_id} scored 100% — use shop-payout-draft instead.", file=sys.stderr)
        sys.exit(1)

    firsts = part.get(job_id, [])
    if not firsts:
        print(f"NO_PARTICIPATION {job_id}", file=sys.stderr)
        sys.exit(3)

    full = []
    unresolved = []
    for f in sorted(firsts):
        mapped = name_map.get(f)
        if not mapped:
            unresolved.append(f)
        else:
            full.append(mapped)
    if unresolved:
        for u in unresolved:
            print(f"NAME_UNRESOLVED {u} for job {job_id}", file=sys.stderr)
        sys.exit(4)

    body = build_body(shop, full, job_id)
    audit = DRAFTS / f"shop-action-plan-{job_id}.md"
    audit.write_text(body)
    print(body)
    print(f"\n# Audit copy saved to: {audit}", file=sys.stderr)


if __name__ == "__main__":
    main()
