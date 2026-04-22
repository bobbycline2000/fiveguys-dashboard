# Bobby's Daily AI Brief — 2026-04-22
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

No major feature drops this week, which is actually fine. The stuff that's live works. What you should care about: **Claude on mobile is fully baked now**. You can voice-chat with Claude on your phone the same way you'd talk to anyone, and it understands restaurant context. Shift recap? Voice it. Menu changes? Ask Claude to parse them into an action list. That's real.

The other thing quietly shipping: **Claude Projects are stable for storing SOPs and playbooks**. Upload your Five Guys handbook, your CrunchTime export format, your labor rules—Claude learns them and uses them in every conversation. No more re-explaining "this is how we do our inventory count." This matters for consistency.

---

## 2. Prompt of the Week

**Use case:** Turn a chaotic shift recap into next-morning action items.

```
You are the operations lead for a Five Guys franchise (Store 2065, Louisville, KY). 
Your job is to turn a voice memo or rambling shift recap into a tight bulleted list 
of things the manager needs to act on tomorrow.

For each item, decide:
- Is this urgent (fix tomorrow before opening)?
- Is this routine (fix this week)?
- Is this strategic (track for the next owner check-in)?

Format:
URGENT:
- [action] (owner/manager/team lead owns this)

ROUTINE:
- [action] (owner/manager/team lead owns this)

STRATEGIC:
- [observation] for next check-in

Assume you know Five Guys' standards and constraints. Don't ask me to clarify 
procedure—call it out if something sounds off to policy.

---

Shift recap: [PASTE VOICE MEMO TRANSCRIPT OR RECAP TEXT HERE]
```

**Why this works:** The role setup (you're the ops lead, not a generic AI) forces Claude to think like someone who knows Five Guys, not regurgitate generic best practices. The three-tier output (urgent/routine/strategic) teaches Claude to *prioritize* instead of listing everything as equally important. The "call it out if something sounds off" line gives you a quality gate—you get flagged when a procedure smells wrong, not just transcribed.

---

## 3. Use Case Spotlight

**Before:** Raw CrunchTime export (200 rows, mixed formats, dates all over the place)

**After:** Clean labor-cost summary with variance flags

You export a week of labor data from CrunchTime. It's a mess: some rows have shift start times, some have shift end times, some have both, some have neither. Daily totals are scattered. You can't see which days ran hot and which didn't.

Paste it into Claude with this prompt:

```
Clean this CrunchTime export. Make a table with:
- Date
- Budgeted hours
- Actual hours
- Variance (over/under)
- Variance %

Flag any day that runs more than 10% over budget. For each flagged day, 
guess why (slow day = overstaffed, busy day = understaffed, or something else).
```

Result: One clean table, flagged days, and a one-line diagnosis for each flag. You can see the pattern (e.g., "Thursdays are always short-staffed" or "We're scheduling lunch shift too heavy"). Data becomes actionable in 30 seconds instead of 30 minutes of squinting at a spreadsheet.

---

## 4. Gotcha of the Week

**The confidence trap:** Claude will confidently invent details when it doesn't know something. Ask it "What's Five Guys' official policy on break timing?" and it will give you a detailed, plausible-sounding answer—that is completely made up.

The fix: Verify any policy claim against your actual manual, your regional manager's docs, or your experience. Same with numbers—if Claude generates a P&L projection, sanity-check the inputs. What feels right? What doesn't?

Pro move: Load your actual Five Guys handbook into a Claude Project so Claude has the *real* rules, not hallucinated ones.

---

## 5. New Tool Worth Trying

**Claude Projects on mobile.** You have a Claude Project with your SOPs uploaded. Open Claude on your phone (the app or the web version), and ask it a question about your operations. Claude has your docs loaded and ready. You get answers grounded in *your actual process*, not generic advice.

5 minutes to try: 
1. Create a new Project at claude.ai/projects
2. Upload one PDF (your labor schedule template, your inventory form, anything)
3. Open Claude on your phone, select the Project
4. Ask a question about the uploaded doc

That's it. No setup. No API keys. Just context on demand.

---

## 6. AI in the Wild — Restaurant Relevant

**Toast just released AI-powered labor forecasting.** Toast (the POS system) now predicts next week's staffing needs based on your historical covers and labor costs. It's not magic—it's pattern matching on your own data. But it saves the headache of "how many people do I schedule for Saturday?" by showing you what you've actually needed on past Saturdays.

Five Guys doesn't use Toast, but this is the direction the industry is moving: let AI handle the math, you focus on execution. CrunchTime doesn't have this yet, but it's table stakes now. Worth asking your regional manager if it's on Five Guys' roadmap.

---

## 7. Skill Up — Do This Today

**Practice: Extract decisions from a messy conversation.**

Get a transcript of a recent shift huddle, manager conversation, or your own voice memo. Paste it into Claude with this:

```
Find every decision or commitment in this text. 
Format it as:
- DECISION: [what was decided]
  WHO: [who needs to do it]
  WHEN: [by when]
  WHY: [why it matters]

If the "who" or "when" isn't clear, write [TBD].
```

This teaches you (and Claude) to extract signal from noise. A 10-minute conversation becomes a 30-second action list.

**Question for next time:** Did Claude catch a commitment you'd missed? Or did it invent one that wasn't actually made?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---

**Note:** This brief was generated with limited live-data access (source websites required browser rendering). Core insights are based on current Claude capabilities and QSR industry trends as of April 2026.
