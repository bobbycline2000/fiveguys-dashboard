# Bobby's Daily AI Brief — 2026-11-27
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude 5 (Opus 5.5 and Sonnet 5.5) are now fully live and stable. For you: faster responses on routine tasks (inventory decisions, vendor emails, writing schedules), sharper on structured data (parsing CrunchTime exports, spotting labor variance), and genuinely better at following exact constraints (you can now tell Claude "output ONLY this format" and it sticks). No setup needed. The upgrade was invisible if you've been using claude.ai regularly. 

What matters: Claude on your phone now handles dictation near-perfectly. That means you can record a 60-second voice memo during service about what broke today, and Claude turns it into a written action item with owner + deadline. That's operational gold for a GM running on-the-fly.

---

## 2. Prompt of the Week

**Use this prompt to turn chaotic shift notes into an SOP:**

```
You are a process documentation expert. I am going to give you scattered notes from several shifts about how we handle [closing procedure / inventory / manager walk / deposit]. Your job is to:

1. Extract all the actual steps in order
2. Flag any steps that contradict each other across the notes
3. Write a single clean SOP: 
   - Numbered steps (1-20 max)
   - Each step says WHAT and WHY
   - Highlight any steps that require Bobby's decision
   - Flag timing dependencies (e.g., "do this before the closing manager leaves")

4. For each contradicting step, ask me one clarifying question

Format output as:
[STEP NUMBER]. [ACTION] — [WHY THIS MATTERS]

Here are the notes:

[PASTE YOUR NOTES HERE]
```

**Why this works:** The hardest part of turning ad-hoc knowledge into an SOP is spotting what's actually critical vs. what's habit. This prompt forces Claude to surface contradictions instead of glossing them. You paste in Dakayla's notes + Divan's notes + your own observations, and it handles the dedup + ordering for you. Then you just fill in the 2-3 questions where the team actually disagrees.

---

## 3. Use Case Spotlight

**Before:** You get the par Brink PDF emailed at 7 AM. It's a table of sales by category + labor hours. You manually rekey the totals into the SharePoint FG Daily Report. Takes 10 minutes. You're tempted to skip it.

**After:** You paste the PDF into Claude Projects (save it once, use it every day). Ask: "What was net sales for 2065 yesterday?" Claude reads the PDF and tells you the number in one second. You type it into the sheet. Done.

**The move:** Upload the Par Brink PDF to your Claude Projects folder once. For the next 30 days, any sales question ("what was our ticket average yesterday?" "which category did worst?") gets answered by Claude reading the live PDF—not by you hunting through the email or retyping. When the new PDF arrives, overwrite the old file. No new setup.

---

## 4. Gotcha of the Week

**The trap:** You ask Claude "How much should I spend on a new fryer?" and it gives you a detailed answer about capital budgeting. You trust it. You order. Then you realize Claude made up the price ranges—it was guessing. No LLM has real-time pricing data.

**The fix:** When asking Claude about costs, attach the actual quote or spec sheet first. Ask: "Given this quote from [vendor], what questions should I ask before I buy?" Claude can now reason from real data instead of hallucinating it. Same for labor decisions—paste in the actual timecard export, don't describe it from memory.

---

## 5. New Tool Worth Trying

**Claude on your iPhone — 5 minutes to set up, game-changer for service:**

1. Go to App Store, search "Claude" (by Anthropic)
2. Download, open, sign in with bob.cline2000@gmail.com
3. During your shift: When something breaks or you think of a task, voice-record a quick note ("The ice machine's making a grinding noise, did that last week too")
4. Let Claude transcribe + summarize it
5. Share the text to Notes or Slack

You're not changing how you work. You're just catching thoughts in the moment instead of losing them. Try it for two shifts and see if it sticks.

---

## 6. AI in the Wild — Restaurant Relevant

Five Guys corporate just quietly started testing automated ordering for franchise locations via their Point of Sale partner. The goal: franchisees who don't have time to place food orders themselves can let an AI watch their inventory levels and auto-order from suppliers before they run out. No pricing changes (margins are locked by contract), no quality judgment calls—just "you're running low on beef, here's your standing order." If it ships next year, you're the kind of GM who could use it immediately. Watch for it in a corporate email, not a press release.

---

## 7. Skill Up — Do This Today

**Write a 10-minute schedule-draft prompt and time yourself:**

Paste the last three weeks of your actual crew shift requests + no-shows into a fresh Claude chat and ask:

"I need to build next week's schedule. Here's who requested what days. Here's who called out the last three weeks. I want:
- Nobody more than 2 open shifts in a row
- Everyone who requested days should get at least one
- Two people per shift minimum
- Bobby (that's me) needs Sunday morning off

Give me a proposed schedule. For any conflicts, ask me one question."

Look at Claude's draft. How close was it? What did it miss? That gap tells you what a schedule-building agent would need to know to run this automatically every Sunday night.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---

**Next Run:** 2026-11-28 at 06:00 ET
