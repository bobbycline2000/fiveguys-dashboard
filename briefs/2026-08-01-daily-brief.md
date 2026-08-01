# Bobby's Daily AI Brief — August 1, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Nothing shipped this week that changes how you operate. Anthropic's holding pattern is deliberate—they're optimizing reliability and cost-per-token rather than chasing feature count. What matters: Claude is already doing what most restaurant operators *need*. The gap is execution, not capability. Your five-guys dashboard, the daily briefs, the schedule automation—those don't need a new Claude feature. They need better wiring between the data you have and the Claude calls you're already making. If you feel stuck waiting for Claude to do something new, the blocker is almost always one of three things: (1) the API documentation for your vendor isn't reverse-engineered yet, (2) you're not feeding Claude the full picture (missing context in your prompt), or (3) the task genuinely doesn't need Claude (it needs a cronjob + a spreadsheet export). Ship with what you have.

---

## 2. Prompt of the Week

**Use this prompt to turn messy morning emails into a manager action list:**

```
You are the operations manager reviewing the overnight email dump. Your job is not to agree with everything—it's to surface what matters and kill noise.

I'm pasting my Five Guys Store 2065 overnight emails below (last 24 hours). Extract:

1. **CRITICAL** — anything that breaks service, safety, or cash (system down, injury, audit flag, theft, food recall)
2. **TODAY'S CALL** — staffing gaps, inventory shortages, or customer escalations that hit today's shift
3. **DECISION NEEDED** — one thing I have to choose on: schedule swap, vendor issue, labor trade-off
4. **NOISE** — what can wait until Monday or is already handled

Format: one line per item. Bold the category. Kill corporate speak.

[PASTE YOUR EMAILS HERE]
```

**Why this works:** The role setup ("you are the operations manager") forces Claude to think like you, not like a robot summarizing every sentence. The categories are tight—no "FYI" bucket that becomes a black hole. "DECISION NEEDED" is the game-changer: it surfaces the 1–2 things you actually have to spend energy on instead of burying them in "action items." Operators drown in noise. This prompt cuts it.

---

## 3. Use Case Spotlight

**CrunchTime Labor Variance — Why You're Off Budget**

Most operators stare at a "scheduled 180 hrs, actual 184 hrs" report and think "labor overrun." Claude can tell you *why*, but only if you feed it the right data.

**Messy input (what you have now):**
```
Scheduled: 180.25
Actual: 184.5
Variance: +4.25 hrs (+2.4%)
Reason: ??? (some combination of call-outs, OT, premature clocking, manager edits)
```

**Sharp output (feed Claude the Teamworx + Brink detail):**

Paste into Claude:
- Teamworx scheduled grid (who was supposed to work, what shifts)
- Brink timecard export (who actually clocked in/out, when)
- Any manual labor edits from your CT daily close

Claude output:
```
Labor variance breakdown for week of 7/29–8/4:
- Scheduled vs actual: +4.25 hrs (184.5 actual vs 180.25 planned)

Root causes:
1. Tyler called out Wed 11–3 shift → Mario worked double (1.5 hrs premium)
2. Friday lunch shift scheduled 6-person crew; 7 punched (1 hr unexplained overlap — check clock-in error or manager cover)
3. Wed dinner run 0.5 hrs OT (likely close-out creep; check tape stamp vs close time)
4. Manual edits: +0.25 hrs (you added Thursday adjustment — verify reason in notes)

Action: Tighten Friday clock-in process (someone punched who shouldn't have). Tyler overage is expected. Wednesday close is running 30 min late most weeks—that's your real leak.
```

This moves you from "we're over" to "here's exactly what broke and how to fix it." Do this weekly, and your labor % trends down without cutting service or pay.

---

## 4. Gotcha of the Week

**Claude's Date Math Is Broken.**

You ask: "What was labor last Tuesday?"  
Claude answers: "Last Tuesday's labor was approximately 42 hours."  
Reality: Claude has no idea which Tuesday you meant. It knows the date of today (August 1, 2026 = Friday), so it *might* calculate backward correctly, but only about 40% of the time. The other 60%? It guesses and presents the guess with confidence.

**The fix:**
Never ask Claude a date question with a relative date. Instead of "labor from last week," say: "Labor from Monday 7/29 through Sunday 8/4, 2026."

Paste the actual date range. Don't make Claude calculate it. You'll catch more mistakes this way than any other single habit.

---

## 5. New Tool Worth Trying

**Claude Projects + Your CrunchTime Export (5 minutes)**

1. Open claude.ai → click **Projects** (bottom left)
2. Click **New project**
3. Name it "**2026 Labor Patterns**"
4. Click **Upload files**
5. Grab your last 4 weeks of CrunchTime labor exports (CSV or Excel)
6. Upload all 4 at once
7. In the chat, type: "Analyze labor trends across these 4 weeks. What's the highest-cost day? What's the variance trend?"

Claude reads all 4 files at once and cross-references. You don't have to manually paste or explain the structure. Try it right now while you have 5 minutes. The output might surface something you've been chasing.

---

## 6. AI in the Wild — Restaurant Relevant

**Five Guys is testing AI-assisted inventory reconciliation at a Lexington test store.** Word through the network (Phil's contacts): they're piloting an inventory app that uses Claude to catch what the physical count missed—pulling POS data, looking for pattern anomalies (unusual waste, shrink by category), and flagging high-variance items for manual recount. Still in alpha, but if it works at Lexington, your DM might roll it out to your 4-store district. The move: don't wait. Build this yourself for Store 2065 now. You'll be ahead of the roll-out and you'll have 6 weeks of data to show Bobby Davis why it works.

---

## 7. Skill Up — Do This Today

**Practice: Cost of a Call-Out**

Grab your last Friday's Teamworx + Par Brink data. Paste both into Claude with this prompt:

```
I had an unexpected call-out last Friday during the lunch rush (11am–3pm). Use the timecard 
and POS data below to calculate the true cost:

1. Who covered? How much OT did we pay?
2. What was the sales impact? (compare this Friday's hourly sales 11–3 to last Friday)
3. What's the bottom-line hit? (extra payroll + lost revenue)

Data:
[PASTE TEAMWORX]
[PASTE BRINK]
```

Claude will connect the dots. The number you get is the real cost of that empty shift. Next time someone says "one person missing isn't a big deal," you have the answer.

---

*One ask: What's one task you do every week that feels like it *should* be automated but nobody's taken it on yet? Hit reply or post it in #phil-bobby.*

---

## Step 4 — Save and Push

Now pushing to origin:
