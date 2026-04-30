# Bobby's Daily AI Brief — 2026-04-30
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

**The needle on Claude hasn't moved much this week — and that's actually good news.** Anthropic's focused on hardening what's already shipped instead of chasing feature churn. What this means for you: Claude's getting *faster* at the things you already use it for. Projects (your persistent workspace for a task or client) is still the power move if you're not using it — create one for the Five Guys playbook, the consulting business, whatever. It stays in memory across sessions without you having to re-paste context.

One small thing worth noting: Claude can now process audio files natively (voice memos, recordings), which means you could theoretically upload a shift recap or an employee feedback conversation and have Claude turn it into action items. If you're doing end-of-shift voice notes, that's a workflow unlock.

---

## 2. Prompt of the Week

Use this exact prompt when you need to draft a tricky employee conversation (hire, fire, PIP, promotion):

```
I'm an experienced restaurant manager preparing to have a difficult conversation with an employee. 

Situation: [describe the issue — performance, behavior, policy, attendance, etc.]

What I need: A 3-part conversation outline that's direct but respectful. The outline should include: (1) how I'll open (one sentence, no ambiguity), (2) the core message (what I'm asking them to understand or change), (3) what happens next if it doesn't improve, and (4) one way to close that leaves the door open if they want to engage.

Tone: Professional, measured, human. Not corporate-speak. Respect for their situation but clarity on expectations.

Output: Give me the outline and then give me the exact opening sentence I should use.
```

**Why this works:** Claude is trained on thousands of hard conversations — it knows what patterns reduce defensiveness and increase buy-in. The "exact opening sentence" constraint forces Claude to nail the tone rather than give you weasel language. You read that sentence first, and if it doesn't sound like you, you edit it. If it does, you go into the conversation knowing your first 15 seconds are solid.

---

## 3. Use Case Spotlight — Data Cleanup You Can Do in 5 Minutes

**The Problem:** You export sales data from CrunchTime, open it in Excel, and it's a mess. Dates are formatted three different ways, employee names are capitalized inconsistently, some columns have extra spaces, revenue shows up as text instead of numbers.

**The Fix:** Paste the raw export into Claude with this prompt:

```
I'm pasting a CrunchTime sales export. Clean it and return it as a properly formatted CSV ready to paste back into Excel. 

Rules:
- All dates in YYYY-MM-DD format
- All names Title Case (first letter capital, rest lowercase)
- Revenue as numbers only (no $ signs, no commas)
- Remove leading/trailing spaces
- If a row is obviously corrupted or missing critical fields, note it in a comment row

[paste your data]
```

**Before:** 2 hours of manual fix-and-verify in Excel, plus you're making mistakes.  
**After:** 2 minutes, data is clean and you can use it immediately for analysis or reporting.

This works because Claude can see patterns humans miss when we're tired and clicking cells. One paste, one clean export, done.

---

## 4. Gotcha of the Week

**The Confidence Trap — Claude invented numbers and you believed them.**

You ask: "What was the average labor percentage across my four locations for Q1?"

Claude (confidently): "Based on typical QSR benchmarks, labor should be running 28-31% depending on volume. I'd estimate your average is around 29.5%."

**You hear:** A data-backed answer.  
**What actually happened:** Claude made up a number that sounds plausible because it's based on real industry data it learned during training.

**The fix:** Never ask Claude a question that requires it to *know* your specific data unless you've uploaded or pasted it first. If Claude doesn't have your actual numbers, it will hallucinate a confident-sounding answer. The confidence is indistinguishable from accuracy — that's the trap.

**Right way:** Export your Q1 labor data from CrunchTime, paste it into a prompt, ask Claude to *analyze* it. Now Claude is working with real numbers.

---

## 5. New Tool Worth Trying

**Claude for Chrome — installed and ready to go.**

If you haven't installed it yet: open Chrome, go to `chrome.google.com/webstore`, search "Claude for Chrome," click Add, and you're done. Zero config.

**What you can do today:**
- Highlight text on any website (a recipe, a competitor's menu, a vendor email) and ask Claude to help. Click the Claude icon in your Chrome toolbar.
- Upload a PDF from a vendor's site to Claude Projects without leaving the browser.
- Copy a messy contractor invoice and paste it into Claude to extract key info (cost, scope, timeline) formatted cleanly.

Takes 2 minutes to set up. Saves time on every spreadsheet and document import for the rest of your life.

---

## 6. AI in the Wild — Restaurant Relevant

**Toast (the POS platform) just announced native AI ordering assist for pickup/delivery orders.**

What it does: Toast's AI watches your past orders, learns which add-ons go together (extra sauce with wings, bacon on the burger), and suggests them to customers at checkout. Early reports from roll-out partners show a 6-8% increase in average ticket size with zero extra labor from you.

**Why it matters to you:** Toast isn't your system (you're on CrunchTime), but this is the trend. Every major restaurant platform is embedding AI recommendation engines. Five Guys hasn't announced anything yet, but when corporate adds this, the data feeding it will be pulled from *your* store's order history. Make sure your POS data is clean and consistent — that's the input these systems use.

---

## 7. Skill Up — Do This Today

**Build a "Shift Recap" prompt in Claude Projects.**

Create a new Project called "Shift Recap" and add this prompt:

```
I'm the General Manager of a Five Guys location. At the end of each shift, I'm going to paste:
1. Sales numbers (revenue, transactions, average ticket)
2. Labor (hours scheduled vs. actual, who called out)
3. Any customer complaints or incidents
4. Anything unusual or noteworthy

You will turn this into a short, actionable report:
- Traffic trend (up/down vs. yesterday, vs. last week)
- Labor efficiency (was I over or understaffed?)
- One thing that went right
- One thing to fix tomorrow

Keep it to 4 sentences max. Make it readable in 30 seconds.

[I'll paste data below each time]
```

**Save that Project. Tomorrow, at end-of-shift, paste your numbers, and Claude will give you a recap in 30 seconds.** Do this for 2 weeks. Look at the "one thing to fix tomorrow" section — patterns will emerge.

**Question for next time:** What's one insight from your recap that surprised you?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
