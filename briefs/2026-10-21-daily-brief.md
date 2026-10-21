# Bobby's Daily AI Brief — 2026-10-21
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude Haiku 5.5 shipped October 7. It's the fastest small model Anthropic has released — which means it runs at roughly 1/3 the cost of the previous Haiku, with better reasoning. For you: this model is ideal for batch operations that don't need deep analysis. If you're looping Claude over 50 inventory items or running daily tip-entry summaries, Haiku 5.5 cuts your token spend and speeds up the reply. The Claude desktop app and web interface should default to it automatically.

That's the consumer signal this week. Nothing headline-shifting. The real story is that Haiku 5.5 makes lightweight operations cheaper and faster — which is exactly where your dashboard automation lives.

---

## 2. Prompt of the Week

Use this exact prompt when you need Claude to give you a labor scheduling recommendation for an unexpected situation (no-show, emergency, shift swap):

```
You are a labor ops advisor for a Five Guys restaurant. Your job is to recommend the best solution for staffing problems, always protecting food quality and customer experience.

Current situation:
- [Describe the problem: who called out, what time, what shift, how many people affected]
- Current scheduled crew: [List names and positions]
- Available alternatives: [List people you could call]
- Current labor %: [Your current percentage]

What's your recommendation? Be specific:
1. Best option to fill this gap (who to call, in what order)
2. Why this protects both labor % and service
3. If you can't fill the gap, what's the fallback (reduced hours, reduced menu items, etc.)

Explain your logic in plain language. I need to make this call in 5 minutes.
```

Why this works: Claude is trained to recognize food safety constraints, labor percentages, and operational reality. The specific structure forces Claude to prioritize (best option first), justify the math, and give you a fallback. The "5 minute" constraint prevents over-analysis. You're not asking Claude to *make* the call — you're asking it to *advise* so you make a faster, smarter decision.

---

## 3. Use Case Spotlight

**Before:** You get a CrunchTime P&L export. It's a wall of numbers. You spend 30 minutes scrolling, cross-referencing actuals vs. plan, trying to figure out what moved.

**After:** Paste the export into Claude with this prompt:
```
This is my Five Guys P&L from [DATE]. What are the 3 biggest variances (positive or negative) from plan? For each one, tell me what caused it and what I should investigate first.
```

Claude parses the numbers, spots the outliers, and tells you where to dig. A variance that looks like noise gets contextualized (new supplier? higher labor? mix shift?). You go from "Why is food cost at 32%?" to "Your chicken order was 18% higher this week — worth checking if that's seasonal demand or a supplier issue."

This is Claude doing spreadsheet janitoring so you do strategy.

---

## 4. Gotcha of the Week

**The trap:** You ask Claude "What should my food cost be?" and Claude gives you a number — say, "29.5% is typical." You write that down. You tell your team. You make decisions based on it.

**The problem:** Claude invented that number. It's plausible, it sounds confident, but it's not tied to *your* store, *your* supplier contracts, *your* menu mix, or *your* product quality standards. Five Guys franchises vary wildly. Your 29.5% might be wildly wrong.

**The fix:** Always ask Claude to explain *why* a number exists, not just *what* it is. Ask: "Why would food cost be 29.5%? What's driving that — labor? waste? pricing? mix?" Then cross-reference Claude's logic against your actual costs. If Claude says "labor is 30% of food cost," you can verify that against your P&L. If it says "assume 5% waste," you can check whether that matches your actual shrink. Anchor Claude's numbers to your reality. Never use a number just because it sounds right.

---

## 5. New Tool Worth Trying

**Claude for Chrome + Your Vendors.**

Open Chrome. Navigate to any vendor site (Sysco, US Foods, your POS provider, your scheduling app). Click the Claude for Chrome extension. Paste in: "What are my last 3 orders?" or "Show me my invoice history" or "What am I spending per month on X?"

Claude reads the page and pulls the data for you — no copy-paste, no manual lookup. Takes 90 seconds. First time takes 2 minutes because you're finding the button.

If your vendor site has a login wall, this won't work. But for sites you're already logged into (your FG portal, your delivery app, your bank), this is a 5-minute win.

---

## 6. AI in the Wild — Restaurant Relevant

**Olo launched a white-label restaurant ordering app** this week. The big claim: no menu price markup. Most third-party apps charge restaurants 15–30% fees hidden in higher menu prices. Olo is betting that restaurants will use them if the math is clean.

Why you should watch: This is the restaurant industry finally admitting that delivery fees and platform markup are out of control. Five Guys corporate isn't advertising delivery partnerships aggressively — that's strategic. But if Olo (or Toast, or a competitor) makes ordering cheaper for franchisees, the pressure on corporate to offer better terms increases. Labor, food cost, delivery margins — all moving. Watch how Five Guys responds.

**Second story, more actionable:** Nation's Restaurant News ran a column this week titled "We know exactly when the rush hits — why don't we know who'll be there to handle it?" The premise: you have 52 weeks of sales history. You know Monday at 6 PM is chaos. You know Friday lunch is predictable. But you schedule crew the same way every week — reactive, last-minute. The gap is real, and it's costing you labor %.

---

## 7. Skill Up — Do This Today

Open Claude. Paste in your most recent weekly schedule (the one you built for this week). Then ask:

```
I'm building next week's schedule. Based on this week's actual sales, what are the 2–3 hours I staffed too heavy and 2–3 hours I understaffed? What should I change for next week?
```

Claude will compare your scheduled hours to what actually happened and give you specific recommendations. Not perfect — you have context Claude doesn't — but it's a pattern detector that takes 30 seconds to run.

**Question for next time:** When Claude spotted a difference between your schedule and actuals, did it match what you already knew, or did it show you something you missed?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
