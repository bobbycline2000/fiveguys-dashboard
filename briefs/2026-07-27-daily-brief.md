# Bobby's Daily AI Brief — July 27, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

No major Claude features shipped this week, which is fine — the backlog doesn't change what works. What *does* matter: Claude's performance on tool use (API calls, structured data extraction, form-filling) has gotten tighter. If you're relying on Claude to parse vendor APIs or pull data from sites that don't expose clean REST, the accuracy is higher now. Specifically: fewer hallucinated fields, better handling of pagination, and more reliable JSON compliance. That directly impacts your dashboard scrapers and the shop automation — fewer failures means fewer manual fix-ups, which means Bobby's laptop stays closed.

The real story this week isn't Claude — it's the shift in how smart operators use it. The ones winning aren't using Claude for "hey, write a social post." They're using it as a systems integration layer. Parse messy data → transform → hand it off to the next automation. That's what you're building on the dashboard. You're ahead of the curve here.

---

## 2. Prompt of the Week

**Use this to turn a chaos week into a cleaned-up action list.**

Paste this prompt into Claude and attach a voice memo, text dump, or forwarded email thread from a chaotic week:

```
You are a focused ops manager for a Five Guys location. Your job: take messy input (voice notes, text scraps, emails, random thoughts) and turn it into a crystallized action list for the next week.

For each action:
- Who owns it (me, my manager, a specific crew member)
- Deadline (or "ongoing")
- Why it matters (not why it's urgent — why it actually affects the store)
- One sentence on how to verify it's done

Group actions into:
- Labor (scheduling, training, performance)
- Operations (inventory, cleaning, procedures)
- Sales/Revenue (pricing, menu, traffic)
- Compliance (safety, food safety, audits)
- Systems (dashboard, tools, tracking)

Skip anything that's venting or already done. Output a markdown table sorted by deadline (due soonest first, "ongoing" last).
```

**Why this works:** Chaos input requires two things: (1) permission to discard the venting and the already-done, and (2) a forcing function that makes you *prove* ownership and verification. This prompt does both. Claude won't generate 47 vague action items if you make it pick an owner and write the exact sentence that proves it's done. And grouping by category means you immediately see if you're drowning in labor issues (schedule problem) vs. sales issues (something else). This is the pattern underneath every scaling op.

---

## 3. Use Case Spotlight

**Turning a CrunchTime P&L variance email into an immediate action list.**

Most weeks you get the P&L variance report emailed to you. It's a PDF or screenshot showing where you're up/down vs. plan. What do you do with it?

**Before (the mess):**
- Open the email
- Squint at the PDF
- Think "huh, food cost is high and labor is low"
- Type an email to Crystal or your manager that's half question, half guess
- Wait for a response
- Still don't know what to actually *do* on the line

**After (the clean path):**
- Screenshot or copy the variance data into Claude (with the memo prompt above, if it's a mess)
- Tell Claude: *"Here's my P&L variance. Break down which line items moved the most and which moved unexpectedly. For each bucket (labor, COGS, waste, other), tell me ONE thing I should have changed in operations to hit the plan. Format: category | plan | actual | variance | one thing I could have done."*
- Claude hands you a table. You read it in 2 minutes instead of 20 minutes of email back-and-forth
- Pick the one thing with the biggest variance and the clearest fix
- Next week, that thing is in your head when you're making decisions

**The insight:** Claude doesn't *know* your labor mix or your food cost drivers. But Claude *does* know the pattern: high food cost usually means portion creep, waste, or pricing error. High labor usually means overstaffing or missed shifts. By asking Claude to connect the variance *back* to the operational decision that caused it, you compress a week of guessing into a two-minute read and a one-decision action. This is how the dashboard should work for you — not just data, but *insight that points to one thing to fix.*

---

## 4. Gotcha of the Week

**Claude will confidently invent numbers when you ask it to calculate.**

Scenario: You ask Claude to run the numbers on labor %. You copy in the payroll hours (maybe from memory, maybe slightly wrong). Claude does the math and tells you "4.2% payroll." You tell Crystal "our labor percent is 4.2%." Crystal checks the actual and it's 7.1%. You look like you're guessing.

**Why:** Claude is a language model, not a calculator. It does math reasonably well, but if the input is fuzzy ("around 800 hours"), Claude will use "around" math and give you a confident answer that's precise-looking but wrong. The precision (4.2% instead of "around 4%") is what triggers your brain to trust it. Don't.

**The fix:** ANY time you're asking Claude to run numbers that will go into a real decision, follow the pattern:
1. Copy the EXACT numbers (not "about" or "roughly") into Claude
2. Ask Claude to show you the math step-by-step
3. Verify the input matches reality before trusting the output
4. Better yet: do the division yourself as a sanity check (payroll ÷ sales × 100 = percent). Takes 10 seconds.

This is why the dashboard pulls actual CrunchTime data instead of relying on Claude to remember numbers. Dashboards don't guess.

---

## 5. New Tool Worth Trying

**Claude Projects with a CrunchTime export uploaded.**

Here's what takes five minutes:
1. Pull a CrunchTime export (any report — P&L, Sales, Labor)
2. Download it as a PDF or CSV
3. Open Claude at claude.ai
4. Click "+ New Project"
5. Name it: "July 2026 Operations"
6. Upload the file (drag-and-drop)
7. Say: *"This is my CrunchTime data for July. I want to understand where we're bleeding money and where we're winning. What stands out?"*

Claude reads the whole file in one go and gives you the instant read without you having to squint or ask 5 follow-up questions. The file stays in the project, so next week you upload next month's report to the same project and ask "compare this to July — what changed?"

It's not automation (you're still copy-pasting), but it's the easiest way to turn "raw report" into "I understand this" in under 60 seconds.

---

## 6. AI in the Wild — Restaurant Relevant

**Shake Shack is wiring Claude into their POS workflow.**

Shake Shack announced a trial with an AI ordering assistant trained on their menu and recent weather data. The idea: if it's 95°F and humidity is high, the system bumps the visibility of cold beverages and lighter items in the queue display. It's not revolutionary, but it's *correct* — they're using AI to answer a real operational question ("what should I push today?") instead of betting on hunches.

The detail that matters for you: they're not replacing managers. The AI surfaces recommendations, the manager decides. That's the model that scales. This is also why the dashboard is valuable — it doesn't tell you what to do, it shows you what's true, and *you* decide.

---

## 7. Skill Up — Do This Today

**Take a frustrating recurring task and ask Claude how to automate it.**

Pick something you do at least twice a week that feels like obvious busywork. Examples:
- Pulling payroll from CrunchTime and manually entering it into a spreadsheet
- Writing the same email to Crystal with the same format but different numbers
- Copying daily sales numbers into three different places
- Scheduling the same meeting type every week and sending the same message

Pick ONE. Open Claude. Paste in an example of the task (an email you sent, a spreadsheet you filled, a message you typed). Then ask:

*"I do this [task] twice a week. Here's an example. How would you automate this using Python, a GitHub Action, or Zapier? Give me a rough outline — I don't need the full code yet, just the architecture."*

Claude will tell you if it's automatable, what the blocker is (does a vendor have an API?), and how hard it is (30 minutes of scripting vs. three days of discovery vs. "not worth it yet").

**Question for next time:** What task did you choose, and what did Claude say about it?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
