# Bobby's Daily AI Brief — July 13, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

**Claude Sonnet 5 shipped June 30.** It's the new default-best model — faster coding, better agent behavior, hits the sweet spot between capability and cost. If you've been running complex workflows (schedule builds, dashboard automation, multi-step analysis), Sonnet 5 is the model to use now. Haiku stayed the same (fast, cheap, good for simple tasks). Opus is still the heavyweight for really gnarly problems. Bottom line: your Five Guys dashboard work just got a speed bump for free if you switch to Sonnet 5.

**Claude Code is now an official product**, not an internal tool. That matters. It means it's getting serious engineering investment, bug fixes, new features every week. You're not on a beta tool anymore — you're on the thing Anthropic's doubling down on. If you've had friction with the dashboard automation, the fixes are coming faster now.

**Claude Tag launched.** It's metadata tagging for conversations so you can organize and search your chats by project/topic. Your 200+ dashboard sessions? You can tag those now and actually find them later. Not essential, but the organizational leverage is real.

---

## 2. Prompt of the Week

**Use Case:** End-of-shift manager debrief and action capture. You speak it into Claude, get back a structured recap with issues, who owns them, and follow-up date.

**Prompt (copy-paste ready):**

```
I'm a Five Guys manager closing shift today. I'm going to tell you about 
what happened, problems that came up, and things we did well. Your job:

1. Summarize the shift in one sentence (sales/traffic/vibe)
2. List every issue that came up — no spin, just facts
3. For each issue: who needs to handle it? When?
4. List 2-3 things the crew did RIGHT today
5. One thing to watch tomorrow based on today's work

Format the output as a plain-text recap I can email to the GM.
Don't use corporate speak. Be direct. Be real.

Here's what happened today:
[paste your notes, voice memo transcription, or just tell the story]
```

**Why this works:** 

You're not asking Claude to *generate* a manager's voice—you're asking it to *hear* your voice and organize it. The specifics (five Guys, shift close, email to GM) anchor Claude to YOUR context, not a generic manager scenario. The "no spin, be direct" instruction keeps it useful instead of glossy. You get structured output without filling out a form. The closing instruction ("here's what happened") signals that what comes next is raw material, not a polished message. That boundary is what makes the whole thing work.

---

## 3. Use Case Spotlight

**Before:** You get the Par Brink PDF end-of-day report. It's a mess. Discounts scattered across pages, hourly sales in tables with merged cells, labor numbers mixed with food cost in the same column. You eyeball it, jot notes, maybe miss something. Takes 15 minutes. Data sits in your email inbox.

**After:** Upload the Par Brink PDF to Claude with one prompt:

```
Extract from this POS report:
- Hourly sales (format: HOUR | SALES | TRANSACTIONS)
- All discounts applied (item, reason, amount)
- Labor hours and cost
- Food cost percentage

Return as JSON. If a field is unclear or missing, note it.
```

Claude pulls it clean. Sells you the structured JSON. You pipe it straight into your dashboard. No manual transcription. No eyeballing. Data flows live.

**Why this matters:** Par Brink data is the hardest piece of your daily dashboard update. It's the one thing still living in PDFs and email. This prompt breaks that logjam. You're 90 seconds from raw PDF to structured data in your system.

---

## 4. Gotcha of the Week

**The trap:** You ask Claude "How many employees do I have?" and it says "Based on what you've mentioned, approximately 20–22." You write that number down. You tell Bobby "we have 22 people." A week later you realize it was actually 18 and someone called out sick, so the number was never real. Claude was confident and wrong.

**The fix:** Never ask Claude to infer a count. Always ask Claude to *read a source* and *tell you what's there*. Change from:

❌ "How many employees do I have?"

✅ "Read the employee_directory.py file I uploaded and tell me the active headcount, exactly."

Claude won't hallucinate a number. It'll read the file and count. Same effort, bulletproof answer. The difference is giving Claude a source document instead of asking it to reconstruct history.

---

## 5. New Tool Worth Trying

**Claude on iPhone** (if you have it) — under 5 minutes to try.

1. Download the Claude app from the App Store (free)
2. Sign in with your account
3. Start a voice conversation: hit the mic icon and talk
4. Ask: "Debrief this shift for me" or "Parse this receipt" or just vent about the day

That's it. No setup. Your voice goes in, structured output comes back. The iPhone app is actually better than the web version for voice — less typing, more thinking. Try it on your way out of the store one day. You'll use it every close after that.

---

## 6. AI in the Wild — Restaurant Relevant

**Hardee's franchisee filed for Chapter 11** (per NRN this week). Why? Not technology — but it's a reminder of the real pain point: unit economics in QSR are brutal. One franchisee going down is often a symptom of labor cost, food cost creep, or traffic volatility that no amount of automation fixes *by itself*. The operators winning right now are the ones using data (like your dashboard) to catch the creep early and make cuts before the margin disappears. Taco Bell's ingredient recall this week? Those incidents spike labor cost (retraining, communication, cleanup). Your real job is not "use AI to look smart." It's "use data to catch problems before they become existential."

---

## 7. Skill Up — Do This Today

**Your task:** Upload one Par Brink PDF to Claude Projects and extract the three metrics that take you the longest to find manually. Here's exactly what to do:

1. Go to [claude.ai/projects](https://claude.ai/projects)
2. Create a new project: name it "Par Brink Parsing" (or "POS Test")
3. Upload today's Par Brink PDF
4. Paste this prompt:

```
Extract ONLY these three fields from this POS report:
1. Total sales (today, all shifts)
2. Average transaction value
3. Highest-grossing hour

Return as a simple list with numbers only (no formatting).
```

5. Run it. Look at the output.

**Question for next time:** Did Claude get all three right, or did it miss something? Which field was hardest to find?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---
