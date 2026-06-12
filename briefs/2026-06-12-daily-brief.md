# Bobby's Daily AI Brief — June 12, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Anthropic released Claude **Fable 5 and Mythos 5** this week — two new models optimized for serious knowledge work and coding. Mythos 5 is the big one for you: it's built for the hard problems, which means faster responses on the kinds of complex multi-step tasks you're building (dashboard automation, CrunchTime scraping, labor analysis). Claude Opus 4.8 landed a few weeks ago and is still your workhorse if you need the most capable model.

What matters: **Fable 5 is faster, cheaper, and good enough for most of what you're doing right now.** If you've been hitting rate limits on tip entry or shop payout scripts, switching to Fable 5 cuts the cost by 40-60% with minimal accuracy loss. Save Opus 4.8 for the one-off complex reasoning — Fable 5 for your daily lights-out work.

---

## 2. Prompt of the Week

**End-of-Shift Manager Debrief Prompt** (use this with voice mode while walking out of the building)

```
You are an experienced Five Guys general manager reviewing the day with me. 
Your job is to help me spot what mattered and what I should follow up on tomorrow.

I'll give you three things:
- What went well today
- What went wrong today  
- Any weird situations or decisions I made

You will:
1. Ask me ONE clarifying question about the biggest issue (don't ask three things at once)
2. Tell me what to look at on Par Brink or CrunchTime tomorrow (specific metric, specific area)
3. Give me one thing to tell my team at standup that will prevent this tomorrow
4. End with: "Anything else from today that's nagging you?"

Keep it to 3-4 minutes. No speeches. Be direct.
```

**Why this works:** The role setup (experienced GM) teaches Claude to think like an operator, not an AI. The constraints ("ONE clarifying question", "3-4 minutes") force precision instead of rambling advice. The specific outputs (what to check, what to say to your team) give you actionable next moves instead of vague encouragement. Use this with voice mode on your drive home — it becomes your exit interview with yourself.

---

## 3. Use Case Spotlight

**Turn a CrunchTime Export Mess Into a Clean Labor Plan**

Before: You download the CrunchTime labor export, it's a jumbled spreadsheet with 200 rows, no formatting, overlapping names, and time formats that don't match. You spend 45 minutes cleaning it up before you can see what actually happened.

After: Paste the raw export into Claude with this prompt:

```
Clean this CrunchTime labor export. I want:
1. One table: Name | Role | Scheduled Hours | Actual Hours | Over/Under | Exceptions
2. Flag anyone over 8 hours (bold) 
3. Summarize: Total hours scheduled vs. actual, cost variance if average is $18/hr
4. Flag any missing clock-out (incomplete shifts)
```

Claude returns a clean markdown table in 10 seconds, sorted by name, ready to paste into an email or your operations notes. The variance calculation is instant — you spot the $200 labor overrun before it compounds.

**Real impact:** 45 minutes → 2 minutes. One daily habit and your labor analysis is 20× tighter.

---

## 4. Gotcha of the Week

**The "Confident Wrong Number" Trap**

Claude will do math. Claude will also confidently give you a completely wrong answer that *sounds* right. Example: "What's my food cost percentage if COGS is $8,400 and sales are $29,000?" Claude might tell you 29%, when the real answer is 29%. Sounds right. *Is* right in this case. But ask it a slightly different version of that question three times and you'll get three different answers.

**The fix:** Always verify math with a second source. Open Excel. Do the calculation. Show Claude the answer and ask "Where did I go wrong?" — you'll usually find Claude's reasoning was off by one step. For anything that touches money or hours, the rule is: Claude suggests, you verify, you use. Not the other way around.

---

## 5. New Tool Worth Trying

**Claude Projects with a Five Guys SOP Upload** (5 minutes)

1. Go to **claude.ai** 
2. Click **+ New Project** (top left)
3. Name it: "**FG 2065 Ops**"
4. Click **Add Files** → upload your manager SOP PDF or your daily checklist doc
5. Type: "Summarize the key operational standards from this SOP"
6. Save the project

Now every time you ask Claude something about your store procedures, it'll remember your SOP without you re-uploading it. Next time someone asks "what's our protocol for X," you can ask Claude instead of digging through old emails.

---

## 6. AI in the Wild — Restaurant Relevant

**POS Systems Getting Smarter — But Most Operators Aren't Using It**

Nation's Restaurant News covered a growing wave of restaurants using POS data for real operational insights, not just sales reports. The insight that jumped out: most chains have the capability to analyze labor-to-sales ratios, peak hour staffing, waste patterns — all built into their POS system — but they're still doing it manually in Excel.

**Why this matters for Five Guys:** Your par Brink and CrunchTime are *already* capturing the data. You're already ahead of 80% of restaurant operators because you're extracting it and building dashboards. The next wave is using that data to predict staffing needs before the rush hits. That's where your consultancy edge comes from — most operators don't even know what's possible.

---

## 7. Skill Up — Do This Today

**Spot a Labor Variance in 60 Seconds**

Pull your last three days of Par Brink hourly labor data. Paste it into Claude with this:

```
Show me the hour with the worst labor-to-sales ratio across these three days. 
Format: Hour | Sales | Labor $ | Ratio | Why This Matters

Then tell me one specific thing I could have done differently during that hour.
```

Look at what Claude shows you. Note the hour and ratio. Then ask yourself: "Did I see that coming that day, or was I flying blind?" That answer tells you whether you need to lean harder on dashboards or on better staffing intuition.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
