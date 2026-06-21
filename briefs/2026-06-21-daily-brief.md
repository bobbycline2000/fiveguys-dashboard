# Bobby's Daily AI Brief — Sunday, June 21, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

No major features shipped this week that change your workflow. What matters: Claude's reliability on factual lookups (dates, math, names) is steadily improving but still not 100%. The real movement is in the ecosystem — more restaurants are wiring Claude into their POS systems and scheduling tools directly. This week Everytable announced they're scaling after a decade of cracking the affordable healthy food code. How did they do it? Automation. They're using AI to optimize kitchen workflows and supply chain. That's your North Star for what's possible. When Claude can talk directly to your CrunchTime data (which is in scope for your consulting business), you'll have the same lever they pulled.

---

## 2. Prompt of the Week

Copy this into Claude next time you need to handle a performance conversation with an underperforming crew member:

```
You are a restaurant general manager coaching a crew member who has shown a pattern of [specific behavior: tardiness/quality/attitude/attendance]. 

Your role:
- Be direct and factual. No corporate speak.
- Make it about impact, not intent.
- End with a clear expectation and next check-in date.
- Document what you said (I'll echo back what I wrote for you to save).

Background: [crew member name], role [position], has [number] instances of [behavior] in the last [timeframe]. Examples: [list 2-3 specific dates/situations].

Write the conversation opener I should use. Then write the follow-up email I send them after we talk, for my records.
```

Why this works: You're giving Claude a role (GM, not buddy), a constraint (facts only, clear expectations), and a job (document). This makes Claude avoid the "yes, and" trap where it agrees with everything and produces motivational-poster language instead of a real conversation. The closing line (echo back + save) turns it into a record you can actually use later.

---

## 3. Use Case Spotlight — Today's Topic: P&L Variance Analysis

**Before:** You get the monthly P&L from CrunchTime. It says food cost is 32% and labor is 28%. You see the variance but have no idea if it's "normal variance" or "actionable problem." You spend 2 hours digging through reports guessing.

**After:** Paste the P&L into Claude with this prompt:

```
I'm a five guys gm. Here's my P&L for [month]:
[paste the P&L data]

What jumped? What should I care about? Give me: (1) the top 2 variances from last month, (2) what causes each (from my perspective), (3) one thing I can change next week to move the needle.
```

You get back: "Labor is up 3% to 31%—likely weekend overtime. Food cost steady at 32%. One lever: next week's Wednesday-Thursday skeleton crew—shift those people to Thursday closing shift and you'll drop 2-3% labor." Actionable. 30 seconds. No guessing.

This is the difference between "I have data" and "I have insight."

---

## 4. Gotcha of the Week

**The Trap:** You paste sensitive business data (payroll, schedules, actual cash counts, employee names + SSNs) into Claude and assume it's private because you paid for Claude Pro.

**The Real:** Claude sees it. Claude doesn't store it (Anthropic has zero-retention logs for enterprise users, with conditions). But the moment you paste an unencrypted screenshot of your POS register or a PDF with SSNs, you've put it in motion. Other people on your network can screenshot, export, forward. Your crew can see the chat on a shared device.

**The Fix:** Never paste actual data when dummy data works. Instead of real names + phone numbers, use "Employee A, Employee B." Instead of "Safe count was $4,387.23," say "Safe count was [amount]." Let Claude work with structure, not secrets.

---

## 5. New Tool Worth Trying

**Voice Mode on iPhone** (if you have one). It takes 90 seconds to try:
1. Open Claude app on iPhone
2. Tap the microphone icon at the bottom
3. Say: "What are the top three things I should know about managing labor costs in a QSR"
4. Claude talks back to you. Hit Stop, read the transcript.

Why this matters for you: End-of-shift voice recaps become automatic. "Summarize my shift notes and flag anything I need to address tomorrow" takes 30 seconds instead of typing a memo. It's in beta but solid.

---

## 6. AI in the Wild — Restaurant Relevant

NRN's 2026 Top 500 dropped this week—the biggest restaurant chains in America, ranked. But the real story buried inside: **Everytable just announced a decade-long scaling run focused on affordable, healthy food in underserved areas.**

How are they doing it? Automation. Their kitchen workflows are increasingly AI-optimized. Supply chains are pre-dialed by an algorithm. Scheduling is predictive (they know Tuesday nights are lighter and staff accordingly before the shift). They didn't hire 100 people. They hired 10 and had Claude-like systems fill the rest of the gaps.

This is the roadmap for your consulting business: you're not selling "better spreadsheets." You're selling "now your GMs have a second brain that talks numbers." Everytable proved the market wants that.

---

## 7. Skill Up — Do This Today

Right now, take 10 minutes and do this:

**Step 1:** Open Claude and paste this prompt:

```
I'm a five guys GM. Tomorrow I have to write SOPs for two things: (1) safe opening procedure, (2) prep list for a monday before inventory. 

Write me the opener paragraph for EACH that I can paste into my training doc. Make them sound like me—clear, direct, no corporate language. Format as bullet-point process steps.
```

**Step 2:** Copy the output. Paste it into a Word doc or Google Doc. Edit it—cross out stuff that's wrong for your store, add the specifics that are missing.

**Step 3:** Read what you changed. Notice the pattern. Next time you need an SOP, you'll know what Claude gets right and what it misses.

**Tomorrow:** Ask yourself—did the SOPs I wrote get used? Did anyone ask questions about them? That tells you if the language landed.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---

**Brief saved for dashboard integration.**
