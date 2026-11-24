# Bobby's Daily AI Brief — 2026-11-24
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

You've got three things running solid right now: **Claude on your phone via voice** (record your end-of-shift debrief and get a written summary in 20 seconds), **Claude Projects** (upload your SOP docs once, refer back without the copy-paste dance), and the **5-minute setup for Claude in Chrome** (run the tip entry flow review directly on the Par Brink page instead of exporting screenshots). None of these are brand new—they've been live for months—but they're the three highest-ROI moves for a restaurant operator who wants Claude to save *time*, not just produce text. If you're not using all three, you're leaving money on the table. Voice mode especially: it's the difference between "I'll type this later" and actually capturing what happened while it's fresh.

The bigger news this quarter is **AI agents getting smarter at step-by-step work** — meaning if you've been hesitant about wiring Claude into your daily workflows (the tip sheet, the daily brief, the schedule fill), those flows are now *more reliable*, not less. The error rate on structured data tasks has dropped. That matters for you because it means the dashboard automation and the tip-entry pipeline Bobby Cline is running can be even more lights-out than they already are.

---

## 2. Prompt of the Week

**Use this prompt for end-of-shift crew debriefs.** Paste this into Claude voice mode and record yourself while walking around the shop at close:

```
You are my restaurant operations advisor. I'm going to give you a stream-of-consciousness 
debrief of my shift. For each issue I mention, tell me:
1. The root cause (one sentence—what went wrong, not the symptom)
2. What I should do tomorrow to prevent it
3. What our crew member(s) need to know (if applicable)

Format your response as a text file I can forward to my team. Use plain language, 
no corporate speak. Lead with the win of the day, then tackle the problems. 
If I mention someone by name doing good work, highlight it.

Here's my debrief:
[Record your 2–3 minute voice memo here]
```

**Why this works:** You're not asking Claude to *create* a debrief from scratch (generic, low signal). You're teaching it to *translate what you already know* into a format your crew can act on. The "debrief as text file for the team" constraint forces Claude to cut the fluff. And naming the crew members doing good work? That's leadership. Claude will pick that up and amplify it in the output.

---

## 3. Use Case Spotlight

**Cleaning up the Par Brink PDF export into actionable data.**

Bobby Cline's team prints the daily Par Brink sales summary and manually enters the top-line numbers into the morning synopsis sheet. That's 8 minutes of copying numbers off a PDF—pure waste. Here's what actually happens if you upload the PDF to Claude:

```
INPUT (Par Brink PDF export):
[Full noisy PDF with logos, timestamps, 40 columns of data, two date ranges mixed]

OUTPUT from Claude in 60 seconds:
{
  "date": "2026-11-23",
  "net_sales": "$4832.17",
  "labor_percent": "28.1%",
  "hourly_labor": "$1358.45",
  "food_cost_percent": "24.3%",
  "top_3_items": [
    {"name": "Bacon Burger Combo", "sales": "$892.50", "qty": "156"},
    {"name": "Regular Cheeseburger", "sales": "$721.30", "qty": "218"},
    {"name": "Fries Large", "sales": "$412.80", "qty": "340"}
  ]
}
```

**Then** pipe that JSON into the synopsis sheet formula. Done in 2 minutes instead of 8. At 6 days a week, that's 36 minutes of your time back every week—or one of your assistant manager's time, which costs more.

The trap most operators fall into: trying to teach Claude to format numbers *perfectly*. Don't. Just teach it to extract *accurately*. Format the output in a simple JSON block, then let your spreadsheet handle the currency/percentage formatting. Claude's job: accuracy. Your spreadsheet's job: presentation.

---

## 4. Gotcha of the Week

**Claude will confidently invent numbers if you let it.**

Example: You ask Claude to "summarize my food cost variance for the last 4 weeks" and you paste in a P&L PDF. Claude will read it, find one week of data, and silently *invent* the other three weeks based on trends. It'll present them like they're real. You'll put those numbers in a report to your DM. Your DM will catch you in a lie.

**The fix:** Whenever you ask Claude for a number, follow up with "verify this is from the actual document, not an estimate." If Claude says "estimated based on trends," stop. Go get the real data. It takes 10 seconds to avoid a 2-hour explanation to your boss.

---

## 5. New Tool Worth Trying

**Upload your store's Five Guys SOP manual to a Claude Project.**

Here's the 3-minute setup:

1. Find your SOP PDF (probably on a shared drive or in an email somewhere)
2. Go to claude.ai/projects (top menu)
3. Click "+ New Project"
4. Name it "FG 2065 Ops" (or your store)
5. Click the paperclip, upload the SOP PDF
6. Done. 

Now next time you're training a crew member or you need to remember the official procedure for something, type "@FG 2065 Ops" in Claude and ask. Example: *"@FG 2065 Ops what's the protocol for a register short over $20?"* It'll search the SOP and answer you in 5 seconds. No hunting through a PDF. This pays for itself the first time you use it in a training session.

---

## 6. AI in the Wild — Restaurant Relevant

**Toast (the POS system) added Claude integration** (live for select franchises, broader rollout Q1 2027). This means restaurants using Toast will be able to ask Claude questions directly against their sales/inventory data without leaving the POS. For you at Five Guys: Par Brink doesn't have this yet, but CrunchTime has talked about similar integrations. What this tells you: in 6 months, the "copy-paste data into Claude" era will be over for the smart operators. The systems themselves will *be* Claude-aware. So the question you should be asking your corporate contact: *"Is Five Guys corporate building a Claude integration with CrunchTime?"* If not, you're ahead of the curve doing it yourself. If yes, you're future-proofed. Either way, you're not in the wrong direction.

---

## 7. Skill Up — Do This Today

**Upload a P&L PDF and ask Claude one sharp question about your margin.**

Go get one of your P&L reports (this week, last month, doesn't matter). Upload it to Claude here (or in your Projects if you set one up). Then ask this exact question:

*"What's the biggest P&L problem this week that I can fix by Friday?"*

Don't ask "what's my food cost" or "is labor high." Ask for the **problem I can actually fix by Friday.** Look at what Claude tells you. If it names something that feels right (crew training gap, one item dragging margin, portion creep on a popular burger), you've got your Friday mission. If it names something you can't touch by Friday (vendor price, corporate policy), it's giving you signal about what to escalate.

**Next time we talk:** Tell me what Claude flagged and whether it was a real gap or noise. This teaches you how to ask Claude the questions that *matter*, not just the questions that are easy to ask.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
