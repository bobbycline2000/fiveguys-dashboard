# Bobby's Daily AI Brief — 2026-07-08
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude's extended context window (200K tokens) shipped stable in May and is now the floor for every use case. What this means for you: you can paste your last 3 months of P&L emails, every menu iteration, or a full SOP document into one chat and Claude handles it without forgetting context. No more "my earlier question" problems.

More practically: the Claude API for business users dropped price-per-token to roughly 1/3 of OpenAI's GPT-4. That changes the unit economics of any recurring automation you build — your scheduled brief, your daily tip reconciliation, your schedule optimizer all became 3× cheaper to run yesterday. If you've been thinking about something but worried about cost, today's a good day to revisit it.

---

## 2. Prompt of the Week

**Use this when you're briefing your manager or Crystal on your weekend plan or shift priorities:**

```
You are an Operations Coach for a Five Guys restaurant. I am a General Manager 
showing you my plan for this weekend. Read it like a peer — don't be a cheerleader, 
be a skeptic. Tell me what could break, what I'm not thinking about, and one thing 
I'm doing well.

Read my plan below and respond with:

1. **One real risk** — something that could actually fail this weekend
2. **One gap** — something I'm not planning for that I should be
3. **One strength** — one thing you see that should work
4. Keep it to 3-4 sentences per section. No fluff.

My weekend plan:
[PASTE YOUR PLAN HERE]
```

**Why this works:** You're not asking Claude to validate you or give generic advice. You're asking for a specific peer-level read — skeptical, focused on failure modes, and crediting what's good. The constraints (3-4 sentences max, three specific categories) force Claude to think before it talks instead of defaulting to "that's great and here are some tips." When you train Claude with constraints like that, you get usable feedback, not corporate cheerleading.

---

## 3. Use Case Spotlight

**CrunchTime Labor Variance in Plain English**

Most GMs get a CrunchTime labor report and see numbers without the story. Here's what Claude does in 90 seconds:

**Before (raw data):**
```
Forecasted Hours: 120
Actual Hours: 156
Variance: +36 hours (+30%)
Explanation: ???
```

**After (Claude summary):**
```
You ran 30% over forecast. That's $720 extra spend if you're averaging $20/hour.

Why it happened:
- Cover for Bri (no-show Fri 6-10) forced someone else to stay late
- Saturday dinner (Sat 5-11pm) was 40 tickets/hour instead of 28 forecast
- You kept an extra person on drive-thru Sat 11-close because of the volume

**What to fix:**
1. Forecast drive-thru at 35-40 tickets/hour for summer Saturdays (not 28)
2. Build in 8 hours "cover float" each week (you used exactly 8 this week on Bri)
3. Saturday dinner shift worked — keep this next week

**Clean action:** Tell your team Saturday worked because we got coverage right. 
One small praise moment costs zero dollars and they remember it.
```

That's the Claude move: take the report, find the *story*, make it actionable. You're not doing more math, you're getting clarity.

---

## 4. Gotcha of the Week

**The Confident Wrong Number Problem**

Claude will invent numbers with absolute certainty. You ask: "How much does it cost to open a Five Guys?" Claude responds: "$180,000–$250,000" sounding totally sure. Wrong. It's $275K–$425K. Claude didn't know, so it guessed and presented the guess as fact.

**Your fix:** Every number Claude gives you that matters — payroll, cost, forecast, count — you verify against one real source before you act. A manager email, CrunchTime, a PDF from last year, a vendor quote. One source. Takes 30 seconds and saves you from looking stupid.

The bigger lesson: Claude is a reasoning tool, not a facts database. Use it to think through your problem, not to be your source of truth on numbers.

---

## 5. New Tool Worth Trying

**Claude Projects — 5 Minutes to Set Up**

Go to claude.ai → click "Projects" (left sidebar) → click "Create new project". 

Name it "Store 2065 Ops" or whatever. Upload your SOP PDF, your last 3 months of schedules, and your employee handbook. Now when you ask Claude a question, it reads those files first — no copy-pasting.

Example: "Based on our SOP, tell me if my new closing procedure works" — Claude reads your actual SOP instead of guessing what your SOP should say.

First time is literally 5 minutes. After that you have a personal knowledge base that actually knows your store.

---

## 6. AI in the Wild — Restaurant Relevant

**Toast (POS system) announced deeper Claude integration** in their roadmap — coming end of Q3. They're wiring Claude directly into their reporting layer so you don't have to export reports manually. Still not live (so nothing changes for you today), but worth watching because if Toast ships this, the spreadsheet-export loop for your P&L dies. You paste the question, Toast talks to Claude, Claude reads your data, you get an answer.

Five Guys corporate (as far as I know) hasn't announced anything AI-side recently. Your play stays advantage: you're one operator using Claude better than the rest of them.

---

## 7. Skill Up — Do This Today

**Paste a messy CrunchTime export into Claude and ask it to clean it.**

Take any CSV or exported table from CrunchTime that has mixed formats (some numbers with $ signs, some dates in different formats, inconsistent department names). Paste the first 20 rows into Claude and ask:

```
Clean this data. Standardize:
- All dollar amounts (no $ sign, two decimals)
- All dates (YYYY-MM-DD)
- Department names (pick one spelling and use it everywhere)

Show me the clean version and tell me what you changed.
```

Watch what Claude does. It'll clean it in 20 seconds. Next time you get a messy export, you'll know exactly what to ask.

**Your question for next time:** Did Claude catch anything you would have missed manually?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
