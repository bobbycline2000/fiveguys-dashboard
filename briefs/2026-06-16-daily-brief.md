# Bobby's Daily AI Brief — 2026-06-16
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Anthropic shipped five concrete things that matter to operators building on Claude. **Dreaming** is a scheduled background process that reviews your agent sessions, spots patterns, and auto-updates memory between runs — so your Claude agents get smarter without you rewiring them every week. **Scheduled Deployments** means agents can now run on a cron job (nightly, weekly, daily) without touching a terminal. **Workflows** gave Claude Code a `/workflows` command for orchestrating multi-agent work transparently — useful when one agent's output feeds another's input. Claude Code also fixed parallel tool execution — a failed Bash command no longer cancels your other commands in the same batch.

The bottom line: agents are less friction now. If you're running lights-out work (your dashboard scraper, your brief generator, your tip entry), these moves buy you time back.

---

## 2. Prompt of the Week

**Your Daily Operations Debrief Prompt** — copy and paste this into Claude after your shift or at end-of-day:

```
You are my operations coach. I'm going to paste my notes from today's shift.
Your job: (1) spot the 2-3 things that went wrong, (2) name the root cause for each one, 
+(3) give me ONE specific action for tomorrow that prevents it. 

Format:
- Issue: [what happened]
- Root: [why]
- Action: [one sentence, do-this-tomorrow]

Don't tell me everything was great. Don't be generic. Be direct.

Here are my notes:
[PASTE YOUR NOTES HERE]
```

**Why this works:** The role setup ("operations coach") primes Claude to be diagnostic, not cheerful. The "root cause → one action" constraint forces specificity — you're not getting 47 suggestions, you're getting the three things that actually broke and one fix each. The "don't be generic" line is your insurance against Claude padding the output. Tomorrow morning, you read your three actions and they're already wired into your day.

---

## 3. Use Case Spotlight

**The CrunchTime Export Cleanup**

You get a P&L export from CrunchTime every week. It's a mess — 47 rows of nested location data, duplicate headers, three different date formats in the same column, $0.00 variance entries you don't care about, and one cell that says "N/A (see notes)" instead of a number.

**Messy input:**
```
LOCATION,PERIOD_START,REVENUE,LABOR_COST,VARIANCE,NOTES
KY-2065,05/26/2026,$12,450.23,($230.12),—
KY-2065,5/27/26,$11820,$2340,0.00,Check actual schedule
KY-2065,05/28/2026,$13100.99,N/A (see notes),($450),Called in 2 staff
```

**What Claude does in 90 seconds:**
1. Reads the messy export
2. Standardizes dates to YYYY-MM-DD
3. Strips zero-variance rows
4. Extracts the buried notes into a separate "Flags" column
5. Returns clean CSV you paste into Excel

**Output:**
```
Location,Date,Revenue,Labor_Cost,Variance,Flag
KY-2065,2026-05-26,12450.23,2340,230.12,—
KY-2065,2026-05-27,11820,2340,0,Called in 2 staff
KY-2065,2026-05-28,13100.99,—,450,Check actual schedule
```

**The prompt:** "Clean this CrunchTime export: standardize dates to YYYY-MM-DD, remove $0 variance rows, move any inline notes to a 'Flag' column, return as CSV."

This saves you 15 minutes per export and eliminates the transcription errors that make your variance analysis garbage.

---

## 4. Gotcha of the Week

**The Confident Hallucination**

Claude will invent numbers and state them with authority. This is the #1 failure mode I see in operators using Claude for financial/operational work.

**The trap:** You ask Claude "what's our labor cost as a % of revenue for last month?" and Claude reads your CSV, does math it *thinks* is correct, and returns "$4,200 is 34% of labor cost" — but the CSV only had 3 weeks of data, not 4. You don't notice the math is based on incomplete data. You present that number in a call with your DM. It's wrong.

**The exact fix:** After Claude does any math on your data, ask it to show its work: "Show me the sum formula you used and the exact rows from the export you pulled from." Make Claude cite its sources. If it can't point to the exact cell, the number is suspect. Don't trust the output until you see the inputs Claude used.

---

## 5. New Tool Worth Trying

**Claude Projects for Your SOP Binder**

If you have a Standard Operating Procedure that's longer than 2 pages, upload it to a Claude Project (new feature in Code). Then ask Claude questions against it — "what's the closing procedure for the safe?" / "who approves time-off requests?" / "what's the dress code exception for religious headwear?" — and Claude answers directly from your document every time.

**Steps:**
1. Open Claude Code (or claude.ai, doesn't matter)
2. Click "Projects" 
3. "New Project"
4. Upload your SOP PDF or paste the text
5. Name it (e.g., "KY-2065 Operations Manual")
6. Ask it questions in plain English

No setup. No parsing. Takes 3 minutes to upload, 5 seconds per question. Your crew can ask it before asking you.

---

## 6. AI in the Wild — Restaurant Relevant

Five Guys extended its partnership with SoundHound AI this year, expanding AI voice ordering across hundreds of locations. The partnership is now processing **over 1 million AI-driven customer interactions** — and Five Guys is giving franchisees the option to roll it out to more stores.

**What they're doing:** SoundHound's voice AI answers every incoming order (even peak hours), handles menu questions, allergen info, specials, parking/location queries — the full FAQ — without a human. Same AI that's already handling 100% of calls at locations that have it.

**Why you should know:** You're running Store 2065. The parent company is already thinking about this. If voice ordering rolls out to your location, your phone volume might drop by 30-40% (good) but you need to know it's coming so you don't panic when ring volume changes. Also: the data from these voice interactions is gold for understanding peak order patterns. Start thinking about how you'd use that signal.

---

## 7. Skill Up — Do This Today

**Practice the "Show Your Work" Discipline**

Open Claude. Paste this week's CrunchTime labor export (just the numbers, no secrets). Ask: "What's our total labor cost this week and what % is that of revenue?" Let Claude answer. Then ask: "Show me the exact sum formula you used and which rows you pulled from."

**What you're looking for:** Can Claude point to the specific cells? Does it cite line items? Or does it say "based on the data you provided" without specifics?

**Tomorrow's question for you:** Did Claude's answer match your mental math, or were there surprises? What surprised you?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---

## Sources
- [Code with Claude 2026: 5 New Agent Features Anthropic Just Shipped](https://www.mindstudio.ai/blog/code-with-claude-2026-new-agent-features)
- [What's Next for Restaurant Tech in 2026? Let's Ask the Experts - QSR Magazine](https://www.qsrmagazine.com/story/whats-next-for-restaurant-tech-in-2026-lets-ask-the-experts/)
- [Why 2026 is the year of the AI-driven restaurant](https://www.qsrweb.com/articles/why-2026-is-the-year-of-the-ai-driven-restaurant/)
- [Five Guys Extends Partnership with SoundHound AI](https://investors.soundhound.com/news-releases/news-release-details/five-guys-extends-partnership-soundhound-ai)
