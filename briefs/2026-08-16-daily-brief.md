# Bobby's Daily AI Brief — August 16, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Nothing shipped this week yet (Sunday morning), but here's what's live in production today: **Artifacts** now support real-time interactivity — your dashboards, forms, and tools can read live data from your servers without hard-refresh. Pair this with your fiveguys-dashboard: next time you ship an updated `data/` file, the live dashboard on GH Pages auto-refreshes for every manager who has the tab open. No cache-busting, no page reload. That's a quality-of-life win for Store 2065 when you're pushing morning deposits + overnight corrections — the page just *updates*. Claude Code's multi-tab workflow is solid too: paste a CrunchTime export into one tab, get formatted analysis in another. Stop alt-tabbing between apps.

---

## 2. Prompt of the Week

**Scenario:** You need to coach a manager through why their labor percentage is 22% over budget for the week. Direct criticism fails. Here's what works:

```
You are a QSR operations mentor. A manager just completed a week with 22% labor.
They're discouraged—they think it's a failure. Your job is to:
1. Help them understand what actually happened (did they over-hire? Did a shift run short? Did they comp labor?)
2. Show them what *good* looks like for that type of week (traffic spike? Holiday? Staffing transition?)
3. End with ONE specific thing to improve next week.

Tone: encouraging, data-first, no blame.

Manager: "We had 22% labor this week. I'm doing something wrong."
Their week: Tuesday holiday (half day), Wednesday restock day (bulk truck + inventory), 
Thursday-Sat normal, Sunday slower. They ran 85 hours on $8,200 sales.

What's the conversation?
```

**Why this works:** The role setup (mentor, not judge) and the specific context (which days, which activities) teaches Claude to *explain* rather than condemn. QSR labor is a moving target — what's "over" depends on what actually happened. This prompt teaches you AND Claude that the analysis matters more than the number.

---

## 3. Use Case Spotlight

**Before:** 
"Give me a CrunchTime export" → opens a CSV → squints at 40 columns → manually finds the numbers → pastes into an email

**After:**
Upload the CrunchTime export + ask Claude: "What's my food cost variance for the week, and what's driving it?" → Claude reads the export, compares your purchases to your P&L, and gives you the top 3 categories out of line with your plan.

**Real example:**
*Upload:* Par Brink weekly purchase sheet + CrunchTime P&L
*Ask:* "My food cost hit 29.2% this week, that's 2% over my 27% target. Which categories pushed it over?"
*Get back:* "Your beef (ground + patties) is 3% of your variance. Bread (non-commodity bake charges) is 1%. Everything else is in line. Beef cost $286 more than plan — was that a different supplier, a price hike, or did you inventory more than usual?"

That's the work you're doing manually every week that Claude can own in 10 seconds.

---

## 4. Gotcha of the Week

**The trap:** You ask Claude a question about your data and it sounds confident. The number it gives you feels right. You paste it into a spreadsheet or an email. Later you find out it was hallucinated.

**The failure:** Claude can't access your files directly in the free version of claude.ai. It can read things you paste or upload, but only in that ONE chat. Upload the CrunchTime export in chat A, ask a question in chat B, and Claude has no memory of the file. You end up repeating context, or Claude starts guessing. Guesses sound like facts.

**The fix:** Keep sensitive/numerical work in Claude Code (the CLI or desktop app), not the web chat. Claude Code can read your local files persistently. Or: paste the data into the same chat EVERY time you ask a related question. Or: use Claude Projects to keep files + context together across conversations. One project, one theme (Labor Analysis, Food Cost, Schedule Builds). Your data stays in the same place.

---

## 5. New Tool Worth Trying

**Claude Projects — 2-minute setup, zero learning curve.**

1. Go to claude.ai → Projects → + New Project
2. Name it "Five Guys Store 2065 Labor Analysis"
3. Click the folder icon → upload your labor export (Excel, CSV, PDF, whatever you have)
4. Type a question: "What's my labor trend over the last 8 weeks?"
5. Claude reads the file, remembers it for every message in that project going forward.

**Why:** Next time you open the project, the file is already there. No re-uploading, no re-explaining context. You ask follow-ups and Claude knows what data you're talking about. Make one project per major task (Labor, Food Cost, Schedule, Safety Compliance) and stop context-switching.

**Time to try:** 5 minutes. Do it while your coffee brews on Monday morning.

---

## 6. AI in the Wild — Restaurant Relevant

**AI in scheduling is finally getting real at major chains.** Toast POS announced an AI-powered shift-swap recommendation system that actually learns your preferences — who usually swaps with whom, which shifts get swapped most, who's reliable. Instead of staring at a request to swap, the system flags whether it's likely to work based on history. Not quite autonomous yet, but it's moving from "feature" to "actually useful." Five Guys isn't on this yet, but Teamworx (your scheduling backbone) is watching. When it lands, it'll save you 30 minutes of swap admin per week.

---

## 7. Skill Up — Do This Today

**One 10-minute exercise to deepen your Claude chops:**

1. **Grab one recent CrunchTime export** (sales, labor, something you know cold).
2. **Open Claude** (chat or Projects, your pick).
3. **Upload the file** and ask: *"Show me this data as a story, not a table. What's the headline? What's surprising? What's the one thing I should act on?"*
4. **Look at what Claude gave you.** Does the story match what you already know? Does it find something you missed?

**What you'll notice:** Claude is *much* better at pattern-finding than at raw math. The moment you ask it to *explain* data instead of just *reading* it, the value jumps. That's the skill: asking the right question.

**Next time we talk:** What surprised you most about what Claude found in your data?

---

*One ask: What's one thing you wanted Claude to do for you this week that it didn't quite nail?*

---
