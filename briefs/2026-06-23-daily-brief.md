# Bobby's Daily AI Brief — June 23, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude's reasoning engine got faster and more reliable this month. Two things you care about: (1) When you paste a messy CrunchTime export or a stack of emails, Claude now extracts the actual numbers without hallucinating decimal places. (2) Claude can now hold longer operational contexts — a full 8-week P&L conversation where you're asking "what if we cut labor by 3%?" stays coherent for the whole session instead of forgetting the baseline halfway through.

One thing that doesn't matter for you yet: the API improvements that let developers build integrations. That's for later when we build out the lights-out pipeline. For now, the practical win is accuracy on the data you're already dumping into chat.

---

## 2. Prompt of the Week

**Manager Incident Debrief Template**

Paste this when you need to process something that went wrong on a shift — a customer complaint, a safety incident, a food quality issue, a team conflict. Send the answer straight to the person who needs to hear it.

\`\`\`
Role: You are a Five Guys operations manager writing a debrief email to [MANAGER NAME] about an incident that happened today.

Context:
- The incident: [DESCRIBE WHAT HAPPENED — WHO, WHEN, WHAT WENT WRONG]
- Your store: Store 2065, Louisville KY
- The team member(s) involved: [NAMES]
- Root cause (your best guess): [YOUR HYPOTHESIS]
- What you want from this debrief: [COACHING / DOCUMENTATION / CORRECTION / ACKNOWLEDGMENT?]

Tone: Direct. Professional. Respectful. Not punitive — this is about learning.

Write a 3-paragraph email:
1. What happened (factual, no emotion)
2. Why it probably happened + what we'll do differently next time
3. One specific thing this person can do to improve by Friday

Sign it from you. Make it something I'd actually send.
\`\`\`

**Why this works:** Claude's strength isn't in making you sound corporate — it's in forcing you to think in order (what happened → why → what's next). The role setup prevents him from being either too soft or too harsh. The constraint of "send it Friday" makes the action concrete instead of abstract. You'll notice Claude gives you one specific behavioral change instead of generic advice like "be more careful."

---

## 3. Use Case Spotlight: Excel Chaos to Operations Report

**The problem:** You get a CrunchTime labor export. It's 47 rows, mixed date formats, some names abbreviated, some full, columns in a random order, and you need to know: "Did we hit labor %" this week?

**Before (manual):** You spend 30 minutes reformatting in Excel, cross-checking names against the roster to make sure "J.Smith" is actually "John Smith," re-sorting by date, then manually calculating labor hours ÷ total hours.

**After (Claude):** Paste the export into a Claude Project. Ask: "Clean this up. Show me total hours by day, labor % by day, and flag any day that's more than 2% off the 28% target."

Output: A clean markdown table with the right dates, names resolved, calculation done, and a 2-line summary: "Tuesday and Wednesday hit target. Thursday was 31% — over by 3 points, probably due to shift add."

**Try it today:** Upload one CrunchTime export to a Claude Project (top of chat, "+" button). Ask Claude to clean it and calculate labor %. Takes 90 seconds. This is how you stop wasting time in Excel.

---

## 4. Gotcha of the Week

**The "Yes And" Problem**

You ask Claude: "Should I reduce portions to bring food cost down?"

Claude responds: "Yes, reducing portions could lower food cost. You could also implement portion control standards, train staff on consistency, audit suppliers for better pricing, and optimize your menu mix."

Now you're confused. Did he say yes or no? What should you actually do?

Here's what happened: Claude said yes (correct), then pivoted to selling you five other ideas (unhelpful). He does this because his training teaches him to be helpful by offering options. But that backfires when you need a single answer.

**The fix:** Add one line to your prompt: "If I ask you a yes/no question, answer YES or NO in the first sentence. Then explain why. Do not offer alternatives unless I ask for them."

Try it: Paste that line into any decision question and watch how much sharper his answers get.

---

## 5. New Tool Worth Trying

**Voice Mode for End-of-Shift Recaps**

Claude on the web now has voice input/output. After your shift ends, pull up Claude in Chrome (or the app), hit the mic button, and talk: "I just closed tonight. We had 8 labor hours over, food cost was wild, and there's an issue with the ice cream machine we need to address tomorrow."

Claude listens and transcribes. Then he asks clarifying questions out loud: "When you say 8 hours over, is that compared to the scheduled hours or to last Tuesday?" You answer verbally. Result: a text recap in your phone without typing a single word.

**Time to try:** 3 minutes. Go to Claude.ai, find the voice button (bottom left, microphone icon), tap it, and talk at your phone like you're texting a friend. That's it.

Why this matters: You can capture shift notes while you're doing close, not 30 minutes later when you've already forgotten half of it.

---

## 6. AI in the Wild — Restaurant Relevant

Toast (the POS system a lot of franchises use) quietly rolled out AI-powered labor forecasting last month. It watches your historical sales patterns and hour-by-hour traffic, then tells you: "Next Tuesday you'll probably need 1.5 more labor hours because your average cover count goes up 12% mid-afternoon."

Most operators are ignoring it. But the ones paying attention are using it to pre-schedule instead of calling people in at the last minute. For you, the takeaway: your POS data is sitting there waiting to power predictions. If Five Guys corporate ever connects your POS (Par Brink) to Claude, that's literally what we'd build first.

---

## 7. Skill Up — Do This Today

**Task: Turn a chaotic problem into a Claude-ready question**

Think of one recurring operational frustration (something you deal with 2+ times a week). Right now, just state it messily: "Food cost is bad" or "Scheduling conflicts keep happening" or "Customer complaints about order accuracy."

Paste it into Claude with this prompt:

\`\`\`
I'm trying to solve an operational problem. Here's how I'd describe it in my own words:

[PASTE YOUR MESSY DESCRIPTION]

Now help me reframe this as a specific, solvable question that I can use Claude to tackle. What data do I need? What exact metric should I measure? What would "solved" actually look like?
\`\`\`

Claude will come back with a crisp problem statement. Screenshot it and save it. That's your north star for the next two weeks.

**Example:** Messy input: "Labor is always too high." Claude reframes: "You want labor hours ÷ total sales (as %) to stay between 27–29%. Which days is it exceeding 30%, and what's the pattern?" Much better.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
