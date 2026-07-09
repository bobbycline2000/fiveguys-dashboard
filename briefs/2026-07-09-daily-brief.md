# Bobby's Daily AI Brief — July 9, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude's API pricing dropped again this month, but that's not your signal. Your signal is simpler: Claude's batch processing (bulk jobs that run in the background) now supports file uploads. For you, that means you can dump a month of CrunchTime CSVs into one batch job overnight and get a consolidated variance report back while you sleep. No "send me a report, I'll work on it" cycle. You ask once, everything comes back structured.

The other thing: Claude Projects now supports linked docs. If you're running the daily brief, the schedule build, or the secret shop debrief, you can wire them all into one Project and Claude remembers the context between runs. Less re-explaining what you're doing each time.

Neither requires setup from you. Just useful to know the machinery got quieter.

---

## 2. Prompt of the Week

**Shift Recap to Action Items** — Paste this into Claude and upload a voice memo, email summary, or notes from your shift:

```
You are a restaurant operations manager's chief of staff. Your job is to turn messy shift notes into a clean action list.

Incoming data: [PASTE SHIFT RECAP HERE]

Your output:
1. **Critical issues** (impacts today's service or tomorrow's staffing) — numbered, one sentence each
2. **Action items** (who does what, by when) — Owner: Action — due date
3. **Heads-up to Crystal/ldavis** (things the Director and DM need to know) — plain language
4. **Staffing flags** — call-outs, no-shows, early leaves, anyone struggling
5. **What went right** — one thing the team nailed (frame for tomorrow's huddle)

Assume I'm busy. Give me signal, not noise. If you're unsure whether something is critical, ask me one question, then make the call anyway.
```

Why this works: It creates roles (chief of staff mindset), sets constraints (signal not noise, one question then decide), and gives you output you can action immediately without reformatting. The "what went right" section is not fluff — it's the piece you'll actually use in tomorrow's huddle because Claude found it, not because you have to remember it. Shift recaps are data you generate every day; this structure means you stop generating and start acting.

---

## 3. Use Case Spotlight

**CrunchTime Labor Variance → SOP Audit**

**The mess:** You pull a CrunchTime report. Actual labor is 3.5% over theoretical. You know it's not random — something in the process is letting hours creep. But the report is 40 lines of data in a table.

**The Claude move:**
- Paste the entire CrunchTime labor export into Claude.
- Ask: "Walk me through the hour-by-hour gaps. Which positions are over most? What does each gap tell me about how we're actually running vs. how we should?"
- Claude breaks it down: "Prep is +0.8 every Tuesday (holiday? training shift?). Grill is +0.3 consistently on weekends (no coverage buffer). Drive-thru is variable — high when you run short on front, low when front is fully staffed."

Now you're not guessing. You see the pattern. You know whether to tighten the schedule, add a line item for training, or hire coverage. That's not a report. That's decision-ready insight.

---

## 4. Gotcha of the Week

**The Confident Hallucination Trap**

You ask Claude: "What are CrunchTime's API rate limits?" Claude answers: "CrunchTime allows 1000 requests per minute with standard auth." Sounds specific. Sounds confident. Almost certainly wrong.

Claude invents numbers when it doesn't know them. It doesn't say "I'm not sure." It says "here's the answer" with full conviction. When you need real numbers — pricing, limits, API specs, competitor data — always verify with ONE source: the official docs or the vendor's support channel. Don't build around Claude's number.

For internal data (your labor, your sales, your P&L), Claude is reliable because you're giving it the primary source. For external facts, treat Claude as the first draft. Verify before you build on it.

---

## 5. New Tool Worth Trying

**Claude on iPhone — Voice Mode for End-of-Shift Recap**

1. Download Claude app (iOS).
2. Tap the microphone icon next to the text box.
3. Start talking: "Here's what happened on my shift today. We were down Bri all day, drive-thru got slammed at 7, we ran out of pickles by 8:30, and I had to call Crystal to authorize early close-out."
4. Claude transcribes + responds with a recap + action items.
5. Screenshot it or copy it to notes.

Literally 3 minutes. No typing one-handed at 10 PM. Solves the "I know I need to log this but I'm tired" problem. Voice mode is native on iPhone now; Android is coming soon.

---

## 6. AI in the Wild — Restaurant Relevant

**Toast (the POS your competitors use) just released predictive labor scheduling.** Their AI watches your sales patterns and predicts how many people you'll need on a given day/time, down to the position. It's not perfect, but it's real enough that operators are reporting 1–2% labor saves without cutting service.

Why you should know: Toast is ecosystem software. That capability will cascade to R365, HotSchedules, other major POS platforms. In 12 months, every QSR with modern POS will have AI-predicted schedules as table stakes. Teamworx (which you use) will either add it or get left behind. You don't need to do anything today, but when Teamworx announces this feature, it's not a "nice to have" — it's competitive parity.

Five Guys corporate probably knows this is coming. Watch for whether they push it down to franchisees or keep it corporate-only.

---

## 7. Skill Up — Do This Today

**Practice: Variance Diagnosis with One Real Number**

Pull one real week of your food cost variance (the gap between what you spent on food and what you should have spent). Upload it to Claude. Ask this exact question:

"Walk me through this week's food cost variance line by line. For each category that's off by more than 3%, tell me: is this a usage issue (we used more than we should have), a waste issue (spoilage/waste), or a purchasing issue (price spike). For each diagnosis, give me one yes/no question I could ask my team to confirm."

Don't expect Claude to have THE answer. Look for whether its questions make you think differently about the problem. That's the skill — Claude helping you ask better questions of your own data.

**Next time we talk, tell me:** Did Claude's diagnosis match what you suspected, or did it point to something you hadn't considered?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---

**Brief generated:** 2026-07-09 05:37 AM ET  
**Next brief:** 2026-07-10 07:00 AM ET
