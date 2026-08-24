# Bobby's Daily AI Brief — 2026-08-24
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude 5.1 shipped in late July with two features worth your attention. First: **Projects with file memory**. Upload a PDF SOP, a spreadsheet, a CrunchTime export, or a full store manual—Claude remembers it between conversations without you re-pasting. Second: **Batch API for heavy lifting**. If you're processing 100 CrunchTime exports or analyzing 50 days of sales data overnight, batch mode runs them cheaper and faster. Both are live in claude.ai now.

The real win: Projects eliminate the "I have to paste this every single time" friction. Your Five Guys SOPs, employee handbook, cleaning checklist, P&L template—drop them once, use forever. For a franchise operator like you, this is the gap-closer between "Claude is helpful" and "Claude is part of how I run the store."

---

## 2. Prompt of the Week

**Use this for end-of-shift crew debriefs (text or voice):**

```
You are a shift debrief specialist for a Five Guys restaurant. Your job is to turn raw notes, observations, and half-thoughts into a clear, actionable summary. You will:

1. Extract the FACTS: sales, labor issues, equipment problems, customer incidents, supply shortages
2. Flag DECISIONS MADE: what did the shift lead decide, and was it the right call given the facts?
3. Surface PATTERNS: if this is the third shift in a row with X problem, call it out
4. Create ACTIONS for tomorrow: specific, named, one sentence each

Tone: straight, no fluff. If the shift was smooth, say so and move on. If there's a pattern brewing, name it.

---

[SHIFT DATA]
[paste crew notes, ticket times, labor hours, incidents, or voice transcript]
---

Now debrief this shift.
```

**Why this works:** The shift debrief prompt does four things well. It gives Claude a role (specialist, not generic helper), which tightens focus. It lists the OUTPUT FORMAT upfront so Claude knows you want facts + decisions + patterns + actions, not a summary of what happened. The "if there's a pattern brewing" line trains Claude to extrapolate—you get early warning, not just yesterday's data. And the tone instruction kills the corporate-speak. You get usable notes you can actually hand to a DM or GM.

---

## 3. Use Case Spotlight

**P&L Variance Troubleshooting — Before and After**

Before Claude: You pull yesterday's P&L, food cost is 31% (vs 28% target). You stare at it. You think "Did we over-order? Did a batch get wasted? Which item?" You email the DM vague concerns.

After Claude: You paste the P&L into a Project, add a note "Food cost is 31%, target 28%. What went wrong?", and Claude responds with:
- **Likely culprit**: Compare item-level COGS to actual usage. Fries and burger buns are running 40% over forecast (waste or shrink). Shake base is up 15%.
- **Second-order check**: Labor cost is also up 6%. Did an all-hands day or a training session eat margin?
- **Action**: Pull footage from the fryer station (if you have it) for 4–6 PM, audit bun counts, ask Chris if shake machine had a jam.

Claude doesn't know the truth, but it narrows WHERE to look from "the whole P&L" to "those two items and that window." You go from 30 minutes of guessing to 10 minutes of targeted investigation.

**The shift:** You stop asking "is my P&L wrong?" and start asking "where exactly did I slip?" Claude turns a black box into a debugging flowchart.

---

## 4. Gotcha of the Week

**The Confidence Trap**

Claude will invent numbers if you ask it to. Show Claude a June P&L and ask "What was May's food cost?", and Claude will either make up a plausible number (31.2%) or refuse cleanly. Most often, it leans confident. The fix: **Always say "If you don't know the number, don't guess. Say so." ** Then paste the actual data.

Example of what NOT to do:
- You: "What's our typical labor% in August?"
- Claude: "Based on Five Guys industry benchmarks, August typically runs 31-33%."
- You, later: "Claude said August is 33%, so we should be hitting that..."
- Reality: Your store is actually 27% in August. You just made a staffing decision off false data.

Real usage: You pull your own August data from CrunchTime, paste it, ask Claude to analyze *your* numbers. Claude works with facts.

---

## 5. New Tool Worth Trying

**Voice Mode for End-of-Day Recap**

If you have Claude on your iPhone (App Store: Claude by Anthropic), voice mode is live. Hit the mic button, talk for 30 seconds: "Shift was chaos, two call-outs, we ran out of patties by 7 PM, Katie coached a new hire, customer incident on the patio around 6." Claude transcribes, you hit send, Claude responds with a quick summary. No typing.

**Time to first value:** 2 minutes. Download the app, open Claude, hit the mic icon. Go.

No setup, no config. Pure friction reduction.

---

## 6. AI in the Wild — Restaurant Relevant

Toast (the POS platform Five Guys uses in some locations) announced in early August that it's shipping a **labor-forecasting AI layer** — takes your last 90 days of sales and labor data, feeds it through Claude, and spits out "You need 8 people on Friday, 5 on Tuesday, 6 on Wednesday." It's opt-in, reads directly from your Toast install, no manual export. Early adoption from Wingstop and Wing Street locations shows ~3–4% labor improvement (right-sizing, not cutting). Five Guys corporate hasn't pushed it yet, but if your location runs Toast (vs CrunchTime), ask about it.

---

## 7. Skill Up — Do This Today

**Practice the "bad input, good question" pattern.**

Task: Grab yesterday's Par Brink sales summary (if you have it) or any messy report that's hard to read. Here's what to paste to Claude:

```
This is my sales report, and it's formatted poorly. But look at it anyway and tell me three things:
1. What line item is growing fastest?
2. Where's the biggest variance from yesterday?
3. If I could only invest time fixing ONE problem, what should it be?

[PASTE THE REPORT]
```

Claude will work with it even if it's a mess, a PDF, or halfway through a thought. Then Claude tells you where to focus. The practice: Claude doesn't need perfect data—you just need a clear question.

**Your question for tomorrow:** What item jumped the most from Aug 22 to Aug 23?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---
