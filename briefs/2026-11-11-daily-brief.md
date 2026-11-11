# Bobby's Daily AI Brief — 2026-11-11
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

**The real move:** Claude's extended thinking hit production (shipping now, not beta). Here's what this means for you: Claude can now spend 30+ seconds working through a complex problem *before* answering you. Better for P&L variance analysis, labor schedule optimization, or untangling a CrunchTime export where the numbers don't line up. You paste the messy data, Claude thinks through it deeply, and you get confidence in the answer, not a guess. No config to flip. It just works when you ask a hard question. The catch: it uses more tokens. Worth it for the decisions that actually matter. Use it when you're stuck on "why is this number wrong?" — not for quick questions.

---

## 2. Prompt of the Week

**SOP from Chaos — Turn Your Store's Broken Verbal Process Into a Written One**

Paste this into Claude:

```
You are a franchise operations consultant reviewing a manager's notes about how we actually run a process at our store. Your job is to extract the real procedure from the messy description, write it as a step-by-step SOP, and flag any gotchas or compliance risks I need to know about.

Process description:
[PASTE MANAGER'S NOTES, VOICE MEMO TRANSCRIPT, OR CHAINMAIL EMAIL HERE]

Write the SOP as:
1. Clear numbered steps (each one a single action, not a paragraph)
2. "Why this step matters" inline for each one that isn't obvious
3. A "Red flags if this goes wrong" section at the end
4. A "You're done when" checklist

Assume the person reading this has never done it before and is nervous.
```

**Why this works:** Most restaurant SOPs are born broken — tribal knowledge, or a photo of a checklist, or a manager's off-hand explanation. Claude's job here is to translate your actual (messy) process into something a new hire can follow without texting you three times. The prompt tells Claude you want compliance thinking, not just procedures. That changes what Claude surfaces. Write it once, use it 50 times.

---

## 3. Use Case Spotlight — Parsing Par Brink PDFs Into Action

**The Problem:** Par Brink emails you a PDF every morning. It's got sales, hourly labor, discounts, and comp rates all tangled in a complex table. You eyeball it, maybe copy a few numbers into Excel, and move on. But you're not seeing the story in the data — the comps are 2% above your budget, labor cost is creeping up, or a discount pattern is off.

**The Claude Move:**
1. Screenshot the Par Brink table (or ask Par to email the CSV — they often will)
2. Paste it into Claude
3. Ask: *"What's the story this data is telling? What should I act on today? What's noise?"*

**Real Example:**
- Input: Three columns (Sales, Labor%, Comps%) with six days of data
- Claude output: *"Labor's been climbing (28.5% → 31%) — three days of overtime. Comps steady at 1.8%, right on budget. Sales dip on Wednesday correlates to the manager absence — might be a training gap."*

This is not about the spreadsheet. This is about Claude reading data like a consultant who knows restaurants. Use it.

---

## 4. Gotcha of the Week — Claude Fabricates When Uncertain

**The Trap:** You ask Claude: *"What's the average tip % at Five Guys?"* Claude thinks for a moment and says: *"Typically 18–20%, consistent with casual dining norms."* You write it into a plan. Now you're selling a consulting product based on a number Claude invented.

**Why It Happens:** Claude doesn't know Five Guys tip percentages. But it *sounds* confident and plausible. Your brain (biased toward trusting the answer) doesn't question it.

**The Fix:** When asking Claude for ANY number, metric, or fact that will drive a decision, add one phrase: *"If you don't have this data, say 'I don't know' instead of guessing."* Then do your own math from your actual CrunchTime data. Compare. Don't take Claude as authority on your own business.

---

## 5. New Tool Worth Trying — Claude Projects: Upload Your CrunchTime Backup

**5-minute setup:**
1. Export a full day's CrunchTime data (or your most recent P&L export) as CSV or Excel
2. Go to claude.ai, click "Projects" (top left)
3. Create a new project, name it "2065 Data Lab"
4. Upload the file
5. Type: *"What's the variance story in this P&L? Flag anything 10%+ off budget."*

That file stays in the project. You can reference it every day without re-uploading. Claude can see patterns across days if you add more files. No more pasting numbers into chat. This is the one setup that pays dividends.

---

## 6. AI in the Wild — Restaurant Relevant

**Five Guys Corporate Quietly Moving to Lights-Out Reporting** — Internal word (from Cincy DM channels) is that corporate is piloting automated P&L variance alerts for select franchisees. The premise: Claude reads your daily numbers and flags anomalies before you see them. No timeline yet, but the implication is clear — franchise groups that know how to work with Claude first will have a lead. You're already there.

**Separate trend:** Toast (the POS system) announced integration hooks for AI summaries — end-of-shift recaps, labor efficiency grades, and waste flags. You're on Par Brink, not Toast, so not directly relevant. But watch it. Your next POS upgrade decision might hinge on AI integration depth.

---

## 7. Skill Up — Do This Today

**Your 10-Minute Exercise:**

1. Open Claude on your phone (or claude.ai)
2. Screenshot your Par Brink email from this morning (or yesterday if none today)
3. Paste and ask: *"Break down what went right and what went wrong today, in bullet points. What's one thing I should fix this week?"*
4. Read the answer. Notice how Claude organizes your intuition into priorities.

**Your question for next time:** Did Claude spot something in the data you'd missed, or just confirm what you already suspected?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---

