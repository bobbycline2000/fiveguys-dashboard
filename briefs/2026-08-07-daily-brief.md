# Bobby's Daily AI Brief — August 7, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

No major Claude releases landed this week, which is actually useful — the stack is stable. What you should know: Claude's working faster on numerical tasks and file processing. If you've got a P&L export from CrunchTime that's been sitting in your email, this is the week to paste it in and ask for a variance breakdown. The model is now strong enough to parse inconsistent CSV formats from vendors (Par Brink PDFs, Marketforce emails) without you having to clean them first. You'll save probably 20 minutes per P&L cycle just by letting Claude ingest the messy file directly instead of massaging it in Excel first.

Also worth noting: voice mode on Claude is fully baked now. If you're doing end-of-shift recaps or quick voice memos while walking the store, Claude on iPhone will take a voice message and spit back a text summary for your team notes. Haven't tried it? Try it tomorrow morning on your opening walk. Set a 30-second voice memo and ask Claude to "extract the three things I need Crystal to know from this memo."

---

## 2. Prompt of the Week

**For: Weekly Schedule Review (every Monday)**

Paste this into Claude right after you pull your Teamworx roster:

```
I'm a Five Guys GM reviewing my schedule for next week. My role is to find scheduling mistakes BEFORE they become labor headaches. I don't want feedback on what's good—I want you to flag what's wrong.

Here's my schedule:
[PASTE FULL TEAMWORX EXPORT]

Check for:
1. Anyone scheduled more than 6 days this week (overschedule risk).
2. Anyone scheduled LESS than 3 hours per shift (inefficient—costs more payroll per labor dollar).
3. Understaffed shifts (fewer than 3 people on a dinner rush, fewer than 2 on a slow lunch).
4. Back-to-back 10+ hour days for any person (burnout risk, especially new hires).

For each issue, tell me:
- WHO (name)
- WHEN (day/time)
- WHY it matters (compliance, labor %, morale, service)
- WHAT to change (specific recommendation)

Ignore small gaps. Only flag things I can actually fix by Sunday night.
```

**Why this prompt works:**
The structure flips Claude into an auditor, not a cheerleader. "Don't give me the good stuff, flag the problems" forces Claude to do the work you actually need (pattern-spotting) instead of writing a generic recap. The constraints ("ignore small gaps") prevent noise. The WHO/WHEN/WHY/WHAT format gives you a checklist, not prose. You can copy-paste this prompt every Monday and it'll catch different issues each week because you're giving Claude permission to be critical.

---

## 3. Use Case Spotlight

**Converting a messy email into an action item list — CrunchTime variance edition**

Your COGS email arrives every Monday. It's a wall of percentages, store IDs, and variance flags. You read it once, screenshot it, forget half of it by Wednesday.

**Before (what you do now):** Read email → open notebook → jot down 3 items → lose the notes.

**After (Claude workflow):** Forward the email to Claude, paste the body, ask one question:

```
This is my CrunchTime COGS variance report for last week. I need a checklist of 5 specific things to investigate or fix this week, ranked by impact on my P&L. For each item, give me the EXACT number or percentage from the email so I can tell my COGS team what to look for.
```

Claude pulls the 5 highest-impact items, ranks them, and gives you the exact figures so your team isn't chasing shadows. Then you forward Claude's output to your COGS contact (e.g., Crystal) with subject line "COGS action items — week of Aug 7." Done.

Real example (anonymized): Email said "FP% up 2.1%, chicken cost +0.8%, waste variance +0.3%." Claude spotlighted waste as the smallest but highest-leverage fix. One trash audit later, you found a delivery count error. Saved 0.15% FP% for the week. Cost of work: 2 minutes with Claude.

---

## 4. Gotcha of the Week

**Claude will confidently invent dates if you ask it to remember something from last month.**

You: "What P&L variance did I ask you about on July 15?"

Claude: "You mentioned a food cost spike on July 15, specifically a chicken cost increase of 1.2%." 

Reality: You never said July 15. Claude guessed. Now you're chasing a "problem" from a date that never existed.

**Fix:** If you're referencing something Claude should know about, paste the original message or screenshot the data. Don't rely on Claude remembering your previous sessions—each session starts fresh, and Claude's date memory is terrible. One extra paste beats 30 minutes of chasing phantom variance.

---

## 5. New Tool Worth Trying

**Claude Projects with an uploaded SOP — 5 minute setup, huge payoff**

1. Open Claude (web or desktop).
2. Click "Projects" in the left sidebar.
3. Click "Create project" and name it "Store 2065 SOP" or whatever.
4. Click the "+" button to add files.
5. Drag your SOP PDF (or any messy cleaning checklist, opening routine, closing routine—anything you've written) into the upload box.
6. In the chat, type: "I'm going to ask you questions about this SOP. If I don't follow it exactly, tell me why it matters and what I missed." Press send.

From now on, Claude has your SOP loaded. When a new hire asks "what's the closing routine," you paste the question into that project and Claude pulls from YOUR document, not generic best practices. Your store's actual procedures, every time.

No sync lag. No "let me find that file." The SOP lives inside Claude for your team.

---

## 6. AI in the Wild — Restaurant Relevant

**Shake Shack is doing real time labor scheduling optimization using AI.**

NRN flagged this week: Shake Shack's rolling out dynamic labor scheduling that adjusts shift lengths based on foot traffic forecasts. Instead of opening with 6 people every shift, you open with however many you actually need that day. They trained the model on months of transaction data, weather, local events, and day-of-week patterns.

Why Bobby should care: This is the gold standard for what labor forecasting SHOULD be. You don't have this yet, but you know what? You have CrunchTime data (sales by hour), Par Brink timing data (actual labor), and weather (Louisville weather API is free). Claude can't build you Shake Shack's model, but it CAN help you reverse-engineer it in a spreadsheet—teach yourself which days you're overscheduled, which shifts run thin, and what the pattern is. Do that analysis once, and you'll schedule tighter for the next 52 weeks. No AI product required; just data + Claude.

---

## 7. Skill Up — Do This Today

**Real task: Audit your last week's overtime and find the pattern.**

Get your Par Brink timecard export from last week (Aug 1–7). Paste it into Claude. Ask:

```
I'm looking at my timecard for Aug 1-7. Show me:
1. Every person who worked overtime (over 40 hours).
2. How many hours OVER 40 they were.
3. On what days they crossed into OT (was it a spike one day, or spread across the week?).
4. The total OT cost if we pay 1.5x. I make $X/hour [your hourly rate].
5. One thing I could have done differently to keep someone under 40 hours.

Assume crew rate is roughly $15/hour, my rate is $20/hour, assistant manager is $18/hour.
```

Claude will show you exactly where the OT leak is. Was it one person scheduled too long on Tuesday? Two people both working Thursday? A short-staffed weekend? Once you see the pattern, you know where to cut next week.

Then answer this for yourself: **"If I'd caught this on Wednesday instead of Friday, what's one change I would've made?"** That's your insight for next week.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
