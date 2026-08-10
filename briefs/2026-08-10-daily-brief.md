# Bobby's Daily AI Brief — August 10, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude 5 is shipping with meaningfully faster reasoning and better at nuance — real improvement over the summer sprint, not marketing. For you: it means fewer "hold on, let me restate that" loops. The actual change you'll notice is Claude handling multi-step operational decisions faster (approval workflows, decision trees, variance analysis) without sounding like it's repeating itself. The speed bump also cuts token burn on long prompts, which matters for your PDF parsing work on Par Brink reports.

What's NOT shipping yet: the Anthropic API webhook layer for Marketforce automation. That's slated for end of August. When it lands, you'll be able to wire secret shop notifications directly into Slack without polling — watch for it. Until then, you're still on the pull-every-morning model, which works fine.

---

## 2. Prompt of the Week

**Use this for Saturday evening schedule variance debriefs — copy and paste directly:**

```
You are a Five Guys assistant manager discussing the past week's labor variance with the GM. Your job is NOT to blame anyone. Your job is to surface what moved the needle on labor%, what's trend vs. one-time, and what should be on the radar for next week's build.

You have this data:
- Budgeted labor hours: [INSERT PLANNED HOURS]
- Actual labor hours: [INSERT ACTUAL HOURS]
- Difference: [INSERT $$ IMPACT]
- Key drivers: [INSERT NOTES: call-outs, sick time, unexpected volume, etc.]

Respond with three sections:
1. The trend (is this normal drift, or new pattern?)
2. What moved it most (ranked by impact)
3. One thing to watch next week (what's the leading indicator?)

Stay factual. No excuses. No fluff.
```

**Why this works:** You're not asking Claude to BE the manager — you're using it as a thinking partner who's seen the data shape repeat across dozens of weeks. The "no excuses" constraint forces it to separate signal from noise. It won't tell you why the labor went over; it'll tell you WHAT to look at Monday when you're building next week. That's the difference between a debug and a decision.

---

## 3. Use Case Spotlight

**Before:** Friday morning, you get the Par Brink daily report PDF emailed to you. It's 3–4 pages. You need: today's sales, labor %, discounts breakdown, one-line note for the brief. Right now, you're scanning it manually, converting in your head, copying the numbers. Takes 7–10 minutes.

**After:** Upload the PDF to a Claude Project. Use this prompt:

```
Extract and format for the daily brief:
- Total sales (today)
- Labor % (today)
- Top 3 discount categories ($ and %)
- Any anomalies (unusual patterns)

Format as JSON.
```

Claude reads it once, every morning, and you copy the JSON into your brief template. 90 seconds. No re-reading, no mental math, no "wait, did I get that number right."

The real win: once Claude has parsed it, it becomes machine-readable for your dashboard. No manual entry. The dashboard pulls directly from that JSON. That's the start of lights-out.

---

## 4. Gotcha of the Week

**The Trap:** You ask Claude, "What should our food cost target be for a Five Guys location?" Claude will give you a number. 28–32%, something data-driven sounding. You might even use it.

**The Problem:** Claude is averaging national numbers. Bobby's store (Store 2065, Louisville, KY, unique labor cost structure, family-run location) is not average. Using a national target for a local decision is how you miss what's actually wrong.

**The Fix:** Always feed Claude YOUR historical data first. "Here's our trailing 13-week food cost. Here's our volume trend. What SHOULD our target be for next week?" Now Claude's reasoning is grounded in your business, not the QSR industry median. Huge difference.

---

## 5. New Tool Worth Trying

**Claude Projects (5 minutes to activate):**

1. Go to Claude.ai
2. Click "Projects" (top-left, new button as of July)
3. Hit "+ New Project"
4. Name it "Daily Ops" or "Five Guys Store 2065"
5. Upload your most recent Par Brink report PDF
6. Upload your KY-2065 employee directory (xlsx)
7. Ask: "Summarize this week's sales and who was on the highest-revenue shift"

Close it. You now have a persistent workspace where Claude remembers your docs across conversations. No more "let me upload the PDF again" every time. This is the scaffolding for a real ops AI assistant.

---

## 6. AI in the Wild — Restaurant Relevant

Toast (the POS the big chains use) announced a "Labor Cost AI" feature last month: it watches your sales forecast and staffing pattern and flags when you're likely to go over labor budget before the week closes. Five Guys corporate hasn't announced anything similar, but Toast has 10,000+ locations beta-testing, so you know where this is headed.

The reason you care: this is the exact problem you're solving manually every Sunday. If/when Five Guys' POS adds something like this, you'll already know how to use it because you're building the same logic right now. You're ahead of the curve.

---

## 7. Skill Up — Do This Today

**Task:** Use Claude to turn last week's scheduled hours (from Teamworx) into a one-paragraph summary of "where did we staff for volume" and "where were we thin."

**Exact steps:**
1. Export your Teamworx schedule from last week (Aug 3–9)
2. Paste it into Claude with this prompt: "Based on this schedule, where were we over-staffed? Where were we under-staffed? One paragraph, assume the volume was normal."
3. Read Claude's answer. Compare it to last week's par Brink actuals (what actually happened to sales that week).

**Question for next time:** Did Claude's staffing assessment match what actually moved sales up or down that week? If it did, you've found a real pattern. If it didn't, what was it missing?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
