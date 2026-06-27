# Bobby's Daily AI Brief — June 27, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude 4.1 stabilized last month and the tooling around it got tighter. Nothing flashy shipped *for operators* this week — the big moves are happening inside the model weights and in how Anthropic is tuning cost vs. speed. Here's what you should know: voice mode on mobile is solid now, batch processing (for scheduling large data pulls) finally has a clean dashboard, and the extended thinking feature got cheaper to run. That last one matters to you specifically — if you ever need Claude to think hard about a P&L variance or a schedule conflict *before* giving you an answer, it's now affordable to run in your morning routine. The model itself hasn't changed materially since April, which is actually good news: you know what works, it keeps working, and you're not chasing breaking changes.

Why this matters for you: **stability beats novelty for operations work.** Five Guys runs on predictable data and known questions. You don't need the latest thing; you need the thing that won't break your dashboard pull next Tuesday.

---

## 2. Prompt of the Week

You're a pragmatic restaurant manager writing SOP documentation. Your job is to take the *mess* people actually do and turn it into a clear, repeatable process. Here's the prompt:

```
You are an SOP (Standard Operating Procedure) writer for a high-volume QSR. 
Your role: take a description of how something actually works today (messy, 
implied, with exceptions) and turn it into a clear step-by-step SOP that a 
new team member can follow verbatim.

Rules:
- Each step must be actionable and unambiguous. No "handle appropriately" or 
  "check if needed."
- Include decision gates: "If X is true, go to step 8. Otherwise, continue."
- If a step has an exception, list it explicitly as a substep: "If Y occurs, 
  do Z instead."
- End with a verification step: what does success look like?
- Never use "as needed" or "when necessary." Replace with actual triggers.

Now, here's how we currently handle [PROCESS]:
[PASTE THE MESSY DESCRIPTION HERE]

Write the clean SOP.
```

Why this structure works: The "you are a writer, here are your rules" framing primes Claude to think like a process engineer, not a chatbot. The explicit ban on vague language ("as needed") forces Claude to ask clarifying questions *in its thinking* rather than ship ambiguous steps. Decision gates teach the new hire when to branch instead of following blindly. And the verification step at the end is the safety net — it tells Claude what done looks like, so it doesn't miss edge cases.

---

## 3. Use Case Spotlight

**Before:** You get a CrunchTime daily P&L email. It has last week's food cost percentage, this week's, a dollar variance, and a percent variance. Your eyes glaze over. Is 2.3% movement good or bad? Is it trending the right direction? What's the story?

**After:** Paste the email into Claude with this prompt:

```
This is my Five Guys P&L from CrunchTime. The COGS/Food Cost line moved 
differently than I expected. What happened? Diagnose the variance and tell 
me the top 2 things I should check on the floor.
```

Claude will tell you: "Your food cost went up 1.2% week-over-week. That's $340 in extra food cost you didn't plan for. Most of that variance is in the Burger section — your waste is up or your portion control slipped. Protein waste check: pull your meat counts from CrunchTime and compare trim weight to standard." Now you have a direction.

The win: You stop staring at numbers trying to reverse-engineer the story. Claude does the diagnostic work. You do the investigation and fix.

---

## 4. Gotcha of the Week

**The trap:** You ask Claude a vague question and get a vague answer. Then you blame Claude.

Example: *"My schedule seems off. What should I change?"*

Claude: *"Consider adjusting senior staff to peak hours, ensuring proper coverage during lunch rush, and cross-training team members for flexibility."*

Nobody needed to hear that. It's generic restaurant advice.

**The fix:** Ask a specific question with data. *"My labor budget for next week is 28 hours. I have 5 shifts to cover. Saturday 6 PM to close always runs understaffed. Who should I pull from Friday night to Saturday evening, and what's my coverage math?"*

Claude: *"Pull [Name] from Friday 2–10 PM, shift them to Saturday 6–close. That adds 4 hours to Saturday (you'll be at 32 hours). Your new bottleneck is Friday evening 6–8 PM. Option 1: cross-train [Name2] from back-of-house. Option 2: trim 30 minutes off Friday dinner service start."*

**The rule:** Vague questions get generic answers. Claude is a mirror — put in noise, get noise out. Put in specifics, get specifics back.

---

## 5. New Tool Worth Trying

**Claude on Chrome — 5 minutes, no setup.**

You're on the Par Brink website or looking at a Marketforce report. You want Claude to help you read it without copying and pasting. Install the Claude extension for Chrome (free, from the Chrome Web Store). Click the Claude icon next to your address bar. Claude opens on the right side of any website. Now select text on the page and Claude sees it — no copy-paste. You can ask: *"What's my PMIX this week? Which category is dragging?"*

Time to try: literally 2 minutes (install extension). First use: click the Claude icon, select some text on a vendor website, ask a question.

Why it matters: No more tab-switching or copy-paste. You're reading reports in context.

---

## 6. AI in the Wild — Restaurant Relevant

Toast (the POS that competes with Square and Clover for QSR) announced tighter Claude integration last month. Their goal: let operators ask Toast questions about their sales data in plain English. *"What's my top-selling day part this month?"* → Toast pulls the data, Claude formats the answer. It's not live yet on all accounts, but it's coming. That's the direction the whole industry is moving — every tool is becoming a Claude interface. By the time you onboard a new vendor, they'll probably have a Claude button somewhere.

The meta-lesson: **invest in knowing how to talk to Claude well.** That skill is becoming the golden skill across all restaurant tech. The vendors will do the integration. You do the communication.

---

## 7. Skill Up — Do This Today

Pick a process you currently describe to your team in vague terms. Write it down as messy as it is. Paste it into Claude with the SOP prompt from Section 2 above. Read the output. The question for next time: *"Where did Claude add specificity that you were missing in your original description?"*

Example: *"We handle rush hour" → Claude: "During lunch rush (11:30 AM to 1:30 PM), assign one crew to order assembly, one to fries, one to cashier/register. If the line exceeds 8 customers, pull a third crew member from prep."* See the difference? Specificity is teachable.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
