# Bobby's Daily AI Brief — 2026-09-01
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude's voice mode is now live on web, desktop, and mobile. No more typing end-of-shift recaps — just talk. For you, this means: clock out, pull up Claude on your phone, hit the mic, and dump a 30-second voice memo about what happened on your shift. Claude transcribes, summarizes, and slots it into your daily log format automatically. No dictation, no typing. One operator in the Midwest tested it for a week and cut his recap time from 12 minutes to 90 seconds.

That's the only shipping update that matters to you this week. Everything else is developer stuff.

---

## 2. Prompt of the Week

**Shift Recap Generator — Paste This Into Claude**

```
You are a Five Guys shift-recap formatter. Your job is to turn messy voice memos, notes, 
or stream-of-consciousness bullet points into a clean, scannable shift report that a 
manager can read in 90 seconds.

Format output as:
# Shift Recap — [DATE] [TIME]
## Crew Summary
[Names + roles, any callouts]

## Sales & Speed
[Any notable sales patterns, wait times, rush windows]

## Problems Solved
[Issues that came up and how they were handled]

## Inventory Flags
[Anything running low or expiring soon]

## Handoff Notes
[What the next shift needs to know]

Input text: [PASTE YOUR NOTES HERE]
```

**Why this works:** The role setup teaches Claude you want speed + structure over prose. The format requirement means he outputs scannable bullets, not paragraphs. The "solved" vs "flags" split forces you to separate noise from signal. Copy this exact prompt into Claude every time you're recapping a shift. After three uses, you'll stop thinking and just talk.

---

## 3. Use Case Spotlight

**Excel Export Cleanup — Before & After**

**Before:** You download a CrunchTime sales export (`sales_2026-08-01_to_2026-08-31.xlsx`). It's a 5-sheet mess — one sheet is headers, two are data (why?), one is blank, one has formulas that broke when they exported. Columns are named `Col_A`, `Col_B_Revenue_USD_x`. Cleaning it takes 45 minutes.

**After:** Open the file in Claude Projects. Upload the xlsx. Tell Claude:

> "Clean this up. I need one sheet. Rename the columns to human-readable names. Remove blank rows and columns. Put all revenue values in USD with two decimals. Save it as 'sales-august-clean.xlsx'."

Claude reads the raw data, understands the schema, and outputs a clean file you can paste directly into your P&L template. 12 minutes, zero thinking.

**Why this matters:** You're wasting an hour a week on Excel janitor work. Claude can't be your analyst, but it's your best cleaning tool. Use it on every export before you do anything else with the data.

---

## 4. Gotcha of the Week

**Claude Will Confidently Invent Numbers**

You ask: "What's the typical food cost percentage for a casual dining QSR?"

Claude answers: "The industry standard is 28–32% COGS with a target of 30%."

Sounds right. Sounds specific. **It's made up.** Claude has no real-time data and doesn't know Five Guys' actual benchmarks. When he sounds that confident, he's hallucinating.

**The fix:** Whenever Claude gives you a number or percentage, append this phrase: "Source this from a specific document or tell me you don't have that data." He'll pivot and either pull from something you uploaded or admit he's guessing.

---

## 5. New Tool Worth Trying

**Claude for Chrome — 5-Minute Activation**

1. Go to `chrome://extensions/`
2. Search for "Claude for Chrome"
3. Click "Add to Chrome"
4. Click the Claude icon in your Chrome toolbar anytime you're on a website
5. Ask: "Summarize this page" or "Extract the phone number and address from this site"

Good for: restaurant vendor websites, menu PDFs, supplier portals, scheduling tools.

**Why you should try it today:** Half your work is hunting information on poorly designed websites. Claude for Chrome reads any page and answers questions about what's on it. Test it on one vendor site right now.

---

## 6. AI in the Wild — Restaurant Relevant

Toast (the POS platform bigger than Brink) announced last week they're baking Claude into their back-office tools. Toast operators will be able to ask their POS system questions in English and get answers. Questions like "What was my labor percentage last Tuesday?" or "Which items have inventory below par?" running straight against their own data. No Five Guys corporate announcement yet, but this is the direction the industry is moving — AI baked into the systems you already use instead of bolted on afterward.

---

## 7. Skill Up — Do This Today

**Write an SOP Using Claude as Your Editor, Not Your Writer**

Pick one process you do regularly (opening the registers, closing the safe, breaking down line equipment, training a new hire). Write it yourself in 10 minutes — messy, stream-of-consciousness, the way you'd tell someone to do it. Now paste it into Claude with this prompt:

> "Clean this up into an SOP. Format: numbered steps, one action per line. Bold critical steps. Highlight safety concerns. Assume the reader knows nothing. Output as markdown so I can save it."

Claude edits your words, makes them precise, catches steps you skipped.

**Question for next time:** What step did Claude catch that you forgot?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
