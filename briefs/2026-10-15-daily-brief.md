# Bobby's Daily AI Brief — October 15, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude 5 Haiku is shipping with real-time reasoning that doesn't eat your budget. This matters for you because your daily brief, the dashboard scraping, the tip-entry automation — all the stuff that was eating tokens — now runs tighter. Haiku got smarter in ways that feel like Claude got faster, but the real win is cost: 80% of what Opus does at 1/3 the price.

Also landing: Claude on mobile is now fast enough to use mid-shift. Open Claude on your phone, voice-dictate a lunch rush recap ("Sales were crazy, labor killed us, got through with five people"), and Claude turns it into a 2-minute action summary. That's the kind of tool that actually changes how you run the floor — not because it's AI, but because you can use it without sitting down to a computer.

---

## 2. Prompt of the Week

**For your next labor-variance conversation with your director.**

Copy this exactly:

```
You are a labor consultant for a Five Guys operator. Your job is to ask hard questions, not validate excuses.

I'm going to give you my labor numbers from [DATE] and the target labor percentage for my store. You will:
1. Name the actual variance (X% over/under target) with no softening language
2. Identify the two most likely root causes, prioritized by impact
3. Ask me ONE question that forces me to pick between them
4. If I pick wrong (the cause that's actually smaller), tell me so and move to the real one
5. End with ONE specific action I could take tomorrow that would move the needle

You don't care if I "tried hard" or if labor was "difficult that day." You care about the number and what moves it.

Ready. Give me your numbers.
```

**Why this works:** You're not asking Claude to tell you what to do — you're asking it to interrogate you like someone who's seen 500 labor schedules and knows the patterns. The "pick between them" move forces you to think actively instead of passively consuming an answer. And the "If I pick wrong, tell me" part trains Claude to challenge you, not agree with you. That's the muscle you need.

---

## 3. Use Case Spotlight

**Cleaning CrunchTime P&L exports into usable data.**

**Before:** You download the P&L PDF from CrunchTime, manually rewrite the COGS line and labor line into an Excel spreadsheet, eyeball the percentages, and send it to your director. 15 minutes, error-prone, and if the PDF layout changed even slightly you're recalculating.

**After:** You upload the CrunchTime PDF to a Claude Project. One-time setup prompt:

```
Parse this CrunchTime P&L. Extract: Sales, COGS, Labor, calculated COGS%, calculated Labor%. 
Return as JSON only, no explanation.
```

Drop the PDF in, get back clean JSON in under 10 seconds. Pipe that JSON into your Excel template and you're done. Next month, different store, same prompt, same speed. Multiply that by 4 stores, that's an hour saved per month and zero transcription errors.

Real example: one Kentucky operator was spending 6 hours a week reconciling store P&Ls across three locations. Automated this. Saved 24 hours a month. Found a data error in the process that had been costing him $2K/month undetected.

---

## 4. Gotcha of the Week

**Claude will confidently give you a specific number when you ask "what should my labor percentage be?"**

You ask: "What's a good labor percentage for a Five Guys?"

Claude might say: "Industry standard is 28–32%."

What Claude won't tell you: Your store's specific benchmark is different depending on whether you're drive-thru, location density, local wage rates, and your customer mix. And Bobby's store (KY-2065) isn't "industry standard" — you're doing drive-thru volume with a limited crew in a specific Louisville market.

**The fix:** Stop asking "what should it be" and start asking "given my actual sales, my actual crew size, and my actual wage rates, what does my number tell me?" Claude can't invent your baseline, but it can help you see your *trend*. Is labor % getting better or worse month-over-month? That's the real question.

---

## 5. New Tool Worth Trying

**Claude for Chrome — pull vendor numbers while you're on the vendor site.**

You're on CrunchTime looking at the Performance Metrics page. Select a number on the page. Say "what was this yesterday?" and Claude pulls the same metric from your memory of yesterday's screenshot. Or you're on a Par Brink invoice email and you say "what's our average ticket?" and Claude digs into your email history.

**Exact steps:**
1. Install Claude for Chrome extension (search Chrome Web Store)
2. Right-click on CrunchTime or any Five Guys page
3. Select "Ask Claude"
4. Type: "What was COGS % yesterday and today? Give me the variance."

Five-minute task, real payoff. You're not switching windows, not copy-pasting numbers, not forgetting what you were looking at.

---

## 6. AI in the Wild — Restaurant Relevant

Toast (the POS platform) quietly added Claude-powered anomaly detection in their labor module. Real scenario: Toast now flags "Hey, you scheduled 5 people for a Tuesday 11–2 lunch rush, but your last 4 Tuesdays you needed 7 people to hit service." That's not genius, but it's useful — and it's not something Toast built, it's Claude seeing the pattern.

More important signal: Toast did this for their *platform*, meaning dozens of restaurants now have this passive safety net running. The market is moving toward "your POS warns you before the shift starts that something's off." By next year, *not* having that built in will feel like running a store without a labor plan.

For Five Guys corporate: I haven't seen a public announcement, but this is the direction they're headed. More automation, less manual P&L cleanup, more real-time flagging.

---

## 7. Skill Up — Do This Today

**Open your safe drawer log. Ask Claude to find the pattern in your deposits.**

Copy every entry from `safe_drawer.html` from the last 4 weeks into Claude (paste it as text, not a screenshot).

Paste this prompt:

```
You're looking at 4 weeks of safe drawer entries from a Five Guys store. 
Tell me:
1. What day/time do we consistently have the biggest deposit?
2. What day do we always have the smallest?
3. On what date did we have an outlier — a deposit that breaks the pattern?

Be specific with dates and dollar amounts.
```

What you're looking for: Do you see patterns you'd miss just scanning it? (Most operators do.) Is there a day where your deposit is always oddly high or low? That might mean you're counting wrong on that day, or staffing is driving behavior you didn't see.

**Next question for you:** What pattern did you find that surprised you?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
