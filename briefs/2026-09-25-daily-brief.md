# Bobby's Daily AI Brief â€” 2026-09-25
*From the desk of your AI engineer â€” what matters today, nothing that doesn't.*

---

## 1. This Week in Claude â€” Plain English

Claude 5.1 is holding steady as the standard for operator-grade work â€” fast enough for real-time decision support, capable enough for multi-step workflows without hand-holding. The bigger news: Claude in Chrome has stabilized as the de facto scraping tool for operators who refuse to touch headless browsers. No new consumer features shipped this week, which is fine. You don't need new features; you need the ones you have to work reliably, and they do.

What actually matters: the prompt caching updates that shipped last month are still paying dividends in scheduled tasks. Your daily brief, dashboard pulls, and tip-entry flows run *faster* because Claude isn't re-parsing the same system context on every call. Less token burn. Faster callbacks. That's not excitement. That's compounding small wins.

---

## 2. Prompt of the Week

**Use this for your daily shift recap â€” voice memo to action items.**

Paste this into Claude (or Claude on iPhone via voice) at the end of your shift:

```
You are a restaurant operations analyst working for a Five Guys franchise. Your job is to convert a manager's raw voice memo or unstructured notes into a crisp, actionable handoff.

Input: [PASTE YOUR SHIFT NOTES HERE]

Output format â€” numbered sections, one sentence each:

**Immediate Actions (for closing manager or next shift):**
1. [Action] â€” [why this matters]
2. [Action] â€” [why this matters]

**Follow-ups (for tomorrow or next week):**
1. [Who] needs to [action] because [reason]. Deadline: [date]

**Data to track:**
- [Metric]: [observed value or concern]
- [Metric]: [observed value or concern]

**Decision needed:**
If any: [Decision] â€” [by whom], [by when]

**Pattern to flag:**
If any: [What's happening repeatedly] â€” suggest [fix]

Keep it tight. No filler. One sentence per item.
```

**Why this works:** You're teaching Claude to think like an operations person, not a chatbot. The constraint "one sentence per item" forces Claude to distill instead of elaborate. The "why this matters" tag prevents Claude from suggesting actions you don't care about. And the "Decision needed" section stops ambiguous handoffs â€” if Claude spots something that needs a call, it says who and by when. By Monday morning, your handoffs will be tighter and less noise.

---

## 3. Use Case Spotlight

**Before:** You've got a CrunchTime labor export (a mess of columns, last 8 weeks of data). You manually scan for "weeks where we ran over budget" and eyeball the causes. Takes 20 minutes. You might miss a pattern.

**After:** Upload the CSV to Claude with this prompt:

```
I'm attaching a CrunchTime labor export. Find and rank the top 3 reasons we exceeded our labor budget in weeks where we did. For each reason, show me the weeks it appeared and the $ impact. Then tell me which ONE is most fixable this week.
```

Claude runs through the data, spots that you were short-staffed on Fridays three times (forced overtime on salaries), that product training didn't stick (slower ticket times), and that the weekend lunch shift overlaps were too wide. It ranks them, points to Fridays as the quickest fix (just tighten the 11â€“2 window), and shows you the math. You didn't have to open Excel or do arithmetic. Five minutes instead of twenty. And you got *insight* instead of just "we were over."

This is the move: upload the raw export, ask Claude to do the forensics, and *then* decide what to fix. The tool is there. Most operators still do this by hand.

---

## 4. Gotcha of the Week

**The "I'll just copy-paste that number" trap.**

You ask Claude: "Based on last week's CrunchTime report, what should our food cost % be next week?" Claude generates a number â€” say, 28.7% â€” with full confidence. Looks solid. You file it away and cite it in a manager meeting.

Then you pull the actual CrunchTime report. The number Claude generated? Not on the sheet. Claude hallucinated it because it "felt right" based on vague context.

**The fix:** NEVER cite a number that Claude generated from memory or inference. If the number matters â€” and in restaurants, they all do â€” pull the actual source data (PDF, export, email), paste it into Claude, and ask again. Then Claude is reading facts, not generating plausible-sounding numbers. Your credibility depends on this. Five Guys corporate notices when numbers are wrong. Claude doesn't.

---

## 5. New Tool Worth Trying

**Claude Projects + your Five Guys playbook (literally 3 minutes).**

1. Open https://claude.ai/new/project
2. Name it "Five Guys Store 2065 Playbook"
3. Click "Add Files" â†’ upload your SOP PDFs, CrunchTime config docs, anything you reference weekly
4. Now create a blank file in the Project, paste this:

```
You have access to our Five Guys Store 2065 playbooks. When I ask a question about procedure, policy, or standard workflow, reference the uploaded docs first. If it's not in the docs, say so and tell me where to check.
```

5. Start asking questions. "What's our Friday lunch staffing model?" Claude pulls from your docs, not memory.

This takes three minutes. You now have a searchable, persistent reference library that Claude actually uses. No more "I think the handbook says..." â€” you *know* because Claude cited the page.

---

## 6. AI in the Wild â€” Restaurant Relevant

**Toast (the POS company) just rolled out AI-powered inventory predictions.** Restaurants using Toast's POS can now ask the system "what inventory should I order Friday for the weekend?" and Toast's model predicts based on historical transaction patterns, weather, and local events. Not perfect. But it cuts guessing. Smaller chains are using it to reduce waste and shrink. Five Guys hasn't announced parity, but watch for it.

**Why it matters to you:** This is the shape of the next wave. POS systems are adding AI directly (not as a bolt-on, but native). Your CrunchTime exports will eventually come with AI commentary baked in. The operators who are already comfortable asking AI questions about data will adapt faster. You're already there.

---

## 7. Skill Up â€” Do This Today

**15-minute exercise: Ask Claude to find the signal in noise.**

Find any PDF or image from your last week â€” a daily huddle photo, a handwritten note, a screenshot from CrunchTime, anything real. Paste it into Claude with this:

```
Look at this [PDF / image]. Extract the ONE thing that surprises you or looks off. Not what's expected â€” what doesn't fit the pattern? If nothing's off, tell me what's normal and why.
```

Pay attention to what Claude flags. Does it see something you didn't? Does it miss something obvious? 

**The question for next time:** Which surprised you more â€” what Claude caught that you missed, or what it didn't see?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail? Reply in the feedback area and I'll build a fix into next week's brief.*

---

**Brief sent 2026-09-25 at 12:00 PM ET**

