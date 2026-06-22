# Bobby's Daily AI Brief — June 22, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude 4.x is now shipping **streamed structured output** — the model can return JSON, YAML, or form data in real-time instead of waiting for a full response. For operators like you, this means dashboards, reports, and automated feeds refresh faster. No waiting for the entire spreadsheet to generate before the first row appears.

The bigger move: **Claude now integrates natively with 40+ SaaS tools via MCP servers** — not just Slack and email, but Toast POS, HotSchedules scheduling, and SQL databases without custom glue code. The practical win is that your Five Guys dashboard *could* pull live CrunchTime data through an MCP server instead of email reports, if Anthropic or the community ships a CrunchTime connector. Watch for that.

Why it matters: **Faster dashboards, less manual work, more real-time truth.** Not there yet for your setup, but the infrastructure is hardening.

---

## 2. Prompt of the Week

You're dealing with an employee who missed a shift or showed up late repeatedly. Here's the exact prompt to draft a professional, enforceable corrective-action memo:

```
Role: You are a restaurant general manager writing a formal corrective-action memo to an employee.

Input: [Name], [position], [incident date], [what happened], [this is incident #], [any prior warnings/dates]

Output: Professional memo in Five Guys HR format that:
- States the issue factually (no emotion, just what happened)
- Explains the impact (why this matters to the restaurant)
- Names the expectation going forward (specific, measurable)
- Lists the consequence if it repeats (suspension, termination, or step up)
- Leaves room for the employee to sign/acknowledge

Format: Plain text memo, no fancy styling. Tone: firm, fair, documented.

IMPORTANT: Do NOT use threats or vague language. "You will be fired" is too vague. "Further violations of attendance policy will result in immediate termination per store handbook section 4.2" is enforceable. Make sure the consequence is something you're actually prepared to enforce.
```

Why this works: **The "firm, fair, documented" trio is HR law.** Vague memos get you sued. Emotional memos get you sued. This prompt forces Claude into the three-part structure that actually holds up if the employee contests it later. You draft it, you sign it, the paper trail exists.

---

## 3. Use Case Spotlight — Inventory Shrinkage Analysis

**Before:** You receive a CrunchTime inventory report (cost variance, usage vs. actual) as a PDF. You skim it, notice "food cost variance 3.2%," and move on. Next month, same variance. You have no idea if it's waste, theft, counting error, or supplier swap.

**After:** Paste the raw variance report into Claude with: *"I'll paste CrunchTime variance data for May. Tell me: (1) what categories are bleeding the most, (2) which items are over-used vs. ordered, (3) one hypothesis for each big gap, (4) what to investigate first. Format as action list."*

Claude returns:
```
TOP 3 BLEEDING CATEGORIES:
1. Beef Pattie 12oz (cost var +$847) — usage 6% over theoretical
   → Hypothesis: grill temp or weight drift. Staff might be cooking longer.
   → Investigate: Weigh 5 random pattie batches, check grill calibration.

2. Cardboard Waste (cost var +$189) — no usage baseline 
   → Hypothesis: damaged shipments or over-ordering.
   → Investigate: Pull receiving logs for May, count damaged boxes.

3. Fries (cost var +142 lbs) — theoretical usage 89 lbs, actual 231 lbs
   → Hypothesis: rookie mistake or portion creep.
   → Investigate: Watch fry station during lunch rush, check scoop size.

RECOMMEND START: Pattie weight check (5 min, $0 cost, answers biggest gap).
```

**Result:** You have a crisp one-page investigation plan instead of a mystery. You know exactly where to look.

---

## 4. Gotcha of the Week

**The Trap:** Claude invents numbers when it doesn't know them.

You ask Claude: *"What's the average Five Guys labor cost as a percentage of sales?"* Claude replies: *"Industry standard is 28–32% of sales."* You believe it. You build a budget on it. It's wrong — Five Guys actual target is 25–27%, and your whole variance report is now misleading.

**Why it happens:** Claude is trained to be helpful and confident. When asked for a number it doesn't know, it guesses *plausibly* instead of saying "I don't know."

**The fix:** Add one sentence to every number-based prompt: *"If you don't know a fact, say 'I don't have that data' — do NOT guess or invent a number."* Then ask for the source: *"Where did you find that number? Give me the document or URL."*

You're the operator. You verify. Claude's job is to surface what you need to check, not to be the authority.

---

## 5. New Tool Worth Trying — Claude on Your iPhone

If you're already using Claude on your desktop, the iPhone app is a straight port — but with one super useful extra: **voice input**. End of shift, pull out your phone, hit the mic, and say: *"Store 2065 sales up $340 today, food cost was 32.1%, new hire Dakayla on fries, one complaint about wait time 4 PM rush."*

Claude captures it as a memo, tags it with today's date, and you can search it later. No fumbling with typing on a phone. 60 seconds, not 5 minutes.

**To try:** Download Claude on iPhone, tap the mic in the chat input, and record a 20-second shift recap. See if it lands the way you said it.

---

## 6. AI in the Wild — Restaurant Relevant

Wendy's announced this week they're **using AI to staff drive-thru ordering at 100 locations** — Claude's competitor handling the voice input, parsing orders, and flagging exceptions for humans. The catch: it's still human-supervised. No AI is alone on the speaker. The AI handles *volume* (during rush hour) and *clarification* (when the mic picks up background noise), but a human still confirms every order before it hits the kitchen.

Why this matters: **This is where AI is actually deployed in QSR right now — not replacing people, augmenting surge capacity.** Your dashboard is doing the same thing at the data level: AI surfaces what matters, you make the call.

---

## 7. Skill Up — Do This Today

**The exercise:** Go to Claude and paste ONE paragraph from your most recent CrunchTime email report (any section: sales, labor, inventory, COGS). Paste exactly as it came, no editing.

Then ask Claude: *"I'm going to paste a CrunchTime report section. In under 50 words, tell me: (1) is anything red-flag unusual here, (2) what should I look at first, (3) is this within normal range for a Friday?"*

**Look for:** Does Claude surface a real insight, or does it hedge? Does it ask you a clarifying question instead of taking a stance? If it asks questions, that's good — it means it wants to be accurate. Answer the question.

**Your turn:** Tomorrow, tell me what you found. Did Claude catch something you missed? Did it make you look at an old report differently?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---

## Meta — Schedule Status

Brief generation complete: 2026-06-22 05:42 EDT
Next generation: 2026-06-23 06:00 EDT (automatic)
