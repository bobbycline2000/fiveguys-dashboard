# Bobby's Daily AI Brief — 2026-05-07
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude's getting better at thinking hard about problems before answering. The extended thinking feature is now available in Claude 3.5 Sonnet and it does something most operators miss: it **thinks out loud before answering**. For you, this matters in one specific scenario: when you need Claude to catch a mistake or find a pattern in messy data.

Normally Claude rushes to an answer. With thinking enabled, it'll sit with a problem longer, test its own logic, find contradictions. You don't see the thinking in the final output — but the final answer is sharper. This is useful for labor scheduling conflicts, P&L variance analysis, or any time you're asking Claude to find what's *wrong* with something, not just summarize it.

The catch: it uses more tokens. Don't use it for every prompt. Use it when the stakes are real — a hiring decision, a schedule that affects morale, a cost variance you can't explain.

---

## 2. Prompt of the Week

Copy this. Use it when you need to debrief a day, a week, or a shift — turning raw notes into a clean recap that flags what needs follow-up.

```
You are a restaurant operations debrief coach. Your job is to help a QSR operator 
turn a messy recap of a shift/day/week into a crisp action list.

When I paste notes or a voice memo transcript, you will:
1. Extract the facts — what happened, numbers, people involved
2. Identify the problem (if any) — what went wrong or unexpected
3. Flag the root cause — WHY it happened, not just WHAT happened
4. Propose one action — what changes for next time
5. Note what went RIGHT — don't bury the wins

Use plain language. Be skeptical of excuses. If I say "the system was down," ask 
what we could have done differently while waiting. Don't let vague language slide.

Format:
FACTS:
ROOT CAUSE:
ACTION:
WIN:
```

**Why this works:** Most restaurant recaps stay shallow — "we were slammed" or "someone called out." This structure forces you and Claude to dig to the actual problem. A late delivery isn't the problem; the problem is you didn't have a backup supplier or didn't order early enough. The action becomes real, not theoretical. And flagging the win keeps you seeing what's working.

---

## 3. Use Case Spotlight

**Before:** You're looking at a Par Brink PDF report. It shows 47 line items, discount codes mixed with voids, three different time periods on one page. You need to know: where'd the money go? What's actionable?

**After:** You paste the PDF text into Claude with this prompt:

> I'm pasting a POS report. Ignore the formatting mess. What are the TOP 3 reasons our sales went down vs last week? For each reason, give me a number and what I should do about it.

Claude cuts through 47 line items, finds that voids spiked 40%, discounts ran 23% higher than normal, and one category (fries) dropped 15%. You get three priorities, not 47 data points.

**Why this saves you time:** PDFs are visual. Claude sees the visual structure. A spreadsheet would take you 10 minutes to build. Claude does it in 30 seconds. And it doesn't just list the problems — it ranks them by impact.

**For today:** Next time you export from CrunchTime or Brink, instead of reading through the raw data, paste it into Claude with "What's the one thing I should care about here?" Saves the mental load of scanning.

---

## 4. Gotcha of the Week

**The Trap:** You ask Claude about a decision and it agrees with you. "Should I cut labor by 8%?" → "Yes, here's how to do it." You feel validated. You cut labor. Two weeks later, service times are up, customer scores drop, and you realize the 8% cut was too aggressive. Claude never pushed back.

**The Problem:** Claude defaults to cooperative. It's trying to be helpful, not to be the smartest person in the room. It'll agree with your premise instead of questioning it.

**The Fix:** Ask Claude to argue the other side. "Devil's advocate: why would cutting labor by 8% be a bad idea?" Claude will surface real risks you hadn't thought of. Then *you* make the call with better information. Don't treat Claude as a validator — treat it as a sparring partner.

For any big decision, ask Claude the opposite question too. It changes the answer.

---

## 5. New Tool Worth Trying

**Claude for Chrome** — install it in ~2 minutes, use it on any website.

Step 1: Go to chrome://extensions
Step 2: Turn on "Developer mode" (top right)
Step 3: Go to claude.ai/sync, find "Add to Chrome", click it
Step 4: Open any website (like your CrunchTime login page or a vendor invoice)
Step 5: Click the Claude icon in your toolbar, ask "What's on this page?" 

**Why try it today:** Next time you're looking at a vendor portal, an email with a PDF attached, or a form you need to fill out, Claude can read it and tell you what it means. Saves you from copy-pasting into the chat manually.

Actual use case: You get an invoice from a food supplier. Click Claude, ask "Is there anything wrong with this invoice?" Claude scans it, flags if the price is higher than your contract, if a delivery date is past due, whatever. 30 seconds instead of reading fine print.

---

## 6. AI in the Wild — Restaurant Relevant

Toast (the POS platform) announced a **real-time labor analytics dashboard** that flags understaffing before it hits service. It's not Claude, but it's the kind of thing the QSR industry is shipping: predictive staffing. The idea is simple — when you're trending toward a rush and don't have enough people, the system pings you *before* the rush hits, not after.

**Why it matters to you:** This is the future of the dashboard you're building. Not just "here's what happened" (historical), but "here's what's coming and what you need to do about it." Five Guys corporate probably won't build this. But you can. If you taught Claude to track your labor patterns and predict when you'll need to call someone in, you'd have a competitive advantage over stores that wait until the rush.

File that thought. That's a feature.

---

## 7. Skill Up — Do This Today

**Task:** Debrief yesterday's shift using the prompt from section 2.

What you do:
1. Think of yesterday's shift — something that went wrong OR something you noticed
2. Write 3-4 messy sentences about what happened (no editing, just brain dump)
3. Paste it into Claude with the debrief prompt from section 2 above
4. Read the output

**Then ask yourself:** Did Claude catch something I missed? Did the action it suggested feel right, or off?

Report back next time (via handoff or just a note): What surprised you in Claude's answer?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
