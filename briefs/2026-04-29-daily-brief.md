# Bobby's Daily AI Brief — 2026-04-29
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude Opus 4.7 is now the default flagship model on claude.ai. It's shipping with improved instruction-following, better at multi-step problems, and handles longer contexts without drift. **What that means for you:** if you've been hitting moments where Claude misses a constraint or forgets part of your SOP mid-conversation, this update fixes that. Reload your Projects—they'll pick up the new model automatically.

The bigger play: Claude now officially supports voice input on iOS and web. You can record a voice memo at end-of-shift and dump it straight into Claude for summary → action items. For a GM doing 3-location walkthrough notes, this is a real time-saver. You don't have to transcribe; just record.

---

## 2. Prompt of the Week

Copy this prompt into Claude and save it as a Project. Use it every time you need to translate a messy CrunchTime export, manager note, or email into a clean action list:

```
You are a Five Guys operations analyst. Your job is to turn messy data, 
emails, or notes into clear, ranked action items with owner and due date.

Input: [PASTE MESSINESS HERE]

Output format:
# Priority Actions (Next 24h)
- Action: [specific thing to do]
  Owner: [who does it]
  Why: [one line reason it matters]
  Due: [specific time/day]

# This Week
- Action: [...]
  Owner: [...]
  Why: [...]
  Due: [day]

# Backlog
- Action: [...]

Rules:
- Only flag something Priority if Bobby or a DM said it's urgent
- "Fix the fry station" → "Recalibrate fry temp, test with thermometer, log reading"
- If an action needs approval, flag: [NEEDS APPROVAL]
- Use 24h clock, ET timezone
```

**Why this works:** The role setup ("ops analyst") teaches Claude to think like your operation, not like a generic assistant. The format rules force specificity—no vague "address staffing" nonsense, only "hire 2 line crew by Friday." The owner field makes it clear who does what. You paste it once, reuse it forever, and every output is actionable.

---

## 3. Use Case Spotlight

**The Problem:** You get a CrunchTime labor export. 200 rows. Hours for 20 employees across 4 shifts. You need to know: Who's over budget? Who's trending over? Who should we reduce?

**The Messy Way:** Copy-paste into Excel, hunt for who's over 40, cross-reference labor budgets, manually calculate trend.

**The Claude Way:** Upload the CSV to a Claude Project with a single prompt:

```
I'm attaching a CrunchTime labor export (CSV). 
For each employee this week:
1. YTD hours vs. their annual budget (are they over-pacing?)
2. This week vs. last week (trending up or down?)
3. Staffing action needed: "keep", "slight reduce", or "pull back immediately"

Format as a table: Employee | YTD % of Budget | Trend | Action.
```

**Result:** Claude returns a ranked list. You see immediately that Sarah is 8% over pace (trim her 2 shifts this week), and that two people are tracking *under* budget (opportunity to add cross-training shifts).

**What you get:** 3 minutes instead of 30. Decisions that are data-backed, not gut-feel. And when you execute the action, you can paste the results back next week and Claude learns your staffing velocity—trend data you can act on.

---

## 4. Gotcha of the Week

**The Trap:** Claude generates a number with confidence. A COGS percentage, a labor forecast, a "this outlet costs 3% less than that one." You paste it into a spreadsheet or cite it to your boss. Then you check the math and realize Claude hallucinated.

**Why it happens:** Claude is a language model. It's not a calculator. If you ask "what's 127 * 0.31?", it doesn't compute; it patterns. It knows the pattern of an answer, but it doesn't guarantee accuracy on novel arithmetic.

**The Fix:** **Never trust a number Claude generates without verification.** Show me the work. Ask Claude to break it down: "Show me the formula: (CrunchTime Labor Expense / Gross Sales) * 100 = Labor %." Now you can verify each input. If Claude cites a CrunchTime number, you verify it in CrunchTime directly. This takes 30 seconds and kills the hallucination.

Corollary: any time you're setting a budget or making a staffing call off Claude's math, read it back and verify. It's not being dumb—you're just using the wrong tool for a precision task.

---

## 5. New Tool Worth Trying

**Claude Projects + Mobile App + Voice = your shift recap automation.**

1. On your phone, open the Claude app (iOS or Android, free).
2. Create a new Project called "Shift Recap."
3. Upload one clean shift recap SOP as a reference document.
4. At end-of-shift, hit the voice button and record: "Food cost looked high today, Sarah called out, register was down for 20 minutes, customer complaint about fry wait."
5. Claude transcribes and formats it into your SOP template.
6. Takes 90 seconds. You're done.

**Why now:** You've got a smartphone. You're not typing recaps at 11 PM. Voice input means you capture what actually happened while you remember it, not a blank-slate email draft next morning. And if you feed the same Project your daily recap for a week, Claude starts spotting patterns: "register downtime on Tuesdays correlates with your shift manager being at lunch."

---

## 6. AI in the Wild — Restaurant Relevant

Toast (the POS system Five Guys locations use) just announced AI-powered labor forecasting built into their dashboard. It's not Claude—it's Toast's own model—but it watches your sales velocity and suggests staffing levels in real-time. **What matters:** every major QSR POS is racing to add AI. Toast is signaling that demand forecasting → staffing automation is table-stakes. 

Five Guys hasn't announced a native integration yet, but if you're not already pulling your Toast sales data and feeding it to Claude for a manual forecast, you're behind the curve. The corporates are coming for this workflow in 12 months.

---

## 7. Skill Up — Do This Today

**The exercise:** Grab your CrunchTime labor export from last week. Paste it into Claude. Ask: "Which employee had the most variance in shift length? What's a staffing pattern that might explain it?"

**What to expect:** Claude lists someone who had a wide range—maybe some shifts 4 hours, some 8. It patterns the reason: "Sarah gets reduced shifts Tuesdays/Wednesdays (inventory), full shifts Thu-Sat (peak)."

**Why you're doing this:** You're training yourself to see what Claude can extract from raw data without you directing it. You're also learning which patterns matter. A variance isn't bad if it's *intentional* (Sarah's intentional part-time window). But if it's chaotic (Sarah's hours jump randomly), that's a scheduling problem.

**Next time:** "Did you notice a pattern I should know about?" Compare what Claude surfaces versus what you already knew. That gap is where your coaching leverage is.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---
