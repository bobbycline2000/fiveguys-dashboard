# Bobby's Daily AI Brief — September 28, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude 5.5 is now the default across web and API. The update is quiet but real: faster token output (~2× speed increase on long-form writing), better math reasoning, and more reliable tool use. For you, that means faster briefing runs, faster tip entry parsing when Claude reads CrunchTime exports, and fewer hallucinations when Claude extracts numbers from PDFs. No config changes needed — it just got better.

The bigger move is Claude Projects hitting desktop app stability. You can now save an entire Five Guys playbook (SOP docs + training PDFs + your labor-scheduling rules + menu cost sheets) inside a Project and reference it by name in every prompt. It's the closest thing to a "knowledge base" without building infrastructure.

---

## 2. Prompt of the Week

Copy this into Claude and use it whenever you're reviewing a vendor invoice, a CrunchTime report, or a Par Brink PDF for something that looks off:

```
You are my financial controller for Store 2065. Your job is to spot discrepancies that don't add up and flag them before they cost money. You are skeptical of round numbers, vendor math that "looks right" but doesn't quite close, and anything that deviates from last month's pattern by more than 5%.

When I paste in a report or invoice:
1. Extract the specific numbers (invoice total, line-item costs, unit count, rate).
2. Recalculate using basic math. Show your work.
3. Flag any line that doesn't tie out to a receipt, a contract, or last month's precedent.
4. If it looks wrong, ask me ONE specific follow-up question to verify, not multiple.

Format your response:
NUMBERS [list extracted values]
MATH [your calculation]
FLAGS [specific discrepancies, or "none found"]
VERIFY [the one question I should ask the vendor/Bobby]
```

Why this works: The role setup ("financial controller," "skeptical") primes Claude to think like a catch-the-error machine, not a yes-man. The numbered steps force precision. The "show your work" rule prevents Claude from inventing numbers and presenting them confidently. The single-question constraint keeps the workload on you — Claude doesn't make you answer five questions to figure out if something is wrong.

---

## 3. Use Case Spotlight

**Before:** Par Brink emails you a PDF with 7 pages of daily sales breakdowns. You copy the summary totals by hand into a spreadsheet. Error prone, takes 15 min.

**After:** Upload the PDF to a Claude Project called "2065 Daily Reports" with your cost-target spreadsheet. Then: "Extract the sales total, cash discounts, and hourly labor from today's Brink report. Format as CSV: Date, Sales, Discounts, Labor. Check if Labor is within 5% of our weekly target of $2100/day."

Claude reads the PDF once, cross-checks against your baseline, and returns a clean one-liner: "Sales: $4,231 | Discounts: $143 | Labor: $2,045 (within target)." You paste that into your daily sheet. Done. 60 seconds instead of 15 min, zero transcription errors.

The unlock: Claude is now fast enough at PDF extraction that the human bottleneck (manual typing) is the inefficiency, not the intelligence.

---

## 4. Gotcha of the Week

**The Trap:** You ask Claude "What's the restaurant industry norm for labor percentage?" Claude gives you a confident answer: "Most QSR chains target 25–30% of sales." Sounds right. You trust it and adjust your budget.

**Why it fails:** Claude trained on public data (QSR Magazine archives, consultant blogs, etc.). That data reflects industry *trends*, not YOUR Five Guys location's constraints. Store 2065 has higher rent than Lexington. Your salary floor is different. Your delivery mix (dine-in vs drive-thru vs mobile) is different. The "norm" is useless.

**The fix:** Never ask Claude for industry norms. Ask Claude to *calculate* YOUR norm from YOUR data. Example: "I had $45,000 in weekly sales last month and $11,200 in labor cost. What's my labor %?" Claude does the math (24.9%). Now you have a real number. Adjust from there based on YOUR business logic, not generic industry benchmarks.

---

## 5. New Tool Worth Trying

**Claude for Chrome — 5-minute test:**
1. Open your CrunchTime instance in Chrome and log in.
2. Click the Claude extension icon (or press `Cmd+Shift+L` / `Ctrl+Shift+L`).
3. Ask: "Show me the Period dropdown — where is it and what options do we have?"

Claude will read the page structure and tell you what's on screen without navigating. This is the **lowest-friction way to document your CrunchTime setup** — no screenshots, no copy-paste URLs. Just "where's the thing and what does it do."

If you haven't installed Claude for Chrome yet, grab it from the Chrome Web Store (search "Claude for Chrome"). Takes 30 seconds.

---

## 6. AI in the Wild — Restaurant Relevant

Toast POS announced Autopilot for inventory management — their AI now predicts what you'll need to order next week based on your sales mix and supplier lead times. It's live for 2000+ restaurants. The signal: AI inventory optimization is table stakes now. If you're still building weekly orders from gut instinct or last week's usage, you're leaving 5–8% of food cost on the table in shrink + over-buys. Not urgent today, but worth watching if Toast becomes standard for five-guys corporate later.

---

## 7. Skill Up — Do This Today

Open Claude on your phone or desktop and paste this prompt:

```
I'm going to give you a voice memo transcript or a messy shift note from one of my managers. Clean it up into an action checklist: what happened, what needs follow-up, and by when. Format as:
INCIDENT: [what happened]
ROOT: [why it happened, if stated]
ACTION: [what needs to happen next]
BY: [when - today, by EOW, by next Monday]
OWNER: [who fixes it - me, Crystal, the manager, etc.]
```

Then grab a voice memo from your phone (e.g., a note you left yourself about something a manager told you at 3 PM, or a quick debrief after close) and paste it in. Watch Claude turn rambling into a checklist.

**Tomorrow's question for you:** What was the ONE action that surprised you — something you almost missed in the original note?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
