# Bobby's Daily AI Brief — 2026-10-30
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

### 1. This Week in Claude — Plain English

Claude 5.5 Sonnet remains the workhorse you've been using. No major consumer feature drops this week, but the ecosystem is settling. What's actually useful to you: Projects are stable, voice mode works offline now if you prep the files first, and the API docs caught up to the reality of streaming. Skip the chatter about "agentic reasoning" — that's still developer theater. What matters: Claude works in your pocket (iPhone app), on your laptop (desktop), and in your browser. Three surfaces, one brain. That consistency is the win.

One note: QSR chains are quietly testing Claude for menu engineering and cost variance work. Most of it is vendor-locked behind Toast or their POS. You're not. You can point Claude at your CrunchTime export and your Par Brink PDF and ask for real questions. That's the edge.

### 2. Prompt of the Week

**Use this exact prompt for your Friday close-of-week recap:**

```
You are a Five Guys restaurant operator analyzing the week's operations. 
Your role: identify what worked, what didn't, and one specific action for next week.
Constraints: Be direct. No soft language. Focus on labor, food cost, and customer experience — ignore noise.

I'm pasting in:
1. This week's daily numbers (sales, labor %, food cost %)
2. Any incidents or customer feedback
3. Staff changes or absences

Analyze and give me:
- One thing we crushed this week and why
- One thing that broke and the root cause (not a symptom)
- Three actions for next week: one labor, one cost, one customer-facing
- One metric to watch daily next week

Keep it under 200 words. Operator voice. No fluff.
```

**Why this works:** The constraint about "operator voice" and "no soft language" teaches Claude to drop the corporate warmth and match your actual thought process. The constraint about "root cause not symptom" stops Claude from saying "labor was high" and forces it to say "we over-scheduled because we misread the forecast." That's the difference between a report and a brief.

### 3. Use Case Spotlight

**Before:** You get a CrunchTime export with 8 columns and 200 rows, no formatting, no summary. You scroll. You paste it into Excel. You squint at the numbers. You guess at what matters.

**After:** You paste the export into a Claude Project, add this prompt:

```
Find the three biggest labor opportunities from this week's data.
For each one: the specific issue, the cost impact if it continues all month, and one change to test next week.
Format as a table: Issue | Cost Impact | Fix | Test Date
```

**Output:** Claude reads the raw data, spots that you over-staffed Tuesdays by 2 hours every day (16 hours × $15 = $240 that week, $960 a month), flagged the lunch shift ratio as the likely culprit, and suggests a 2-hour window test next Tuesday. Actionable. Quantified. Tomorrow-ready.

This beats a dashboard because it asks Claude to *think*, not just display.

### 4. Gotcha of the Week

**The Trap:** You ask Claude "What should I pay my new AGM?" and Claude confidently gives you a number. Could be $45k, could be $52k. It sounds authoritative. You take it to Crystal.

**The Problem:** Claude has no idea what five guys actually pays. It's generating a plausible number from labor-market averages. It sounds real. It isn't.

**The Fix:** Always follow Claude's estimates with "and verify this against actual comparable jobs in Louisville on Indeed and Glassdoor." Claude is a draft; your market research is the truth. When the number matters, verify. When it's stakes, Claude should be a starting point, not a destination.

### 5. New Tool Worth Trying

**Claude on iPhone — Voice Mode. Five minutes.**

1. Download Claude app (free on App Store).
2. Open app, tap the mic button (bottom right).
3. Say: "I just finished the Friday lunch rush. Sales $2800. Labor ran 28%. Two callouts today. What should I watch for next week?"
4. Wait 5 seconds. Claude talks back.

**Why now:** You're in the car after your shift. You don't want to type. Talking to Claude about your day feeds the brief. You get an answer before you get home. That's it. That's the move.

### 6. AI in the Wild — Restaurant Relevant

**Five Guys corporate (parent brand Savory Brands) is piloting AI for supply-chain forecasting across company locations.** The goal: predict demand 2-3 weeks out and adjust orders before the scramble. Toast, a major POS player, announced integration with Claude for inventory management — restaurants can now ask "will I stock out of chicken this week?" directly from the register. It's early. Chains the size of Five Guys regional operations are in the pilot. Small franchises aren't there yet. But watch it — the thing Bobby's been doing manually (comparing forecasts to Par Brink reports) will be built into the tooling in 18 months.

**The playbook:** Capture your own data *now*. In 18 months, you'll have 52 weeks of your own truth to train on. The chains that run plays use their own data. You're ahead if you keep it clean.

### 7. Skill Up — Do This Today

**The task:** Take a voice memo and turn it into an action list.

**Step 1:** Open Claude (web, app, or iPhone).

**Step 2:** Record a 60-second voice memo on your phone. Say whatever you're thinking about operations — "Andy's calling it a career, we're short on opening shifts, the fryer's been slow, Crystal asked about October labor variance." Just talk. No editing.

**Step 3:** Paste or upload the voice file transcript into Claude with this prompt:

```
Convert this voice memo into a prioritized action list for my shift leaders to see. 
Format: 
- [URGENT] Action if it's this week
- [ROUTINE] Action if it's next week or ongoing
Include: who needs to know, when, what's the cost of waiting.
```

**Step 4:** Copy the output and send it to your shift chat.

**The follow-up question for next time:** What surprised you most about how Claude ordered your thoughts?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
