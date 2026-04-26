# Bobby's Daily AI Brief — 2026-04-26
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

**Claude Design just went live** (April 17). This is a legit tool—not an experiment. You can now collaborate with Claude to build menus, promotional graphics, store signage templates, and scheduling slides without touching Figma or Canva. For Five Guys specifically: training posters, weekly crew schedules, promotional flyers, shift assignment boards. No design experience required. Just describe what you want ("create a Five Guys crew schedule template for 10 people, 2 shifts, red/yellow Five Guys colors") and Claude handles the visual output.

Why this matters: you currently spend time wrestling with Excel or Google Sheets layouts. Claude Design is faster and looks sharper.

---

## 2. Prompt of the Week

**End-of-Shift Operations Recap** — Paste this exact structure into Claude after your shift:

```
You are an operations audit assistant for a Five Guys franchise. Your job is to listen to my shift recap and flag three things: (1) what worked today, (2) what broke and why, (3) one specific action for tomorrow. Keep answers short—bullet points, not paragraphs. If I mention something that was expensive or time-consuming, ask me what it cost and what it prevented.

Here's my shift recap:

[PASTE YOUR VOICE MEMO TEXT, NOTES, OR MEMORY HERE. BE MESSY. INCLUDE STAFF NAMES, FOOD WASTE AMOUNTS, EQUIPMENT ISSUES, CUSTOMER COMPLAINTS, SALES NOTES, ANYTHING THAT HAPPENED.]
```

Why this prompt works: You're giving Claude a clear persona (auditor, not cheerleader), then asking for structured output (three categories), and forcing it to ask about cost + prevention (because that's how you actually think). The "be messy" instruction removes the pressure to pre-clean your input. Claude handles the translation from memory into action items.

---

## 3. Use Case Spotlight

**CrunchTime Export Cleanup & P&L Summary**

**Before:** You export a CrunchTime report (Labor, Sales, COGS) and get a spreadsheet with 47 columns, dates in three different formats, and totals that don't match the header row. You spend 30 minutes in Excel guessing which columns matter.

**After:** Paste the messy export into Claude with this: *"Clean up this CrunchTime export and give me (1) sales total, (2) labor total, (3) food cost total, (4) flag anything that looks like a data entry error."* Claude reads the noise, finds the signal, and gives you three numbers + one red flag in 20 seconds.

Example output:
```
Sales: $4,827.34
Labor: $1,240.50 (12.7% of sales — normal)
Food Cost: $1,635.20 (33.8% of sales — slightly high, check Monday deliveries)
Flag: Void transactions on 4/23 don't have manager codes — training issue or cash handling blind spot
```

---

## 4. Gotcha of the Week

**Claude Hallucinating Numbers Like It's Confident**

You ask: *"What's average labor cost per hour at a Five Guys?"*

Claude says: *"Typical Five Guys labor cost is 28–30% of sales, with average hourly rates of $14.50–$16.00 for crew and $22–$28 for managers."*

You write it down as fact. You report it to your DM. Later, you realize it was a guess—a confident, well-structured guess, but a guess. Claude doesn't have real Five Guys payroll data. It pattern-matched your question to food service benchmarks and returned an answer that "sounded right."

**The fix:** When asking Claude for numbers about your specific business, say: *"I'm going to paste actual data from my store—CrunchTime, payroll, sales reports—and I want you to calculate [X], not guess. Don't use industry benchmarks unless I ask for those separately."* Force Claude to work from YOUR data, not from what sounds plausible.

---

## 5. New Tool Worth Trying

**Claude Projects with Your SOP**

Do this right now:
1. Go to claude.ai
2. Click "Create Project" (top left)
3. Name it "Five Guys Store 2065"
4. Upload your SOP documents (if you have a PDF or Word doc)
5. Start a new chat in that project and ask: *"What's the cash handling procedure step 3?"* or *"Summarize the opening checklist"*

Claude now remembers your SOP for that entire project. No copy-paste. No asking which document. This takes 90 seconds.

Why: Your SOPs are load-bearing knowledge. Claude remembers them inside that project. Future updates are just new uploads.

---

## 6. AI in the Wild — Restaurant Relevant

**Little Caesars Deployed Drone Delivery (This Week)**

Little Caesars partnered with Flytrex to launch high-capacity drone delivery at select locations. Not science fiction—actual test markets, actual delivery of pizzas.

Why Bobby needs to know: The labor shortage and delivery cost problem that you're solving with tighter operations is also a problem for big chains. Drones solve it differently (capital + tech). You solve it better (smarter scheduling + automation). In 24 months, either drone delivery becomes standard (and Five Guys corporate will decide whether to adopt), or it stays niche. Either way, the big chains are betting on tech-first solutions. Your edge is that you're building operations intelligence first—the tech follows.

---

## 7. Skill Up — Do This Today

**Turn a Voice Memo into an Action List**

Here's your exercise:
1. Record a 3–5 minute voice memo on your phone about something that happened today (a problem, a win, a staff issue, a customer complaint—anything)
2. Paste the transcript into Claude (or use Claude's voice mode to speak it directly)
3. Ask: *"Organize this into (1) what happened, (2) who's responsible, (3) what I'm doing about it, (4) what I need to tell my DM"*

Watch what Claude does with rambling, emotional, non-linear input. That's the moment it earns its paycheck.

**Question for next brief:** Did Claude capture the issue accurately, or did it miss something you were thinking but didn't say out loud?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
