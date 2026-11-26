# Bobby's Daily AI Brief — 2026-11-26
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude just shipped **Projects with live web search** — your chats can now read the current web without you copy-pasting. This matters because you can drop a CrunchTime menu, a Par Brink PDF, or a Five Guys website into a Project and ask Claude to find prices, compare them, or flag inconsistencies in real-time. No more "here's what I think the current price is." You get what's live. The other move: **prompt caching is now standard** on all plans, which means Claude remembers your context across chats — load your store procedures once, ask 50 questions, pay for one context window instead of fifty.

Both are infrastructure plays. The web search is the bigger operator win: it means your daily brief can pull live data instead of waiting for email reports. That's worth bookmarking.

---

## 2. Prompt of the Week

**For coaching a crew member after a shift miss or mistake:**

```
You are a Five Guys shift leader coaching a crew member who [specific situation: missed their shift / forgot a closing task / was late to a key period]. Your goal is to help them stay on the team by understanding what happened and fixing it.

Ask exactly three questions:
1. What happened from their side? (Don't interrupt. Listen for the real reason: oversleep, transportation, personal crisis, misread the schedule.)
2. What do they need from us to prevent this next time? (They might need a phone reminder, a schedule printout, clarity on a process — don't assume.)
3. How can they make it right? (Offer a concrete path: extra closing, covering someone's shift, owning a task. Let them choose; don't decide for them.)

Your tone: direct but human. You are keeping them, not replacing them. No sarcasm. No "this is unacceptable." Lead with the assumption that they want to be here.

Write your response as a text they'd actually send or a 1-on-1 script they could read aloud.
```

**Why this works:** Most coaching fails because it starts with frustration instead of curiosity. The three-question frame forces you to understand *their* problem before you sell *your* solution. If someone is chronically late, there's always a reason — a bus route that changed, a kid's school pickup conflict, a disability nobody mentioned. When you find the actual constraint, the fix is real. The prompt forces emotional intelligence by making you say "I want to keep you" instead of "here are the rules."

---

## 3. Use Case Spotlight

**Taking a chaotic handoff email and turning it into a daypart-by-daypart action list.**

**Before (what you get from the manager on duty):**
> hey just so you know first shift was slower than expected, we might be short on fries if the lunch rush hits like last week. also one of the fryers has been acting weird again — sometimes it shuts off. mark and carlos both left early so we're thin for the evening. the fries guy called out for tomorrow morning so we need to figure out the backup. oh and someone needs to follow up on that beef order from wednesay, i think it was short

**After (what Claude turns it into):**
> **IMMEDIATE ACTIONS (before 11 AM)**
> - Inspect fryer #2 — document shutdown pattern (frequency, temperature, error codes) — if it fails again, don't use it
> - Verify fries inventory: current level vs. typical lunch peak consumption — if below 60%, prep extra tonight
> - Contact beef supplier re: Wednesday short order — confirm expected delivery date + quantity
> 
> **LUNCH SHIFT (11 AM – 2 PM)**
> - Expect traffic surge (similar to last week) — station backup fry crew by 10:45 AM
> - Monitor fryer performance during peak
> 
> **EVENING SHIFT**
> - Staff gap: Mark + Carlos out early = 2 fewer hands. Prioritize line speed; consider limiting special orders if traffic spikes
> - Brief evening team on fryer watchfulness
> 
> **TOMORROW MORNING**
> - Fries guy (name?) missing — assign: [backup name + start time]
> - Secondary backup on standby if primary doesn't confirm by 8 PM tonight

**Why this matters:** Handoff emails are decision-making noise. They mix urgency (the fryer thing) with logistics (staff shortage) with follow-ups (the order). Your brain has to sort it. Claude can parse that in 30 seconds and turn it into a checklist you can actually execute. Try it tomorrow morning with whatever chaos email you get — paste it in, ask for a daypart breakdown, and watch how much clearer your morning gets.

---

## 4. Gotcha of the Week

**Claude will confidently invent numbers if you ask for a calculation it can't verify.**

You: *"What's the average check size if we did 450 transactions and $3,850 in sales today?"* 

Claude will likely say: *"$8.56 per check"* — which is correct (3850 ÷ 450 = 8.55).

But you: *"What's the average check size if we did 450 transactions and $3,850 in sales over three days?"*

Claude will ALSO confidently give you a number — *"$8.56 per check"* — even though the question is ambiguous. It doesn't know if you mean the total average across three days, the daily average, or three separate days you want averaged. It'll just pick the most plausible-sounding answer and present it as fact.

**The fix:** Always feed Claude the specific constraint. *"We did $3,850 in sales across three days (Friday, Saturday, Sunday) with 450 transactions total. What's the per-check average?"* Now it's clear: $8.56 total average, or if you want daily: clarify that too. When Claude doesn't have enough info to know it's ambiguous, it assumes. Test it once: ask an ambiguous math question and watch it answer anyway.

---

## 5. New Tool Worth Trying

**Upload your store's SOP (Standard Operating Procedures) doc to a Claude Project — takes 90 seconds.**

Here's what you get for the time:
1. Open claude.ai → Projects (top left)
2. Create new project, name it "Store 2065 SOP"
3. Click the + button, upload your SOP PDF / Google Doc export
4. Now ask Claude anything about it: *"What's the closing checklist for fries?"* *"How long does the deep clean take?"* *"What's the policy on comping orders?"*
5. Claude can cross-reference it. *"If we're short-staffed and the closing SOP calls for three people, can I do it with two?"*

The win: you've built a searchable, explainable version of your SOP. Next time a new crew member asks "what do I do after the lunch rush?", point them to the Project chat instead of re-explaining. Five minutes now saves you hours over the next six months.

---

## 6. AI in the Wild — Restaurant Relevant

**Toast (the QSR POS) is now offering embedded AI for void/comp decisions.** A crew member marks an order for a comp. Instead of your manager having to review it ("why are we comping this?"), Toast's AI can flag unusual patterns — high comp rate for one crew member, comps clustering at shift change, comps spiking during busy periods. You get a summary: "This user comped 8 orders today (vs. 2 yesterday). True comp or error pattern?" It's not making the comp/no-comp decision; it's flagging the signal so you catch problems faster.

The real move: Toast is teaching its POS to recognize *behavior patterns*, not just transactions. That's the shape of restaurant AI for the next year — fewer robots doing the work, more AI acting as your second pair of eyes on what your team is doing.

---

## 7. Skill Up — Do This Today

**Practice the most useful Claude move for ops: uploading your P&L and asking "what should I worry about?"**

Here's your 10-minute task:
1. Export your last week's P&L from CrunchTime (or whatever you have).
2. Open Claude on your phone or desktop.
3. Upload the PDF.
4. Ask: *"What jumped compared to my historical average? What's the biggest variance and why should I care?"*

Watch what Claude does: it'll find the three things moving out of bounds (labor%, food cost%, maybe discounts). It won't tell you what to do about them, but it'll tell you what's worth your attention. Tomorrow, ask: *"If I wanted to fix [the biggest variance], what would I need to change?"*

**The question for next time:** Did Claude catch something in your numbers that you would've missed? Did it save you from chasing a small variance while missing a bigger one?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---

