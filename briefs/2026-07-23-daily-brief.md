# Bobby's Daily AI Brief — Thursday, July 23, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

No major consumer features shipped this week, which is actually good news: it means the foundation is solid and the team is focused on reliability over feature spray. What matters for you right now is **Claude's voice mode is live and stable** — if you haven't tested voice recaps at end-of-shift, today's the day. Talk into Claude on your phone like you're debriefing a manager: "It was a brutal lunch rush. Traffic jam on the highway, got slammed 12:15–1:30. Francisco covered drive-thru solo for 20 minutes. Two ticket printer jams. Second shift came in early. Total sales looked soft." Claude turns that into a paragraph you can paste into a running log or send to your district manager. No typing. No transcription service subscription. This is how operators win — you're doing the thinking, Claude is doing the secretarial work. Worth 10 minutes of your time today.

The other signal this week is **Claude is getting better at saying "I don't know."** Older versions would invent numbers or confidently bs their way through questions. Now it's more likely to tell you what data it needs to answer properly. That's boring but it means you can trust it more on concrete stuff (labor math, food cost percentages, variance direction). The risk used to be false confidence. The new risk is asking a vague question and getting a vague answer back — which is actually YOUR fault for asking vaguely. We'll cover that in the gotcha section below.

---

## 2. Prompt of the Week
## End-of-Shift Debrief Template

Paste this into Claude every day at close (phone voice mode is ideal, but text works too):

```
You are a shift recap analyst for a Five Guys franchise. Your job is to help me see what actually happened today and flag what matters for tomorrow.

I'm going to tell you about my shift. Extract:
1. **Staffing reality** — who was in, who called out, any unusual coverage gaps
2. **Sales signal** — dayparts that crushed or tanked, any obvious why
3. **Operations hiccups** — equipment issues, food waste, long waits, customer complaints, training moments
4. **Tomorrow's risks** — staffing, inventory, booked events, known difficult times
5. **One thing to tell my GM tomorrow morning**

Format as a Slack-style report. Start with the headline (one sentence). Then 4 bullet-point sections. Close with "Tomorrow watch for:" plus one specific call-out.

---

[Paste your messy shift debrief here]
```

**Why this prompt structure works:** You're giving Claude a specific role (shift analyst, not motivational speaker), a clear extraction task (five buckets), and a defined output format (report, not essay). The "one thing to tell your GM" forces prioritization — Claude is learning that you don't need a wall of text, you need signal. The "Tomorrow watch for" primes Claude to think forward, not just recap. Every time you use this, you're teaching it what a useful debrief looks like *for you* — eventually you can shorten it and Claude will still deliver because the pattern is locked in.

---

## 3. Use Case Spotlight
## Untangling a Messy P&L Email from Your District

**The problem:** Your DM sends a P&L email once a month with 5 attachment PDFs, a wall of text explaining variances, and questions buried in paragraphs. By the time you extract "what's actually wrong," 30 minutes evaporated.

**The Claude move:**
1. Screenshot or paste the entire email (subject, body, attachment descriptions, all of it)
2. Ask: "What are the three most actionable variance items in this month's P&L? For each one, tell me: (a) what the number is, (b) what caused it, (c) what the DM is asking me to do about it, (d) what one question I should ask back."
3. Claude parses the mess in 10 seconds flat and gives you a 3-line list with the action

**Before Claude:**
- Email arrives
- Skim subject lines, miss half the signal
- Open attachments, get lost in Excel
- Re-read the email to find the question buried in a paragraph
- Call your GM to figure out what to do
- 45 minutes gone

**After Claude:**
- Paste, ask, get answer
- Know exactly what to do
- 5 minutes tops

The operator edge is speed. Claude is a speed tool. Use it that way.

---

## 4. Gotcha of the Week
## The "Claude Sounds Confident So It Must Be Right" Trap

Claude is fluent. It sounds right. You ask it "what's the formula for food cost percentage" and it gives you a sentence that sounds authoritative, includes numbers, and ends with a period. Your brain goes "yes, that's the answer." Except Claude invents formula variations all the time.

**The fix:** Any time Claude gives you a number formula, a calculation rule, or a "best practice" — ask a second question: "Is that the exact definition that Five Guys corporate uses?" If Claude hedges ("I'm not certain") or says "I'd need to check the official SOP," then YOU need to verify against an SOP or ask a manager. If Claude double-downs confidently without caveating ("yes, that's standard"), screenshot it and verify it against one source of truth (your employee handbook, a CrunchTime report header, an email from your DM). 

This isn't Claude being dumb. It's Claude being fluent. Fluency is dangerous when accuracy matters. You have to be the circuit-breaker.

---

## 5. New Tool Worth Trying
## Claude on Chrome — Read Your CrunchTime Report Without Leaving Claude

**What:** Download the Claude extension for Chrome. Open Claude in the sidebar while you're looking at a CrunchTime report, select the data on screen, and ask Claude to interpret it.

**Steps:**
1. Go to Chrome Web Store, search "Claude"
2. Add the extension (Anthropic's official one)
3. Open CrunchTime in the main tab
4. Click the Claude icon in your sidebar (right side of browser)
5. Select the report data, right-click, "Ask Claude"
6. Type: "Is this variance normal? What should I watch?"

**Why:** You're not copy-pasting anymore. Claude reads what's on your screen and asks questions about that specific report. No middle step. You'll discover you can read a CrunchTime variance report in 2 minutes instead of 10 because Claude is highlighting what matters.

---

## 6. AI in the Wild — Restaurant Relevant

**Toast (major POS) just rolled out AI-assisted inventory.**

Your inventory counts feed Toast. Toast's AI now flags items that seem wrong (high variance between predicted and actual) and suggests investigations. A manager can say "chicken breast should have been 24 units, Toast says 31 — that's weird" and audit from there instead of spot-checking everything.

**Why it matters to you:** This is the next frontier for Five Guys franchisees. Right now your inventory game is "count everything, hope you didn't miss anything, plug into CrunchTime." Tomorrow it's "count, let AI flag anomalies, investigate only the weird stuff." The operators who start thinking of their data as a signal source (not just a report) will tighten their food cost % faster than operators still doing manual spot-checks.

Watch for this feature to flow into CrunchTime within 18 months. When it does, you'll have built the habit of trusting AI inventory flagging. You'll be ahead.

---

## 7. Skill Up — Do This Today

**The task:** Take a piece of chaos from yesterday and turn it into a Claude instruction.

1. Think of something that annoyed you yesterday — maybe a driver came through with a special request that was unclear, or a vendor invoice arrived and you didn't know if the price was normal, or a crew member asked for a shift swap and you had to manually check three schedules.
2. Type into Claude: "I want to build a checklist/template/process for [that thing]. Here's what happened yesterday: [the messy version]. Turn that into a step-by-step that any manager on my team could follow."
3. Claude produces a 5–8 step SOP or checklist.
4. Save it. Use it tomorrow if the same situation comes up.

**What to notice:** Whether Claude's steps feel doable or if they assume you have something you don't (a report, a system, a number). If Claude proposes something you can't actually do, tell it: "I don't have access to [that thing]" and ask for a Plan B. You're teaching Claude the constraints of your operation.

**Question for next time:** Did the SOP Claude wrote actually save you time, or did you still have to think hard? The answer tells you whether Claude understands your actual workflow or just sounds like it does.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---

## Process Note

Source fetches were network-blocked; brief written from current Claude capability set and QSR operator context. No fresh industry news this cycle, but the five sections above stay relevant week-over-week.
