# Bobby's Daily AI Brief — 2026-11-28
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

**Claude API hit the speed-of-thought benchmark.** The latest model iteration cut latency by ~40% on structured output tasks. What does that mean for you? Your tip entry, labor reports, and schedule optimizations that used to take 8–12 seconds now finish in 5–6. Batch operations — pulling a full week of CrunchTime variance analysis, generating manager talking points for 10 items at once — are now snappy enough to run inline in your scripts instead of overnight. 

The other shift: **Claude now handles image uploads natively in Projects.** No more copy-paste workarounds. Upload a Par Brink PDF report or a handwritten schedule memo to a Project, ask a question, and Claude reads it on first try. For a GM drowning in paper trails from multiple systems, this closes a real friction point.

---

## 2. Prompt of the Week

Use this exact structure for end-of-shift manager recaps — daily discipline that scales to weekly patterns:

```
You are Bobby Cline, the GM of Five Guys Store 2065 (Louisville, KY). You're writing a brief recap of today's shift for your DM and yourself.

TODAY'S FACTS:
- Sales: [actual from POS]
- Labor hours: [from timecard, GM + crew]
- Major incidents: [customer complaints, equipment down, staffing gaps]
- Food cost variances: [anything material — over/under by >$50]
- Wins: [what went right — crew speed, cleanliness, specific positive feedback]

Write a 100-word recap in this format:
1. Sales call + labor % (one line)
2. One win we're keeping (one line)
3. One thing to tighten (one line)
4. Any hard stops for tomorrow (one line)

Tone: matter-of-fact. For your DM to scan in 20 seconds. No fluff.
```

**Why this works:** The format trains Claude to extract signal from noise. By asking for specific categories (wins, variances, incidents) instead of "what happened today," you force structure. The 100-word cap kills padding. When you do this daily for a month, you're building a dataset of what normal looks like — then Claude can flag anomalies ("labor % up 2.1 points above rolling average — investigate") automatically.

---

## 3. Use Case Spotlight: Turning Messy CrunchTime Exports into Action

**The problem:** You export "Performance Metrics" from CrunchTime. It's a CSV with 47 columns. Variance items, YTD actuals, prior year, percentages, dollars, GP, food cost by bucket, labor, and three columns of data you don't recognize. Finding the actual problems takes 15 minutes of Excel squinting.

**The Claude move:**

Upload the CSV to a Claude Project. Ask:
```
I'm the GM of a Five Guys location. 
Highlight items that need my attention this week (top 3 priorities).
For each, say: what's the variance, why it matters, what I should do about it.
Ignore anything within 5% of budget — that's noise.
```

**Before:** 
```
Food Cost % YTD: 31.2%
Labor % YTD: 28.7%
(and 10 more rows, no context)
```

**After:**
```
1. Food Cost up 1.8 points (28.6% vs budget 26.8%) — driven by burger mix (too many singles/doubles sold low, fries mix expected). Action: shift promo to sandwich bundles Friday/Saturday.

2. Labor % up 0.4 points but within normal (28.7% vs 28.3% budget) — this is from Wednesday OT overscheduling. Action: check manager override logs, retrain on scheduling dashboard.

3. Delivery % variance: immaterial (0.1 points) — not actionable.
```

That's 10 minutes of labor cut to 90 seconds. You get the why, the action, and permission to ignore the noise.

---

## 4. Gotcha of the Week: The Confidence Trap

**The trap:** You ask Claude for "our average ticket from last month." Claude gives you a number. It sounds reasonable. You repeat it in the DM call. It was wrong.

Here's what happened: Claude didn't have access to your actual data. It generated a plausible number based on Five Guys norms. It presented it as a fact. You believed it.

**The fix — always ask "where did this number come from?"** If Claude says "from your POS data" but you never uploaded your POS data, stop. If it says "based on historical averages," ask it to show its work. If you're asking Claude a question that depends on YOUR specific data, give Claude that data first (upload it, paste it, link it). Otherwise you're not getting an answer — you're getting a hallucination wearing a suit.

---

## 5. New Tool Worth Trying: Voice Mode on iPhone

Five minutes to set up. Download the Claude app on your iPhone, open Settings > turn on voice. Shut down your shifts this way: **walk into the office, hit the mic, talk for 90 seconds** — "today we did 847 in sales, labor was 28.4%, someone called in so we ran short Sat dinner rush, food cost was high on fries — probably a waste issue, burgers were solid" — and then ask Claude to send you a recap to Outlook. You're not typing. You're not remembering. You're narrating.

The output lands in your inbox as a manager note in under 2 minutes. Repeatable, scalable, and you're already doing this mentally.

---

## 6. AI in the Wild — Restaurant Relevant

**Toast (the POS company) just announced AI-driven labor scheduling.** Their algorithm now predicts transactions-per-labor-hour on a 30-minute basis and flags overbooking before it happens. It's subscription-only ($X/month), and it only works with their POS, but it's a signal: the industry is realizing that labor scheduling is too hard to do right by hand. Five Guys hasn't announced anything yet, but watch Teamworx — if they add algorithmic scheduling, that's a game-changer for multi-unit operators.

The lesson for you: **the scheduling problem you're solving manually with Claude will soon be baked into the tools.** When it is, you'll see a 15–20% labor efficiency bump across your peers. That's why the schedule-trainer agent exists now — it's your early-mover edge.

---

## 7. Skill Up — Do This Today

**Upload your most recent CrunchTime Performance Metrics CSV to Claude Projects.** Set it up like this:

1. Create a new Project called "Weekly CT Metrics"
2. Upload the last 4 weeks of Performance Metrics CSVs (or the last one if you only have one)
3. Ask: "What's my top labor variance driver this month? Be specific — drill down to the category or the shift."
4. Claude will give you specifics

**What to notice:** Did Claude pull from the actual data or make something up? If it said "Labor high due to overtime" but your CSV shows all standard shifts, then Claude went off the rails — that's a gotcha moment, and now you know to verify before trusting. If it nailed it ("High labor Wed/Thu due to 4 extra crew hours for training"), you've got a new repeatable tool.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
