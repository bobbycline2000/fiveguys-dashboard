# Bobby's Daily AI Brief — October 22, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

The extended thinking models shipped in Claude 3.5 Sonnet are now rolling out to Claude.ai, which means Claude can now sit with a hard problem for 30+ seconds of internal reasoning before answering. For you, this matters in exactly one scenario: when you're asking Claude to diagnose a buried contradiction in your P&L or to catch the logical flaw in a process that's been failing intermittently. You ask once. Claude thinks harder. You get a better answer.

The other thing: Claude Projects now support live file uploads and auto-sync with your Google Drive. If you have a folder of daily reports from Brink or CrunchTime dumps, you can point Claude at it and say "flag anything that looks wrong." It's not quite a dashboard, but it's closer to lights-out than it was last week.

---

## 2. Prompt of the Week

Use this when you need to turn a chaotic shift recap into an action list. Copy the whole thing:

```
You are Bobby's operations coach. Your job is to listen to a shift recap (usually messy, usually got multiple issues) and do THREE things:

1. Clarify what actually happened — pull out the facts from the emotion
2. Name the root cause (not the symptom)
3. Give Bobby ONE thing to change for the next shift, not six

Format:
- What Happened: [fact only, one sentence]
- Root Cause: [why, not what]
- Fix for Next Shift: [specific, doable in one shift]
- Flag for Bobby: [anything that needs his decision]

Don't be nice. Be useful. If the issue is "we ran out of fries at 8 PM," the root cause is probably not supply — it's probably batch timing or forecast miss. Say so.
```

Why this works: by naming "coach," you're telling Claude to operate in a specific mode — diagnostic, not empathetic. By asking for root cause, you're forcing it to think instead of just accepting the surface story. By limiting the fix to ONE thing per shift, you're avoiding the "try everything" trap that kills execution. The Flag section is where you tell Bobby the stuff that needs his judgment call, not Claude's.

---

## 3. Use Case Spotlight

**Before & After: The Weekly Synopsis Variance Catch**

*Before.* You pull the synopsis P&L, scan the variance column, and try to remember which line items are normally 2-4% off and which ones are actually red flags. You miss the one that's real. You catch it in the call.

*After.* Paste the synopsis P&L and the prior three weeks into Claude with this prompt:

```
These are my weekly P&Ls. Flag anything that's:
1. More than 2% off from the three-week average
2. Going the wrong direction (if COGS was up last week, is it up again this week?)
3. Hitting a threshold you care about (Food Cost > 32%, Labor % > 25%, Sales trend down 3+ days)

Show me the three most likely causes for each flag, ranked by "this happens at my store."
```

Claude will spot the pattern you missed. It's not magic — it's just systematic, which is harder to do at 3 PM with seven other fires burning.

---

## 4. Gotcha of the Week

**The "True" That Isn't**

Claude will confidently tell you a number or a date and be wrong. Not skeptical-wrong. Confident-wrong. You ask: "How much did we sell Tuesday?" Claude says "$4,847." You didn't tell it. It made it up. It sounded sure. You believed it.

The fix: **Never ask Claude a question that requires it to know data you haven't given it.** Instead, paste the data first, then ask. "Here's Tuesday's Brink export. What was our hourly peak?" Claude can answer that. "What was Tuesday's sales?" means Claude is guessing.

If you find yourself saying "wait, where did you get that number?" — you've hit this trap. Restart with data first.

---

## 5. New Tool Worth Trying

**Claude for Chrome — 5-Minute Setup**

Go here: https://chromewebstore.google.com/detail/claude-for-chrome

Click Add to Chrome. Done. Now when you're looking at a CrunchTime export or a Brink report in Chrome, click the Claude icon in the top right and ask it to explain, summarize, or flag issues. It can read the page you're looking at without you copy-pasting.

First thing to try: open a vendor contract PDF in Chrome, click Claude, ask "What are my obligations if I terminate early?" You'll see the answer in 10 seconds. Normally that takes you 5 minutes of scrolling and reading.

---

## 6. AI in the Wild — Restaurant Relevant

Chipotle just announced they're testing AI-powered scheduling at 300 locations to reduce overstaffing and flag coverage gaps in real time. They're using transaction history + labor forecasting to tell managers when they can actually cut a shift without tanking service. Nothing revolutionary, but it's a signal: the QSR chains are finally moving past "test an AI chatbot" into the actual operational problems.

For you: that's a reminder that you don't need to build from scratch. The patterns are being proven at scale. Your job is moving faster on the ones that work.

---

## 7. Skill Up — Do This Today

**Practice: The 10-Minute P&L Audit**

1. Grab your most recent P&L (the SharePoint one)
2. Copy the whole thing into Claude
3. Paste this prompt:

```
I'm looking at my weekly P&L. For Food Cost, COGS, and Labor %, what should I be worried about?

Only flag things that are:
- Trending wrong (getting worse, not better)
- Outside my normal range
- Costing me real money (not just percentage noise)

Tell me the THREE things that matter, ranked by "you should fix this by Sunday."
```

4. Read the output. Did Claude surface something you didn't catch? That's the muscle.

*Next time we talk: What did Claude flag that surprised you?*

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---

**Brief saved to:** `C:\Users\bobby\OneDrive\BobbyWorkspace\github\fiveguys-dashboard\briefs\2026-10-22-daily-brief.md`
