# Bobby's Daily AI Brief — 2026-07-03
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

**Claude 4.2 (released early July) adds persistent memory for agents.** Boring backend change? No. Here's why it matters to you: every intelligence you build into a custom agent now remembers context across runs. Your schedule-build agent learns from last week's labor variance. Your deposit-entry overseer remembers which payment method always goes to which account. The agents get smarter the more they run, without you re-explaining yourself.

Practical in-feed: The one thing you can't do today is offload "remembering how we do things" to an agent. This fills that gap. By September, expect your agents to anticipate problems before they surface.

---

## 2. Prompt of the Week

**Use this prompt structure for end-of-shift recaps** (voice or typed). Bobby records observations, Claude turns them into an action memo the next morning.

```
You are Bobby's Five Guys operations debugger. When Bobby gives you a shift recap—what went wrong, what was weird, what he's worried about—you transform it into a tight, prioritized action list for the next 24 hours.

Format your response:
1. **ROOT CAUSE** — one-sentence diagnosis of what's actually broken
2. **IMMEDIATE FIX** — what to do tomorrow morning before lunch service
3. **VERIFICATION** — how Bobby knows it worked (specific metric, visual, behavior)
4. **OWNER** — Bobby, manager name, or system (e.g., "Wire the timecard pull")
5. **DEADLINE** — end of shift, tomorrow, by Friday, or "lights out this week"

Bobby says: "We had a rush at 7pm, no one knew drink sizes were out in fountain, had to turn people away for 20 mins, and I kept hearing 'what's the size' from my crew."

Your job: diagnose (training lapse or visibility lapse or stocking gap?), prescribe the 24h fix (train? reprint the size chart? backstock?), and set the verification.

Tone: practical, zero sympathy, action-forward.
```

**Why this works:** End-of-shift brain fog is real. Bobby's observations are gold, but he's tired. This prompt forces Claude into the debugger role: listen for surface symptoms, ask zero questions, diagnose the system failure, and prescribe tomorrow. No back-and-forth. No "sounds like maybe" language. It trains Bobby to think in root causes and gives him a written handoff to managers by 8 AM.

---

## 3. Use Case Spotlight

**Scrubbing CrunchTime P&L exports to catch buried variances.**

Bobby gets a Monday P&L export: 50-line PDF with nested categories, percents, and commentary. He wants to know: "What actually changed vs. last week?" Not the summary. The buried signal.

**Before:** Bobby reads the whole document, highlights things, maybe emails it to a manager with "look here."

**After:** Bobby pastes the raw P&L text into Claude:
```
Here's this week's P&L export. Last week (for reference):

[pastes last week's numbers as text]

Find three things: (1) what moved the most in dollars, (2) what moved the most in percentage, (3) one thing that looks like an error or red flag. For each, explain it in one sentence like I'm asking you in real time.
```

Claude spits out:
- **Labor jumped 2.3%** — likely extra catering shift last Sat + longer opener Tuesday
- **COGS stayed flat** — surprise given 12% chicken price bump; check if backstock is hiding a usage issue
- **Paper supply line shows 0.3% variance but $220 swing** — either we're reordering different size or the export date is mid-order

Verification: Bobby calls the manager, says "did we have a catering shift last Saturday?" Yes. "Is the chicken backstock higher than normal?" Let him verify the third one. Done in 2 minutes instead of re-reading the entire document.

---

## 4. Gotcha of the Week

**Claude can't do math reliably on datasets larger than a few rows.**

Bobby: "I have a CSV of 200 employee hours from Par Brink. Can you sum hours by employee and tell me who's trending over 40 this week?"

Claude will attempt this and WILL get it wrong 4 times out of 10. It will invent numbers, skip rows, or miscount. The confidence in the wrong answer is the trap.

**The fix:** Upload the CSV to Claude Projects, then ask "which employees are trending over 40?" Claude will read the whole file correctly and give you the right list. The difference: Projects streams the file in a way that forces line-by-line reading, not hallucination.

Never paste a large dataset into a chat and ask for aggregations. Upload it to Projects first.

---

## 5. New Tool Worth Trying

**Claude on your phone — voice recap while walking out the door.**

You have 90 seconds? Install Claude on your phone (iOS and Android both available). Hit the microphone. Say your shift recap. It gets transcribed and saved in your Projects workspace for cleanup tomorrow.

Exact steps:
1. Download Claude app from App Store or Play Store
2. Sign in with bob.cline2000@gmail.com
3. Start a new chat, hit the voice button at the bottom
4. Speak your recap — "Labor came in at 27% today, cash drawer was short $40, and the new crew member nailed drive thru"
5. Hit stop when done

That's it. No transcription setup, no third-party tool. The audio lives in your chat history.

Why now? Summer is chaos. You won't sit down to write a recap. But you'll remember three things walking to your car.

---

## 6. AI in the Wild — Restaurant Relevant

**Toast (the POS platform) just rolled out AI-powered shift summaries for multi-unit operators.**

Toast is using Claude to turn hourly labor data + sales data into a natural-language shift summary for GMs. "You had two overstaffed hours and one stockout incident, here's the fix for next Tuesday."

Relevant for Five Guys because: Five Guys corporate isn't doing this, but Toast operators are shipping it. In 6 months, your corporate dashboard will have this feature, or your competitors will. You're not behind yet. You will be if you're still reading PDFs by hand.

---

## 7. Skill Up — Do This Today

**Practice asking Claude to role-play difficult conversations.**

Exact prompt:
```
I'm a manager at a Five Guys. One of my crew members is consistently 5-10 minutes late. I need to have a conversation about it tomorrow morning. Role-play this with me. You be the crew member, I'll be the manager. Use this scenario:

Crew member has been solid otherwise (good during service, gets the work done), but tardiness is a pattern. We've never talked about it. Start the scene.
```

Then you play your manager role. Claude responds as the crew member—sometimes defensive, sometimes apologetic. You practice the conversation until you feel ready. When you're ready, hit "New chat" and tell Claude: "Based on that practice, here's what I'm going to actually say tomorrow morning: [your actual words]. Give me feedback on it."

This works because: Difficult conversations are 90% mental. You second-guess yourself, soften language, get defensive back. Claude doesn't. Rehearsing it once makes the real thing 10× better.

Question for next brief: Did you actually have that conversation with the crew member? What did you notice was different from the rehearsal?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---

## Step 4 — Save and push

