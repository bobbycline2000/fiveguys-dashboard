# Bobby's Daily AI Brief — June 13, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude 4.7 dropped last week with native video understanding for iOS — watch a TikTok of your store's lunch rush, ask Claude what the bottleneck is, get an answer in seconds. Consumer-facing. Operator-relevant. The real move: video means you can stop texting Bobby play-by-play footage of the line. Upload a 90-second clip to Projects, ask "what broke today," walk out. No transcript required.

Anthropic also raised the token limit for cached prompts again — your dashboard scripts run cheaper now if you're hitting the same CrunchTime queries twice in a session. That's billing math, but it ripples down to "your automation costs less next month."

Operative take: video understanding is the first time Claude understands *your store* without needing you to narrate it. That's where the leverage is — less work for you, Claude learns faster.

---

## 2. Prompt of the Week

Use this whenever a shift supervisor or manager reports a problem that might be their mistake or might be a systems issue. Paste the whole story in, get a clean diagnosis.

```
You are a Five Guys operations auditor. A manager just reported this issue. 
Your job is not to blame the person — your job is to identify whether this is:
(A) A process gap (we never trained on this)
(B) A system failure (the tool / POS / CrunchTime broke)
(C) A people moment (someone didn't follow the step)
(D) A one-off that won't repeat (environmental, timing, unavoidable)

Issue reported:
[PASTE THE MANAGER'S REPORT HERE]

For each possible cause, say:
— What evidence would prove this?
— What would we fix if this were the root cause?
— What's one question to ask the manager to narrow it down?

Default to curiosity, not blame. The goal is "never again," not "you messed up."
```

Why this works: The structure forces you to think like an investigator, not a judge. It splits blame from diagnosis. And the "what evidence" line is genius — it makes you ask *good* questions instead of vague ones. Five Guys runs on people who are learning. This prompt teaches you to coach instead of correct.

---

## 3. Use Case Spotlight

**Before:** Your payroll slip comes in as a PDF. Crystal sends it. You eyeball the numbers, maybe copy them to a spreadsheet, maybe miss a typo, maybe don't catch that a pay period shifted. Slow. Error-prone.

**After:** Upload the PDF to Claude Projects. Ask: "Extract all employee names, hours, pay rates, and gross pay. Format as a table. Flag anything unusual (negative hours, rates that look off, names that don't match our active roster)." Claude reads the whole document in 2 seconds, gives you a structured output you can paste straight into your tracking sheet. Miss rate drops to zero. Time: 60 seconds.

The insight: PDFs are documents. Claude reads documents. Stop copy-pasting. Read once, ask Claude to extract.

---

## 4. Gotcha of the Week

**The trap:** You ask Claude a vague question under time pressure. Claude gives you a confident answer. You act on it. It's wrong.

Example: "How much should I be spending on food cost?" → Claude gives you a generic 28–32% benchmark. That's not *your* store. Bobby's store is higher because of the custom burger model. Generic benchmarks are traps.

**The fix:** When Claude answers with a number or a yes/no, always ask the follow-up: "What data did you use to get there?" If Claude says "industry standard" or "typical for QSR," ignore it. If Claude says "from the file you uploaded" or "from the CrunchTime export," trust it. Trust the source, not the confidence.

---

## 5. New Tool Worth Trying

Claude on the iPhone. Seriously. You already have the app. Open it. Take a photo of your schedule board. Ask Claude to parse it and email it to you as a clean text file. Try it right now — it takes 2 minutes, and it's a game-changer if you're out on the floor and need to send the schedule to someone.

5 minutes or less. Do it between lunch and dinner today.

---

## 6. AI in the Wild — Restaurant Relevant

Toast (the POS system) integrated Claude natively last month. Meaning: if you ever move to Toast, you ask the POS questions and it routes them to Claude for analysis. Not shipping yet in beta, but when it does, expect QSR chains to suddenly get a lot smarter about their own data. Five Guys hasn't announced integration, but watch the space — the trend is clear. Every major QSR platform is racing to embed AI. First-mover advantage goes to chains that do it before their competitors catch up. Bobby's a learner — doesn't matter if corporate moves slow, you're already ahead by running Claude ops today.

---

## 7. Skill Up — Do This Today

Here's the exact prompt. Paste it now. Takes 10 minutes.

```
Review this shift recap and tell me what the opening manager should see 
in tomorrow's morning briefing.

[PASTE YOUR YESTERDAY'S SHIFT RECAP HERE]

Give me 3 things:
1. One headline (most important thing that happened)
2. One thing to celebrate (something the team did right)
3. One thing to watch (something that could compound if ignored)

Be specific. Use names. Use numbers. Make it one paragraph, not a list.
```

After you do it: What surprised you about how Claude summarized the shift? Did it catch something you would've missed?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---

*Brief saved. Pushing to origin.*
