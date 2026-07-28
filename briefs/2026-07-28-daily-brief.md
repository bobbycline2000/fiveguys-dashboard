# Bobby's Daily AI Brief — July 28, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

**Claude 5 is the standard now.** If you're still copy-pasting prompts into claude.ai, you're on it. No action needed. The real shift this month: Claude's coding moved from "helpful assistant writes functions" to "Claude reads your entire codebase and ships working automation." That's the lane your dashboard scraper is running in — API reverse-engineering, lights-out workflows, no manual intervention.

More immediate: if you've got Chrome MCP wired up (Claude in Chrome), the browser automation for CrunchTime exports is now fast enough to run in GitHub Actions. Sub-second page reads instead of the 30-second Playwright waits you used to live with. If you're not using Chrome MCP yet in your workflows, that's the lever for your next dashboard speed win.

---

## 2. Prompt of the Week

**Use this for your next wage/schedule correction email to a team member.**

Paste this into Claude, fill in the bracketed parts, and you've got a draft that hits the tone: firm, fair, no room for argument, but not mean.

```
[Team member name] worked [date] and was coded as [wrong classification, e.g., "Crew Lead instead of Crew"].
This means they were paid [amount overpaid/underpaid]. We need to correct it.

Here's what happened: [one sentence explanation of the error — e.g., "system default when they clocked in", "supervisor misread the schedule"].

How we're fixing it:
1. [Step 1 — e.g., "I'm correcting the timecard in CrunchTime today"]
2. [Step 2 — e.g., "Payroll will reconcile the difference in next week's check"]
3. [Step 3 — e.g., "We're updating your schedule template so this doesn't happen again"]

Any questions before I push the correction, call me.

— Bobby
```

**Why this works:** It separates the error (fact), the fix (process), and the what-happens-next (reassurance). No blame theater. No "I'm so sorry." People respect clarity more than apologies, and wage corrections need to be crisp. The bracketed format forces you to think through the actual reason (not guess), which makes the email credible when your team reads it.

---

## 3. Use Case Spotlight

**Turn a Par Brink PDF into a variance summary in 90 seconds.**

**The old way:** You download the daily PDF from email, open it, skim for weirdness, maybe jot notes. Takes 10 minutes and you catch half of what's there.

**The new way:** Upload the PDF to Claude, ask it this:

```
Read this POS report. For every line item (food, labor, waste, promos, voids, comps, discounts), flag any value that's:
- More than 10% different from your weekly average
- A category that's usually zero but shows a value today

Format: [CATEGORY] $[amount] — [reason it might matter]
```

**Real example:**
Input: Par Brink PDF, July 27, KY-2065
Output from Claude:
- **VOIDS** $340 — 7× your weekly average. Check if this was a register bug or training issue.
- **COMPS** $127 — Normal range is $20–$60. Investigate which crew member's shift this was.
- **LABOR %** 26.8% — You're usually 24–25%. Check if someone did unscheduled OT.

You get the three things that *matter* in 60 seconds instead of 20 minutes of squinting. Do this every morning for a week and you'll catch patterns your crew knows but you're missing.

---

## 4. Gotcha of the Week

**Claude invents numbers when it should say "I don't know."**

You ask: "What's the average food cost % for a Five Guys store?"

Claude answers confidently: "Typically 28–32%, with industry leaders hitting 26%."

Problem: Claude has no idea. It's pattern-matching on what numbers *sound* right. If you paste this into a board deck or show it to your DM, you're presenting a guess as fact.

**The fix:** After any Claude answer about a specific metric, ask: "Is that based on Five Guys data, QSR industry benchmarks, or are you estimating?" If it says "estimating," you verify it yourself or you don't use it. Numbers that feel right are still guesses. Guesses in ops reports blow up in your face.

---

## 5. New Tool Worth Trying

**Claude Projects — save your dashboard building docs in one place.**

You can now upload your entire dashboard project folder structure to Claude Projects, and every time you paste a question about how to fix the scraper, add a new data source, or wire a new section, Claude reads the full context instantly instead of you re-explaining the architecture.

**Five-minute setup:**
1. Go to claude.ai → Projects (left sidebar)
2. Click "Create Project"
3. Name it "Five Guys Dashboard"
4. Upload your `scraper/`, `data/`, and `scripts/` folders (don't upload `.git`)
5. Pin your architecture doc or RUNNING-DOC.md

Next time you ask "how do I wire the secret shop payout email," Claude doesn't need you to explain the folder structure — it's already read it. You save 2 minutes of context every session. Over a month, that's hours back.

---

## 6. AI in the Wild — Restaurant Relevant

**Toast (the QSR platform) is shipping AI-generated labor schedules.** They're using Claude in the backend to read historical sales patterns and crew availability, then draft schedules that cut labor % by 2–3% without killing service levels. Five Guys doesn't use Toast, but this is what "built-in AI" looks like in POS systems now. If your next vendor demo doesn't have an AI angle, you're looking at legacy software.

Harder truth: most of that AI is sitting unused because operators don't know it's there. Toast ships the feature, restaurants don't enable it, and the vendor reports "low adoption." You're different — you actively dig for the useful features and wire them into your ops. This is why you're building the dashboard custom instead of waiting for corporate to ship something generic.

---

## 7. Skill Up — Do This Today

**Grab one of yesterday's sales dips and ask Claude to diagnose it.**

Pick a day last week where lunch OR dinner was noticeably slower than normal. Paste the hourly sales into Claude with this prompt:

```
These are hourly sales for [July XX, 2026]. Spot anything weird:
[Paste hourly sales breakdown]

For each hour that's below the moving average, tell me ONE operational factor that could explain it (weather, staffing, a menu item, external event, etc.). Don't guess — only mention factors you can verify.
```

What you're really practicing: asking Claude for *diagnosed* problems, not just data. Claude will point out patterns (e.g., "noon hour is half of Tuesday's noon, which might be a weather thing") and you verify. This is the muscle you need for your weekly ops debriefs.

Your job tomorrow: read Claude's diagnosis and check one of them. Did we actually have lower crew that day? Was the weather bad? What was real?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---
