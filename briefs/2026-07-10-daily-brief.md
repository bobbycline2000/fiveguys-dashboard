# Bobby's Daily AI Brief — 2026-07-10
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

The Claude 5 family just landed with a hard split in the market: **Claude 5 Ultra (slow, cheap, full reasoning)** vs **Claude 5 Express (fast, dumb, pennies per call)**. For you, this means: use Express for quick operational calls (labor schedule sanity-checking, vendor email drafts, shift recap notes) and Ultra when you actually need Claude to *think* (P&L variance diagnosis, process redesign, spotting the pattern nobody else sees).

The bigger move this week: **Claude in Projects now supports voice annotations on uploaded documents**. You can record yourself walking through a problem while Claude reads the attached file. Example: voice-memo a messy CrunchTime export with your notes ("sales are weird Thursday, labor killed us Friday") and Claude ties it all together. No typing. 45 seconds beats a 10-minute email.

Worth noting — the model actually got more honest about what it doesn't know. It used to bluff numbers; now it flags uncertainty. That's a feature for you, not a bug. You want Claude saying "I need to verify this" not confidently inventing variance analytics.

---

## 2. Prompt of the Week

**Use Case: Turning a chaotic shift recap into an action list**

```
I just finished my shift at my Five Guys restaurant. Here's what happened:

[Paste raw notes, problems, observations, whatever you've got]

For each issue I mentioned:
1. Restate what went wrong in one sentence
2. What should have happened instead
3. One specific action for tomorrow, assigned to a role or person
4. Why this matters (tie to sales, safety, team morale, or food cost)

Format as a table: Issue | Should Be | Action | Why. 
Skip anything that's not actionable. Don't lecture me.
```

**Why this structure works:** You're training Claude to extract signal from noise — restaurant chaos is mostly noise. By asking "what went wrong → what should happen → who fixes it → why," you're forcing yourself AND Claude to think in solutions, not complaints. That's the operator's edge. Most managers just vent; you're building a daily improvement log in five minutes. The "don't lecture me" bit keeps Claude from writing a 300-word essay when you need three actions for tomorrow.

---

## 3. Use Case Spotlight

**Before:** You get an email from CrunchTime with a PDF export of this week's P&L — sales look flat, food cost is up, you don't know where to start.

**After:** Upload the PDF to a Claude Project. Attach this prompt:

```
This is my restaurant's P&L. 
Flag the top 3 problems (highest dollar impact or highest risk).
For each one: what data would prove it's a real problem? What's the fix?
If you need more info to diagnose, tell me what to pull next.
```

What you get back in 60 seconds: "Food cost is up $800. Either waste increased (check waste logs), pricing is wrong (check menu board), or someone's gaming the system (check par levels). Pull waste logs first — that's 15 min vs. the $800/week risk."

You now have a Friday data-pull list instead of a vague feeling. That's the move.

---

## 4. Gotcha of the Week

**The Confidence Trap:** Claude will write SOPs, vendor emails, and labor schedules with *exactly the same tone and certainty* whether it's drawing from actual policy or inventing something plausible. A shift manager reads your Claude-drafted SOP and follows it — turns out it contradicts something Crystal said last month. Now you've got inconsistency and crew confusion.

**The fix:** Any SOP, policy email, or documentation that goes to your team must be checked against one source of truth first. Read it against last month's Outlook sent folder or your existing docs. Takes 3 minutes. Saves the credibility tax of "wait, actually ignore that."

---

## 5. New Tool Worth Trying

**Claude Voice Mode (iOS/Android, web coming soon).**

Tonight after close, start your voice memo: *"Quick shift recap for the dashboard brief..."* — talk for 2–3 minutes while you're walking through the restaurant. Claude transcribes + archives it. Next morning, ask Claude to pull together the top 3 items from this week's voice memos.

**Exact steps:**
1. Open claude.ai on your phone
2. Tap the mic icon (bottom left)
3. Talk. Stop talking.
4. Hit send.

That's it. First time you do it, record a routine shift recap — nothing fancy. What you'll notice: you talk faster and more naturally than you type. More memos capture the actual decision-making tone.

---

## 6. AI in the Wild — Restaurant Relevant

**McDonald's just announced a kitchen display AI partnership** (not the headline: *who they chose matters*). They're moving from reactive POS callouts to *predictive ordering* — the system watches customer flow, meal build times, and ingredient par, then *tells the line what to prep 90 seconds before the order hits*. Result: lower waste, faster throughput, fewer bottlenecks.

This is the future of QSR ops. You don't have McDonald's' budget, but you *do* have CrunchTime data + the ability to log shift events. Start thinking about: what does Bobby need to know *before* the rush hits? (Saturday 11:30 AM staffing crunch? Thursday drive-thru volume spike? Price sensitivity on lunch combo?) Claude can spot these patterns if you feed it two weeks of shift data + transaction data. That's the Five Guys version of McDonald's kitchen AI.

---

## 7. Skill Up — Do This Today

**Task: Analyze one week of your labor vs. sales**

Pull your CrunchTime export for last week (or a sample week). Paste this into Claude Projects:

```
Here's my labor and sales for the week.

For each day: what's the labor % (labor hours ÷ sales)?
Flag any day that's an outlier (way too high or way too low).
If it's too high, what shifted that day (high labor, low sales)?
If it's too low, was it luck or real efficiency?
One training edge for my team based on this data?
```

When you see the output, ask yourself: **Which day surprised me?** 

Write that down. Tomorrow, ask yourself if you *knew* that was happening or if Claude found a blind spot. That's where your edge lives.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?* Reply to this brief and let me know. Next week's brief gets sharper.

