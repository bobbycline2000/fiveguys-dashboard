# Bobby's Daily AI Brief — November 7, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude Haiku 5.5, Sonnet 5.5, and Opus 5.5 all shipped in September-October with **30-40% cheaper pricing and faster response times**. That matters to you directly: your automation costs just dropped. If you've been sitting on automations that felt expensive to run on schedule (daily briefs, tip entry verification, dashboard refreshes), the math just changed. Same output, cheaper compute. More importantly, Haiku got tuned specifically for "high-volume work like summarization, subagents, and browser use" — which is *exactly* what your dashboard pipeline does. You're already running on the right model for the right job. No changes needed, but you're getting better performance for less money as of this week. That's the win: you built the right thing at the right time.

---

## 2. Prompt of the Week

**The Labor Forecast Debrief Prompt:**

```
You are a Five Guys GM analyzing labor forecast misses for a shift debrief with your DM.

The GM has:
- Scheduled hours from Teamworx
- Actual punches from the POS/timecard
- Secret shop or transaction data showing actual rush/traffic
- Customer count or sales velocity data

Your job: write a tight 2-3 paragraph debrief explaining WHY the forecast missed, what happened, and ONE concrete change for next week.

Use this structure:
1. State the miss clearly (e.g., "Scheduled 8 labor hours for the 4-8pm rush; actual was 11 hours")
2. Explain what the traffic data reveals (e.g., "Saturday's 6-7pm saw 2x normal transaction velocity; we had no visibility into that")
3. Name the root cause (e.g., "Forecast assumed steady velocity; didn't account for high school pickup traffic that hit 5:45-7pm")
4. Give ONE actionable fix (e.g., "Next Saturday: schedule +2 hours 5:45-7:30pm based on this observed pattern")

Input data (paste below):
- Scheduled labor:
- Actual labor:
- Traffic/transaction data:
- Notes:

Output: [Your debrief]
```

**Why this works:** The structure is specific. It doesn't let Claude hand you a generic "staffing is important" paragraph. It forces him to SEE the miss (the numbers), EXPLAIN it (the why), and FIX it (the action). This is how you turn forecast data into operational change. The key line is "ONE concrete change" — that constraint forces Claude to avoid vague recommendations and make a call. You're training Claude to think like a GM, not a chatbot.

---

## 3. Use Case Spotlight

**The CrunchTime P&L Cleanup Workflow**

You pull a P&L export from CrunchTime. It's a mess: 47 line items, some labeled "Miscellaneous Labor," some missing category names, formula cells that won't copy, numbers that don't add up to your till reconciliation. You paste it into Claude with one question: *"Clean this up. Make a clear categorized summary. Flag anything that doesn't reconcile to my cash drawer balance."*

Claude outputs:
- A clean category-by-category breakdown (Labor, COGS, Overhead, Comps, etc.)
- Subtotals that actually add
- A clear flag: *"ALERT: Labor total is $427 higher than usual — verify whether this includes admin/office labor not in POS."*
- A second table: what's still unexplained or suspicious

**Before:** 20 minutes reading the PDF, copying numbers into a fresh spreadsheet, figuring out what "Misc Labor 4782" is.
**After:** 30 seconds pasting, 2 minutes reading the clean output, and you actually know what the weird number is.

This is not a demo. This is how you turn vendor reports into usable intelligence. Claude reads the numbers you can't, flags the contradictions you miss, and saves you the grunt work so you can focus on the actual problem (is our food cost really up, or did the export include a supply donation?).

---

## 4. Gotcha of the Week

**Claude Will Confidently Invent Dates**

You ask: *"When is the next holiday after Labor Day 2026?"*

Claude, if uncertain, might say: *"The next major federal holiday after Labor Day 2026 is Thanksgiving on November 28, 2026."*

This sounds confident. It is wrong. Thanksgiving 2026 is November 26, not 28. Claude didn't know. Claude guessed. And because it guessed with confidence, you'll write it on the schedule, and you'll be off by two days.

**The fix:** Never trust Claude's date math without verifying it yourself. Not because Claude is stupid. Because dates are a domain where being confidently wrong is worse than being silent. If you ask for dates, ask Claude to show its work: *"What day of the week is November 26, 2026? Count forward from today to verify."* The moment Claude has to show work, it's slower and more honest. That friction is the point.

---

## 5. New Tool Worth Trying

**Claude Projects with an Uploaded SOP**

Here's a 5-minute experiment:

1. Open claude.ai
2. Click **"+ New Project"** (top left)
3. Name it **"FG2065 SOP Library"**
4. Click **"Upload Files"** and grab one SOP from your Five Guys docs (e.g., opening checklist, secret shop debrief format, food safety checklist)
5. Ask Claude: *"Summarize this SOP. What are the three things that get missed most often? How would you rewrite step 4 to be clearer?"*
6. Follow-up: *"Turn this into a one-page quick reference for staff."*

**What happens:** Claude reads the SOP once, keeps it in memory for the entire project, and lets you build on it with follow-up questions. No copy-pasting the same document over and over.

**Why try it:** This is how you turn a wall of old documentation into a tool that actually improves execution. In 5 minutes, you'll see whether Claude can see the gaps in your own process.

---

## 6. AI in the Wild — Restaurant Relevant

**The Scheduling Pain is Real — And Nobody's Solved It Yet**

Nation's Restaurant News published a piece this week titled: **"We know exactly when the rush hits — why don't we know who'll be there to handle it?"**

The problem is simple: restaurants have POS data (exact transaction counts hour by hour, day by day, location by location). They have labor history (who was scheduled, who actually showed up, what the labor cost was). But they don't connect them. Most scheduling tools still ask managers to guess. No tool ingests actual traffic patterns and says: *"Saturday at 5:45pm you need 11 people, not 8."*

Bobby, you're already doing this manually with Teamworx + your P&L. The fact that this is *still* a pain point for chains with $100M in revenue tells you: there's a real product gap. And it tells you something about your own setup — you're ahead of the industry on this problem.

---

## 7. Skill Up — Do This Today

**Your 10-Minute Exercise: The Shift Summary Prompt**

Open Claude right now. Paste in this prompt:

```
I'm a Five Guys GM. At the end of my shift, I want Claude to help me write a 4-sentence debrief for my DM and the next GM.

I have these data points:
- Sales target: $1,200. Actual: $1,087.
- Labor scheduled: 8 hours. Labor actual: 9.2 hours.
- Incidents: one delivery was 35 minutes (customer complaint), one card reader went down 2-4pm.
- Staffing: called Bri to come in early (3pm instead of 5pm) due to unexpected volume 2-4pm.

Write a shift summary that:
1. States the miss (sales, labor variance)
2. Explains what happened
3. Flags the operational issue (the reader downtime? The forecast miss?)
4. Suggests ONE thing for tomorrow

Make it tight. One paragraph. Actionable.
```

Look at what Claude outputs. Notice whether it actually uses the data or hand-waves past it. Notice whether it gives you something you'd actually paste into a Slack message to your DM.

**Your next-session question for me:** Did Claude's debrief match what you'd actually write, or did it feel like the generic version of your shift?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
