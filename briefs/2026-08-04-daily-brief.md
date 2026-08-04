# Bobby's Daily AI Brief — August 4, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

**Claude's upcoming voice mode expansion** has hit wider release. For restaurant ops, this means you can voice-memo your end-of-shift debrief into Claude on your phone and get a structured action list back within seconds — no typing required. Most operators still think of Claude as something you sit down to use. The voice path changes that: talk-to-analyze-to-action loop while you're walking the line during closing.

Why it matters: Your shift notes are valuable data. Right now they're either not captured or stuck in your head. Voice mode makes capture frictionless. You'll start externalizing the pattern-matching your gut does naturally. That means the next GM (or an operator you're training) gets a repeatable system instead of "do what Bobby does."

---

## 2. Prompt of the Week

**Use this when reviewing a labor schedule from CrunchTime or Teamworx and you smell something off:**

```
Role: You are a five-guys store labor analytics expert. You've worked as a GM and assistant manager at high-volume locations.

I'm sending you a weekly labor schedule. Your job is to flag:
1. Shifts that are under-staffed for that daypart (lunch/dinner/prep)
2. Gaps in coverage (no opener/closer, no experienced person on shift)
3. Opportunities to cross-train (if Jane works dish 8 hours this week, can she shadow front counter for 1 shift?)
4. Days where labor % looks like it'll spike (if we hit forecast, are we over budget?)

Format your response as:
- IMMEDIATE FIXES (fix before the week starts)
- TRAINING OPPORTUNITIES (low-risk moves)
- WATCH (monitor these shifts closely)

Don't tell me what's obvious. Tell me what I'm missing.

---
[PASTE YOUR SCHEDULE HERE]
```

Why this works: Most schedules are built to fill slots, not to optimize for coverage gaps or training. This prompt trains Claude to think like a GM who's seen schedule-created disasters. The "don't tell me obvious" constraint forces Claude to hunt for non-obvious patterns—exactly what your instinct does but what a new manager misses. You get Claude thinking at GM-level, not assistant-manager-level.

---

## 3. Use Case Spotlight

**Cleaning up a chaotic CrunchTime labor export → actionable roster**

Before:
```
Store,Date,Employee,Clockin,Clockout,Role,Exceptions
2065,2026-08-03,BOBBY,14:30,23:15,GM,
2065,2026-08-03,BRIAN V,10:45,16:20,Crew,LATE_PUNCH
2065,2026-08-03,LIDY,11:00,19:30,Crew,MANAGER_OVERRIDE
2065,2026-08-03,DIVAN,12:00,20:45,Crew,
2065,2026-08-03,BROOKLYN,13:15,22:00,Crew,EARLY_LEAVE_PENDING_APPROVAL
...
[50 more rows, inconsistent formatting, missing data in random cells]
```

Prompt to Claude:
```
Clean this CrunchTime export. Standardize times to 24-hr format. Flag:
- Any clock-in after 9am (late arrival)
- Any early departure before 9pm (early leave)
- Manager overrides or exceptions
- Total hours per person
- Gaps (roles with no one scheduled)

Output: CSV with columns: Employee, Role, Hours, Status, Flags
```

After: CSV with 8 rows, clean times, flags highlighted, total labor hours calculated, early/late summarized in one column.

What changed: 10 minutes of manual Excel wrestling becomes 30 seconds + clean data you can actually use. You spot that Brian arrived 45 minutes late and nobody flagged it. You see the breakdown by role for labor-budget planning. You can now feed this into your P&L variance analysis.

---

## 4. Gotcha of the Week

**The Confident Hallucination with Date Math**

You ask Claude: "Our labor % was 29.5% last week. Week before that was 31%. How much did we improve?"

Claude says: "You improved by 1.5 percentage points, or roughly 4.8% improvement week-over-week."

Sounds right. You tell your team. Then auditing your actual P&L, you realize the dates got flipped—the 31% week was actually the more recent one. Claude's math was perfect. The direction was wrong.

**The trap:** Claude is good at arithmetic but has zero way to verify which date is which. It will math confidently using whatever dates YOU gave it, even if you got them backwards.

**The fix:** Always include explicit dates in your question. Not "last week vs. two weeks ago." Say: "Week of July 28–Aug 3 (29.5%) vs. week of July 21–27 (31%). What's the trend?"

Even better: paste your actual P&L export with the dates printed in the source data. Claude then has ground truth instead of relying on your casual reference.

---

## 5. New Tool Worth Trying

**Claude Projects + a CrunchTime SOP**

- Open Claude.ai → click Projects (left sidebar)
- Create new project: name it "CrunchTime Labor Reports"
- Upload your `CrunchTime_Data_Export_Guide.pdf` (if you have it) or a doc with the steps you use weekly
- Add context: "I run a Five Guys store in Louisville. I export labor data weekly for P&L analysis."
- Now every time you start a conversation in that project, Claude has your SOP loaded and will ask clarifying questions scoped to YOUR process, not generic CrunchTime

**Time to try:** 3 minutes. Open Claude → Projects → + Create → name it → upload one doc → done.

Why: You stop re-explaining your workflow every session. Claude knows your store's specific labor-tracking rules.

---

## 6. AI in the Wild — Restaurant Relevant

**Toast (POS system used by high-volume independents and some chains) just released AI-assisted inventory reordering.** It watches your usage patterns for the week, predicts your needs for next week, and flags if your order is way off—not "order 50% more," just "you typically order 200 chicken breasts per week but this order has 140."

Why Bobby should care: Five Guys corporate is not moving this fast. But the larger franchisees who run multiple locations are already experimenting with Toast's API to build custom labor and inventory dashboards. This is the gap that's closing—smart independent operators are out-tooling the corporate supply chain.

Your ops dashboard is already ahead of most Five Guys locations. Keep building.

---

## 7. Skill Up — Do This Today

**Take a voice memo of today's close, have Claude turn it into tomorrow's opening notes.**

Here's the exact process:
1. Open Claude on your phone
2. Switch to Voice mode (settings icon → Voice)
3. At 11 PM (or whenever you close), talk naturally: *"Hey, so we hit about 8,200 today. Brian was late again, we need to coach him. The fry station was slow around 6—noticed the oil cooler thermometer is reading high, I think we gotta check that. Food cost looks heavy on fries this week. We're good on ice cream. Madison needs another cross-train shift. See any labor issues I missed?"*
4. Copy Claude's response into a Google Doc or send to yourself
5. Read it first thing when you open tomorrow

**Your reflection question for next brief:** What did Claude miss from your voice memo? What did it nail that you expected it to overlook?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---
