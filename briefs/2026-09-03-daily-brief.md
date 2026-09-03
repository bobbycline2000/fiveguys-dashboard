# Bobby's Daily AI Brief — 2026-09-03
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

No earth-shattering Claude releases this week, which is fine. What matters to you is stable, predictable capability — not shiny beta features. The real move right now is that Claude's accuracy on reasoning (math, logic, multi-step chains) has been solid for months. The gotcha is people still using Claude for quick advice when they should be using it for structured analysis. You have the tool. Use it right.

**What changed:** Claude's handling of uploaded CSVs/Excel files got faster. If you're pulling reports from CrunchTime and pasting them as text, stop. Upload the file. Claude processes it smarter and returns cleaner analysis. One thing worth trying: upload your Par Brink PDF, ask Claude to extract the discount trends, and compare to last month. See if it catches something you missed.

---

## 2. Prompt of the Week

**Shift Recap → Action Plan**

This is a prompt you can run end-of-shift or next morning to turn what happened into what you do.

```
You are a Five Guys shift operations analyst. Your job is to read a brief shift recap and turn it into a prioritized action plan for the manager and the team.

Shift Date: [DATE]
Shift Type: [Lunch / Dinner / Overnight]
Crew Count: [NUMBER]

Shift Recap:
[Paste what happened — cash issues, customer complaints, equipment breaks, labor clashes, food waste, staffing gaps, anything noteworthy]

Your output:
1. Root cause of the biggest issue (one sentence)
2. What to do about it (specific, immediate step)
3. What to watch next shift
4. One thing the crew did right (morale matters)

Keep it tight. No fluff. Format for someone reading it on their phone.
```

**Why this structure works:** The "root cause → immediate action → what to watch" sequence forces you to move from "something went wrong" to "here's what we do." The "one thing right" forces you to notice positives, which managers skip. Upload your phone notes from shift, paste them in, run it. You get a 90-second briefing instead of a rambling recap.

---

## 3. Use Case Spotlight

**Before:** Email from Par Brink: a PDF with 4 pages of sales, labor, discounts. You open Excel, manually enter discounts into a spreadsheet, cross-check totals, wonder if you missed anything.

**After:** Upload the PDF to Claude + paste your question: *"What were our top 3 discount drivers today? Which discount code spiked highest hour-over-hour? Any patterns vs. last Thursday?"* Claude extracts the data and does the comparison. You get the signal in 30 seconds instead of 10 minutes of spreadsheet work.

The key: Claude doesn't just read PDFs. It *understands* the structure. It compares across multiple pages. It spots anomalies (a discount that fired 200 times when it normally fires 5). Most managers are still printing these out and writing notes by hand.

---

## 4. Gotcha of the Week

**The Invention Problem:** Claude will confidently make up numbers that sound reasonable. Ask it "what was the average customer spend at Five Guys in 2024?" and it'll give you an answer. It will *sound* plausible. It will be wrong. You'll trust it. You'll use it in a conversation with your district manager. It will be embarrassing.

**The Fix:** Any question about facts — trends, numbers, benchmarks, historical data — gets a second source. Ask Claude, then verify against your actual data, an industry report, or a person who knows. For Five Guys specifics, your district manager or your P&L are the truth. Claude is the spark. Verification is your job.

---

## 5. New Tool Worth Trying

**Claude on your iPhone (5 minutes)**

1. Go to the App Store on your iPhone
2. Search "Claude"
3. Download the official Anthropic app (blue icon, white C)
4. Sign in with bob.cline2000@gmail.com
5. Take a photo of your shift checklist, a receipt, or a handwritten note
6. Ask Claude: "What's on this? Any gaps?"

Why: You're already writing notes on your phone. Five seconds of a photo + one question beats typing out the context. Works for menu photos, competitor visits, staff timesheets, inventory counts. Test it once and you'll use it every shift.

---

## 6. AI in the Wild — Restaurant Relevant

**Toast POS (major competitor to your Par Brink setup) just announced AI-powered labor scheduling.** Here's what matters: they're automating the "who should work when" question using historical sales data + time-off requests. The promise is fewer labor outs and less overstaffing. The gotcha is you still need *accurate* sales forecasts or it'll suggest you staff up for a Tuesday that's always dead. This is why reverse-engineering your own CrunchTime data (which you have, right now) beats waiting for a vendor to solve it for you. You have more data than Toast does. Use it.

---

## 7. Skill Up — Do This Today

**Extract Discount Trends from Your Par Brink PDF**

1. Pull your Par Brink report PDF from your email (or ask Craig to send yesterday's)
2. Open Claude
3. Upload the PDF
4. Paste this: *"Show me every discount code that fired. Rank by frequency. Which one is most used?"*
5. Look at the answer. Ask yourself: "Do I recognize this pattern? Is it what I expected?"

One follow-up: *"Which discount code drove the highest total revenue? Did that match the most-used code?"*

**What you're learning:** The difference between "used most often" and "made most money." Most operators only watch frequency. You're spotting which discounts actually move the needle on revenue. That's the lever.

**Question for next time:** What's one discount code that fired way more (or less) than you expected?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---
