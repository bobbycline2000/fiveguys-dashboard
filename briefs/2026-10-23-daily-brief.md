# Bobby's Daily AI Brief — October 23, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Anthropic just donated Agent Skills (the framework that teaches AI tools how to do specialized tasks) to the Agentic AI Foundation. Translation: if you build a workflow that works in Claude, that same workflow will start working in dozens of other AI platforms too—Toast, HubSpot, whatever else you use. It's not flashy, but it matters. Right now you're building workflows that live only inside Claude. In six months, those same skills run anywhere.

Consumer feature bump: Claude on iPhone got faster, and the Projects feature (where you upload your SOPs and Claude remembers them) got a polish pass. Nothing breaking, but the fact that Claude remembers *your* restaurant's process instead of generic ones is becoming the baseline. That's the shift—from generic AI to *your* restaurant's AI.

---

## 2. Prompt of the Week

**Copy-paste this straight into Claude when you need to debrief a tough shift or meeting:**

```
You are a restaurant operations advisor. Your job is to listen to what went wrong (or right) and reflect back what you hear in a way that's useful for next time.

I'm going to describe a shift or situation. For each problem I mention:
1. Name the actual problem (not the symptom)
2. Suggest ONE change that could prevent it next time
3. Tell me what to watch for to know if that change is working

Don't try to fix everything. Don't give me ten ideas. Just the most important one per problem.

Here's what happened: [PASTE YOUR SHIFT NOTES, EMAIL, OR VOICE MEMO HERE]
```

**Why this works:** The role tells Claude to *advise* not *lecture*. The constraints (one change, watch for this signal) force Claude to prioritize and keep it actionable. Restaurant shifts are chaos—what you need from AI is the one thing that matters, not a consultant's full report. This prompt teaches Claude to think like a GM, not a business school case study.

---

## 3. Use Case Spotlight

**Before:** You get the weekly SharePoint FG Daily Report from bdavis. You eyeball the 2065 tab, maybe notice something's off, maybe don't. Takes 5 minutes of staring.

**After:** Paste that xlsx into Claude Projects. Ask: "What's different this week vs. last week? What should I be concerned about?" Claude instantly cross-tabs the numbers, flags variance, suggests what to ask about on Monday. Same data, 20 seconds, actual insight.

Real example from last week: A manager pasted a week of Par Brink labor vs. scheduled. Claude flagged that Thursday ran 18% over target. Root cause? A call-in without coverage. Claude pulled the Thursday shift and asked one question: "Did you pull someone from kitchen to front, or did you run short?" That one question changed the whole debrief from "labor was over" to "here's why, here's how to fix it next time."

Stop reading raw numbers. Let Claude read them for you and tell you what to care about.

---

## 4. Gotcha of the Week

**The trap:** Claude invents plausible-sounding numbers when it doesn't know.

You ask Claude: "How many Five Guys are in Kentucky?" Claude says confidently: "There are approximately 47 Five Guys locations in Kentucky as of October 2026." Sounds authoritative. You quote it. It's wrong. Maybe there are 23. Maybe 89. Claude doesn't actually know—it guessed and presented it like fact.

**The fix:** After any question about a specific count or statistic, ask Claude to cite where it got that number. If it can't (because it made it up), don't use it. Better yet: ask Claude to tell you *how* you'd verify that number (call corporate, search the Five Guys app, check SEC filings). Then go verify it yourself. Use Claude as a research partner, not a reference library.

---

## 5. New Tool Worth Trying

**Voice mode on Claude for iPhone—5 minute setup.**

Download Claude app. Tap Settings → Voice Input. Tap "Enable." Now you can tap the microphone icon in any chat and speak. Claude transcribes and responds via text or voice (your choice).

Use case: End of shift, walking out, you've got 20 things rattling around your head. Open Claude, tap mic, say: "Recap: we ran 18% labor over, DJuan called in, had to pull Alex from kitchen, two tickets backed up, fixed it by 8:30, next time adjust for Tuesday's smaller prep crew." Hit send. Claude writes it back as a clean paragraph. Paste it into your shift log. You've captured the whole day in 90 seconds instead of 10 minutes of typing.

Do this today. Talk to Claude for 3 minutes. You'll get why this matters.

---

## 6. AI in the Wild — Restaurant Relevant

**Bojangles just rolled out AI drive-thru systems to all 900 restaurants.** Not a pilot. All of them. By this week.

What they're doing: AI listening to orders, confirming them, handling the chaos of voices in the background, and flagging to the headset person when something sounds wrong. Not replacing people—augmenting them. A headset person + AI = faster, fewer order mistakes.

Why it matters to you: Bojangles is a franchisee chain, same as Five Guys. If a regional QSR just proved that AI drive-thru works at scale, corporate's next earnings call will absolutely get the question: "When's Five Guys rolling it out?" You should know what's coming. And if you're building your own ops AI right now (which you are), you're ahead of the conversation instead of behind it.

---

## 7. Skill Up — Do This Today

**Prompt:** Open Claude. Paste in one of your recent shift notes, a manager email, or a voice memo you recorded. Ask Claude:

```
Break this down by category:
1. What went well (list it)
2. What went sideways (list it)
3. What's the one thing I should do differently next shift?
```

Then look at the answer. Ask yourself one question: *Did Claude catch something I would've missed?* Maybe it noticed you mentioned staffing four times in different ways. Maybe it saw a pattern in the times things got messy. 

Next time, before you panic about a bad shift, run it through Claude first. You'll notice the difference.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
