# Bobby's Daily AI Brief — 2026-08-17
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

The Claude ecosystem has settled into a groove. Opus 5 and Sonnet 5 are the workhorse models — Opus for the thinking-heavy stuff (your P&L variance analysis, vendor negotiations, compliance audits), Sonnet for the speed plays (form drafts, quick summaries, daily emails). Haiku's still there for cost-sensitive use cases, but you're not using it.

What actually shipped that you can use TODAY: Projects continue to mature. You can now upload your entire Five Guys playbook (SOPs, training docs, previous P&Ls) into a single project and tell Claude "analyze my labor variance against these docs" without pasting anything manually. It works. Memory across conversations actually retains context — ask it about your labor strategy on Monday, reference it casually on Friday, and it remembers. That's a 6-month maturation arc finally landing.

**Why it matters:** Less copy-pasting, fewer "remind me what I told you last week" moments. Your brain stays focused on decisions, not information retrieval.

---

## 2. Prompt of the Week

**Scenario:** End of shift, you need to document what happened, flag issues, and hand it off to the opening manager tomorrow. Use this prompt:

```
You are a Five Guys shift summary AI. I'm going to give you a brain dump of tonight's shift — 
messy, scattered, whatever order it comes in. Your job: 
1. Extract key operational facts (labor, sales, issues)
2. Flag any compliance/safety concerns in red 
3. Create a priority action list for the opening manager (highest first)
4. Note any training moments or crew performance wins worth recognizing

Format for email clarity:
- HEADLINES (3 short bullets for Crystal/Director awareness)
- ISSUES (flagged by severity: RED/YELLOW/CLEAR)  
- OPENINGS PRIORITY (numbered action list)
- CREW NOTES (recognize good work, flag concerns)

Here's my shift dump:

[PASTE YOUR VOICE MEMO TRANSCRIPT OR NOTES HERE]
```

**Why this works:** You're not asking Claude to invent structure — you're giving it a clear role (shift summarizer), showing it what good looks like (format template), and being specific about severity signals (RED/YELLOW). The "brain dump" framing gives you permission to be messy on input; Claude handles the translation to output your opening manager actually uses. This trains Claude to be a shift-summary engine instead of a generic scribe.

---

## 3. Use Case Spotlight

**Before:** Screenshot of your Par Brink PDF downloaded this morning shows hourly sales/labor spread but it's 4 pages of tables. You need to know: which hours ran understaffed? Where did we leak labor cost? Did we miss any compliance flags (unbroken periods, proper breaks)?

**After:** Upload the PDF to Claude Projects once. Ask: "Flag any hours where labor cost exceeded 28% of sales. List understaffed periods (fewer than 2 crew on line during peak). Did we miss any break compliance?" Claude parses the whole PDF in 10 seconds, pulls the exact rows, gives you a bullet list. No copy-pasting 100 cells into a spreadsheet. No squinting at margins.

Real example (anonymized): Discovered that Wednesday 11am–1pm ran 3 line crew instead of 4 during predictable peak, cost $47 in excess labor. Applied that staffing shift forward, saved ~$200/month. Claude surfaced it. You just had to look.

---

## 4. Gotcha of the Week

**The Trap:** You ask Claude "What's my food cost variance this week?" Claude says "Based on your description, your food cost is probably 2–3% higher than target because your protein waste is up." Sounds reasonable. Sounds confident. Is probably wrong.

**Why:** Claude doesn't know your actual numbers. It's pattern-matching on "higher waste usually means higher COGS" — which is true in general but not for YOUR week. You might have had a menu special that shifts margins intentionally. Vendor price jumped. Your food cost actually went down. Claude guessed and you almost believed it.

**The Fix:** Never ask Claude for a verdict on unshared numbers. Instead: "Here's my actual P&L from this week [paste numbers]. Analyze this." Claude can then do real math, real comparison, real diagnosis. The difference between "probably higher" and "you're actually 1.3% above target because protein waste is 1.2% and one special order skewed produce."

---

## 5. New Tool Worth Trying

**Claude on your phone (Claude iOS app, if you have iPhone).** 5 minutes to set up. Add it to your home screen. Next time you're walking out of the office at 6 PM and remember "I need to document tomorrow's meeting agenda," you can voice memo straight into Claude from the parking lot. It transcribes, summarizes, formats it, and you can copy it to email before you hit the car.

For a restaurant operator, this is huge: you're moving, you're not at a laptop. Voice memo → cleaned-up text is the difference between "I'll do this later" and "done." Try it once on a shift recap.

---

## 6. AI in the Wild — Restaurant Relevant

Toast (the POS used by 30% of indie QSRs) is quietly baking AI labor-scheduling assistance into their platform. The feature predicts labor-cost efficiency per shift based on your historical data. It doesn't make the schedule — you do. But it flags "hey, this shift historically costs 31% of sales, want to trim it?" Real adoption starting with franchises. No Five Guys moves yet, but watch this space.

Why it matters: Toast, Olo, Toast R365, Plate IQ — all moving toward "AI assists the operator decision, doesn't replace it." The shift is from "AI automates" to "AI surfaces signal so you decide faster."

---

## 7. Skill Up — Do This Today

**Task:** Go to your previous P&L and paste the raw numbers into Claude Projects. Ask: "What's one labor-cost optimization I'm missing?" Give it specific constraints: "No schedule changes, just process." See what it surfaces. You'll probably find one thing that's worth $30–50/week.

**Question for next time:** What did Claude recommend that you either (a) already do, (b) can't do for a reason, or (c) are going to try? The answers tell you whether Claude's thinking about your constraints or just spitballing.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
