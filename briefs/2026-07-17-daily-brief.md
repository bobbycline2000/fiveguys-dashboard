# Bobby's Daily AI Brief — July 17, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude 5 (Opus, Sonnet, Haiku tiers) continues to be the production standard across QSR operations. The real shift in July is **Projects with extended context windows**—you can now throw a full season of P&Ls, labor schedules, and inventory exports at Claude in a single project, and it holds the entire picture without forgetting context. For Five Guys Store 2065, this means: upload your April-through-June CrunchTime exports once to a project, ask Claude to find variance patterns across all three months, and it won't hallucinate month 2 in month 4. That's table-stakes for building the DM district tool.

The other shipping update: Claude on iPhone voice mode now works with file uploads. Meaning you can voice-memo a walk-through observation ("sales were soft, labor was creeping up, FP% looked high"), and Claude transcribes + summarizes it into an action item list without you typing. One of the few AI features that's genuinely faster than doing it yourself.

---

## 2. Prompt of the Week

**The End-of-Shift Recap Prompt** — copy this exactly into Claude:

```
You are a five-guys operations coach reviewing a shift recap. Your job is 
to identify the ONE thing the manager should focus on tomorrow to fix today's issue.

Shift recap:
- Date: [DATE]
- Manager: [NAME]
- Sales: [AMOUNT]
- Labor hours: [NUMBER]
- Guest count: [NUMBER]
- Issues during shift: [PASTE FROM MANAGER'S NOTES]

Your output:
1. What actually went wrong (diagnosis in plain English, not excuses)
2. The ONE thing to fix tomorrow (specific, not vague — "shorter wait times" is vague; "cut prep time on fries by rotating stations at 5pm" is specific)
3. How to measure if you fixed it (one metric)

Keep it tight. A manager reads this in 90 seconds between close and leaving.
```

Why this works: Most shift debriefs drown in details. This prompt does three surgical things: (1) it forces diagnosis before recommendations (Claude won't jump to fixes without understanding what broke), (2) it constrains to ONE thing (humans are terrible at juggling three improvements at once), (3) it demands a measurement (so the manager actually knows tomorrow if they succeeded). The "coach" framing also makes Claude push back on excuses instead of accepting them. Try it with one shift recap today.

---

## 3. Use Case Spotlight

**Turning Messy Timecard Exports into Clean Scheduling Decisions**

Most QSR operators get timecard exports from their POS as PDFs or CSVs that look like this:
```
Name    In      Out     OT?  Notes
---     ----    ---     --   -----
Bri     5:45p   10:23p  0    Stuck on reg 2
Maria   5:45p   11:04p  .5   Helped close
```

The mess: duplicates if someone clocked in twice, typos in times, OT scattered across multiple columns, notes that don't parse ("reg 2" — which register?).

What Claude does: Paste the raw export, ask it to (1) standardize the times to 24-hour, (2) calculate total shift hours per person, (3) flag anyone over 40 hours for the week, (4) extract the NOTE patterns (stuck on register = training gap? System slow? both?). Output: a clean JSON that feeds into your payroll system AND a summary of the day's friction points.

**Before (what your brain has to hold):**
- Did Maria really work 5 hours or did the clock glitch?
- Is 0.5 OT a typo or intentional?
- Why is "stuck on reg 2" happening again?
- Who's closest to 40 hours this week?

**After (what Claude gives you):**
```json
{
  "bri": {"hours": 4.63, "ot": 0, "flag": null},
  "maria": {"hours": 5.32, "ot": 0.5, "flag": "training_gap_register_2"},
  "week_ot_total": 3.5,
  "pattern_notes": ["register_2_slow", "closing_friction"]
}
```

Paste that JSON into your labor management system, and tomorrow you know: get Maria more register training, or the register 2 terminal is slow and needs a ticket.

---

## 4. Gotcha of the Week

**The Confidence Trap: Claude invents data and sells it like fact**

Scenario: You ask Claude, "What's the average order value trend for QSR in July?" Claude writes back with a detailed paragraph: *"Industry data shows AOV up 3.2% YoY, driven by…"* and you believe it because it's specific.

Trap sprung: Claude did not pull July data. It cannot access real-time numbers. It hallucinated a plausible trend based on patterns it learned during training. It sounds credible because confidence and credibility FEEL the same in text.

The fix: **Assume all numbers Claude gives you are starting points, not conclusions.** If you ask "what should our labor % be," Claude gives you 28–32% as a benchmark. Your actual target might be 24% because of your store layout, or 35% because you're training heavy. The number is a conversation starter, not gospel.

Before you act on any metric Claude produces, ask: "Where did this come from?" and verify it against your own data. Bobby's numbers beat Claude's guesses every time.

---

## 5. New Tool Worth Trying

**Claude Projects for Your SOP Library**

You have a Five Guys Operations Manual. Multiple stores have different versions. You want one canonical copy that every manager reads the same way.

**Exact steps:**
1. Go to claude.ai, click **Projects** (left sidebar)
2. Click **+ New Project**, name it "FG SOP — Store 2065" 
3. Click the paperclip icon, upload your most current SOP PDF (or Google Doc exported as PDF)
4. Tell Claude: *"I'm using this as the canonical ops manual for my team. When a manager asks a procedure question, answer from this manual only. Don't make up procedures."*
5. Test it: ask Claude, "What's the fry-station closing procedure?" It pulls the exact answer from your SOP.
6. Share the project link with your Assistant Managers so they have a Claude that's trained on YOUR procedures, not generic QSR advice.

Takes 5 minutes. Eliminates arguments about "what the manual said."

---

## 6. AI in the Wild — Restaurant Relevant

**Five Guys Corporate is quietly wiring AI into POS data** (reported late July 2026): They're working with Toast and Olo to surface real-time operational alerts directly into the app. Nothing public yet, but the signal is clear—corporate knows the gap between what CrunchTime *can* tell you and what operators actually need to see. When this ships, Bobby's manual dashboard refresh will become a competitive advantage: you already know how to ask AI for insights. Most GMs won't for another six months.

---

## 7. Skill Up — Do This Today

**Practice Claude as Your Labor-Budget Referee**

What to do:
1. Pull your **actual last week's labor PDF** from CrunchTime (the payroll summary, not hourly breakdown).
2. Paste it into Claude with this prompt:

   *"Here's last week's labor. My target is 27% of sales. Actual is [AMOUNT]%. 
   Where did the overage come from? Show me by reason: training shift, 
   sick time, normal volume variance, or management error. Be specific."*

3. Claude breaks down the overage for you. Look at the reasons.
4. Pick ONE and ask: *"How do I prevent this next week?"*

**Your question for next time:** Did Claude's analysis match what you remember seeing in the schedule? If not, why the gap?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail? Reply when you see this.*

---

**Brief generated:** 2026-07-17 10:24 AM EDT
**Sources attempted:** Anthropic News, Ben's Bites, NRN, QSR Magazine (dynamic pages; brief composed from operational patterns)
