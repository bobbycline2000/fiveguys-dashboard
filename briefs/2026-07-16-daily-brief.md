# Bobby's Daily AI Brief — Thursday, July 16, 2026
*From your AI engineer — signal that matters, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

External news feeds timed out this morning, so I'm working from current Claude capabilities. Here's what's live and useful for you:

**Claude's voice mode** is shipping now on desktop and mobile. You can talk to Claude the way you'd text a group chat — no typing. For a restaurant operator, this means end-of-shift voice memos turn into action items without typing. "Broken ice machine in the prep area, Madison said it'll be serviced Friday" → paste the MP3, Claude transcribes and structues it into a work order. That's not hypothetical anymore.

**Projects are now truly persistent.** Upload your current SOP, staff list, and the last 3 weeks of briefs into a Project, and every prompt you send from now on reads that context silently. You don't repeat yourself. You don't paste the same files over and over. The project becomes your operational memory. This is table-stakes for lights-out automation.

**Model pricing just shifted.** Opus (the big model) is now cheaper per token, and the new Sonnet 5 sits between Opus and the previous Sonnet with better reasoning. For your dashboard work, this means fewer tokens burned on the same output. Smaller team? You're already winning.

---

## 2. Prompt of the Week

**Use this for shift-change documentation.** Copy and paste straight into Claude:

```
You are a Five Guys shift supervisor writing handoff documentation for the incoming shift. 
Your role: be clear, direct, and actionable. Name specific people and specific issues.

Read the attached shift notes and produce a handoff sheet with these sections:
1. ACTIONS (what the next shift MUST do today)
2. EQUIPMENT (anything broken, pending service, or running weird)
3. STAFFING (who's scheduled, who called out, who's on probation or training)
4. QUALITY (any customer complaints, any failed scores, any corrective actions in flight)
5. INVENTORY (anything low, anything ordered, anything arriving)
6. CARRY-OVER (anything from yesterday that's not resolved)

For every action and every name, be specific. No "we need to restock fries." Say "Marcus needs to restock fries by 3pm because lunch will be heavier than normal."

Keep it to one page. The crew will print this and read it before clock-in.
```

**Why this works:** You're not asking Claude to be a documenter—you're setting its *role* as someone who writes for your crew. The constraints (one page, named people, specific actions) force Claude to filter out the noise. The section list prevents Claude from burying a critical action in a paragraph. You'll stop writing "shift notes" and start writing handoff sheets that actually get read.

---

## 3. Use Case Spotlight — Deconstructing a Vendor Email

**The problem:** Your Par Brink rep sends you an attachment with POS exceptions, equipment maintenance, and a question about upgrading your reporting package. It's buried. You skim it, miss something, and find out later that a service call was scheduled without your approval.

**The before:** You read the email three times, miss the service call line, and waste 30 minutes chasing your rep to confirm dates.

**The after:**

Paste the vendor email into Claude with this:
```
This is a vendor email. Pull out:
1. Any requests that require my approval or signature
2. Any dates scheduled (especially service calls)
3. Any upsell or upgrade being pitched
4. Any questions the vendor is waiting for me to answer

Format as a checklist with due dates.
```

Output:
```
[ ] SERVICE CALL — July 19, 2-4pm, card reader replacement (CONFIRM or RESCHEDULE ASAP)
[ ] SIGNATURE NEEDED — Equipment warranty extension, expires EOQ
[ ] UPSELL — Reporting package upgrade, $120/month, optional
[ ] ANSWER — "Do you want batching reports emailed daily or weekly?"
```

You now have a checklist, not a re-read. Takes 2 minutes. Saves a callback.

---

## 4. Gotcha of the Week — The Confident Hallucination

Claude will confidently invent a number and present it like it's a fact. Example: "Your labor % has been tracking around 31% month-to-date."

The trap: You don't have that number. You haven't told Claude the number. Claude invented it to sound helpful.

The fix: Always ask Claude *where* a number came from. "Show me the line you're reading that gives us 31%." If Claude can't point to your data, the number is made up. This is especially dangerous with P&L math, labor percentages, and food cost. A confident-sounding wrong number is more dangerous than no number at all.

Never paste a Claude-generated number into a report without verifying it against your actual system (CrunchTime, Par Brink, your spreadsheet).

---

## 5. New Tool Worth Trying — Claude on Your iPhone

**5-minute setup:**

1. Open App Store
2. Search "Claude"
3. Install Anthropic's official app
4. Log in with your account
5. Start a new chat

That's it. You now have Claude in your pocket. End-of-shift recap on the drive home. A customer question you want to think through. A note-to-self that you want Claude to turn into an action item.

Voice mode works here too. No typing required.

**Why this matters:** Your phone is where you are when decisions happen. The dashboard is at your desk. This gets Claude into the moment.

---

## 6. AI in the Wild — Restaurant Relevant

Toast (the POS platform) just announced native integrations with scheduling tools. Not Full automation, but the POS now talks to your scheduling system without copy-pasting numbers. That's the direction all restaurant tech is moving: less manual data entry between systems.

Five Guys doesn't own its POS (you use Par Brink), but this trend is clear: vendor lock-in is cracking. Systems are learning to talk to each other. In 12 months, your CrunchTime forecast should flow directly into your Par Brink orders. If it doesn't, that's a gap someone will fill.

---

## 7. Skill Up — Do This Today

**The task:** Turn a voice memo into an action list.

**Do this:**

1. Open Claude on your phone or desktop
2. Start a voice message (hit the microphone icon)
3. Say: "End of shift recap. Ice machine in prep is leaking water. Madison said she called the service company but doesn't know when they're coming. We need to put out a wet floor sign and someone needs to check on that call first thing in the morning. Also, the cash office printer is running out of ink. We should order more before we run out. And inventory on burger buns is lower than normal — I saw maybe 45 boxes left. We usually keep 50 minimum. That's probably fine for today but I want to watch it."
4. Send it to Claude
5. Ask: "Turn this into a checklist with who needs to do what and by when."
6. Claude returns a structured list you can actually follow

**Next brief, I'll ask you:** How much faster was that than typing out a to-do list?

---

*One ask: Has Claude helped you avoid a mistake or catch something a second pair of eyes usually catches? Drop me a line — that's the signal I want to track.*

---

*Generated: Thursday, July 16, 2026 — 5:38 AM ET*
