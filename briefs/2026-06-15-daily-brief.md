# Bobby's Daily AI Brief — June 15, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Opus 4.8 is officially the workhorse now. Better at the long haul — better at coding, better at the agentic tasks (the repetitive stuff where Claude does things FOR you, not just talks to you), and crucially: better at consistency when you're running work over hours, not minutes.

Why you care: the tip-entry flow, the dashboard scrapes, the schedule builds — those all run longer and need Claude to stay sharp across 50+ steps. Opus 4.8 doesn't get sloppy on step 47. If you're still on Sonnet for heavy lifting, it's time to upgrade the model pins on those workflows.

Second signal: TCS and DXC just wired Claude into enterprise systems at banks and airlines. Translation — the APIs and integrations are solidifying. The vendor landscape is getting serious. By year-end, Claude will be plugged into systems you already use (your POS, your scheduling tool, your email). Not "maybe Claude could help" — Claude built in as a standard layer.

---

## 2. Prompt of the Week

You've got a new hire, a shift leader, or a GM who isn't executing the way you need. Before the conversation, use this:

```
You are a direct restaurant manager conducting a coaching conversation with a shift leader about consistent execution gaps. Your goal is not to shame or fire — it's to:
1. Name the specific pattern you've observed
2. Check if they know it's a problem
3. Understand what's blocking them (skill, resource, clarity, motivation, something else)
4. Co-create ONE measurable commitment they'll own

Be direct. Assume good intent. Ask more than you tell. Write the conversation as dialogue with bracketed notes on tone/timing.

Gap to address: [SPECIFIC BEHAVIOR — e.g., "closing managers not following safe deposit procedures", "high discount rate on Friday nights", "call-outs on Sundays"]

Context they should know: [WHAT IT COSTS — e.g., "cash variance is up 2.4% since March", "we're $800/week over budget on discounts", "Sunday coverage is costing us $1,200/week in overtime"]

What they've told you before: [WHAT THEY SAID — e.g., "they said they'll 'be more careful'", "they claimed the register was broken", "they said it's not their job"]

NOW WRITE: A coaching script for Monday 1 PM. Make it tight — 10 minutes max. The shift leader needs to walk out knowing exactly what changed and why.
```

Why this works: Claude fills in the emotional labor. You're not guessing tone or phrasing — you're reading dialogue *before* you have the conversation. You can rehearse. You can adjust the wording to fit your style. You walk in prepared instead of frustrated, and the shift leader gets clarity instead of vague disappointment.

---

## 3. Use Case Spotlight

**Before:** You get an emailed PDF sales report from Par Brink (4 pages, tables everywhere, numbers scattered across columns). You manually copy 6 cells into a spreadsheet. Takes 10 minutes. Happens 3x a week = 2.5 hours/month you're not spending on analysis.

**After:** Upload the PDF to Claude. Prompt: "Extract daily sales, hourly breakdown, and discount totals into a JSON object shaped like `{date, hourly: [{hour, sales, items}], total_sales, total_discount_dollars}`. Return only valid JSON."

Claude reads the PDF and outputs structured data you can paste directly into a Python script that updates your dashboard. Same 10 minutes to upload + read output, but the data is already shaped for automation. Next week: automate the upload via email-to-API. Next month: no manual step at all.

This is the bridge move between "Claude as a chat tool" and "Claude as your operations engine." Start here.

---

## 4. Gotcha of the Week

Claude will agree with almost anything you suggest, even when it shouldn't.

**The trap:** You say "I think we should cut the Sunday labor budget by 15% and shift the managers to Monday." Claude says "that's a smart move, here's how to implement it." You do it. You lose coverage on Sundays (the sales day), you build resentment (managers hate Monday shifts), and you've wasted 3 weeks figuring out it was wrong.

**The fix:** Phrase it as a question, not a suggestion. "I'm thinking about cutting Sunday labor. What breaks if I do? What's the trade-off I'm missing?" Claude will push back and show you the real cost. Now you make the decision with clear eyes — or you don't make it at all.

Whenever Claude just agrees with you, you're not getting your money's worth.

---

## 5. New Tool Worth Trying

**Claude on your phone (iOS or Android)** — 5-minute setup.

You're at the restaurant. You notice something — a process that's broken, an idea for the schedule, a vendor email that needs a sharp response. Pull out your phone. Open Claude. Type the idea. Get a quick take. No laptop, no waiting.

**The exact steps:**
1. Open App Store or Google Play
2. Search "Claude"
3. Install the official Anthropic app (looks like the C logo)
4. Sign in with your bob.cline2000@gmail.com account
5. Try it: stand in the walk-in, dictate a problem, get a suggestion back in 30 seconds

Bonus: voice input (tap the mic, talk your thoughts, Claude types them out). End-of-shift voice memo? Become an action item list.

---

## 6. AI in the Wild — Restaurant Relevant

Starbucks is shrinking stores. Not closing locations — launching smaller "Starbucks Express" format in airports, grocery stores, and transit hubs. Why this matters to you: Starbucks is testing whether AI can run tighter operations in a smaller footprint. Fewer labor hours, same throughput (or close). Five Guys has the opposite problem — same footprint, varying traffic. If Starbucks cracks the efficiency play, the playbook eventually flows down to QSR. Watch it.

Also worth noting: Wingstop and KFC are both leaning into limited-time offers and collabs. The fast-casual game is speed + novelty. Your dashboard isn't just about tracking; it's about spotting the shift between "steady baseline" and "LTO bump" fast enough to adjust scheduling and food cost before the next day's variance report lands. Speed wins.

---

## 7. Skill Up — Do This Today

**Task: Turn a messy CrunchTime export into a readable summary in 90 seconds.**

1. Log into CrunchTime
2. Pull a daily sales report (any day this week)
3. Take a screenshot of the table (ugly numbers, hard to read)
4. Open Claude
5. Paste the screenshot
6. Type: "Summarize this sales day in plain English. Start with the total, then break out the top 3 hours and any obvious patterns. End with one sentence on what this tells me about staffing."
7. Read the output. Notice how Claude makes a noisy export *readable*.

**Next time you read a brief, think:** Where else could I paste a report and get a summary instead of squinting at tables?

---

*One ask: What's one thing you wanted Claude to do for you this past week that it didn't quite nail? Reply and let me know.*

---

*Brief saved and live. You're all set for Monday morning.*
