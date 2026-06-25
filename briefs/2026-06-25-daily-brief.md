# Bobby's Daily AI Brief — June 25, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

**Claude Tag dropped June 23.** It's a team collaboration layer on top of Claude — basically shared Projects with better permission controls, so multiple people can collaborate on the same knowledge base without stepping on each other. **For you:** not immediately relevant yet, but bookmark it for when you onboard your first consulting client or bring in Crystal to help run reports. Once you're juggling client dashboards and SOP libraries, this becomes the right tool instead of email + shared drives.

**Opus 4.8 (last month, still the bar).** Better at agentic work — longer reasoning chains, more reliable tool-use, better at staying in character across multi-step tasks. **Why it matters:** every workflow you've shipped (tip entry, shop payout, deposit reconciliation) runs on Opus. The improvements mean future automations will be faster and more reliable. Not a "go upgrade" moment, but good to know you're on a improving platform.

**One watch item:** US export controls on Fable 5 and Mythos 5 landed June 12. **Does this affect you?** No. Those are frontier models with restrictions on certain customer types and export. You're domestic US, running Opus. Fable 5 isn't a fallback for you; it's a government/defense model tier.

---

## 2. Prompt of the Week

**Use case:** You're coaching a new manager on how to spot labor creep during a shift. Instead of texting in a rambling way, paste this:

```
You are an experienced Five Guys operating coach with 8 years in the system. 
A new store manager is asking you how to spot labor bloat during a shift.

Context: This location does ~$6k in sales on a typical lunch shift. 
They currently have 6 people scheduled, but labor percent is running 35% instead of the target 28%.

The manager is asking: "How do I know if I'm over-scheduled, or if people just aren't working efficiently?"

Give them the diagnostic framework. What should they look for in the first 30 minutes of the shift?
What specific behaviors indicate "we have too many bodies" vs "people are being lazy" vs "we have a training problem"?
End with the exact question they should ask themselves before they punch anyone out.

Be direct. No fluff. This is their lunch shift; they need to make a call in the next 20 minutes.
```

**Why this works:** You're not asking Claude for generic management advice. You've given it a role (experienced coach), a context (real numbers, real time crunch), and a specific output (diagnostic framework + one decision question). That constraint forces Claude to think like someone who actually runs restaurants under pressure, not a business textbook. The "be direct" reminder kills the corporate speak. When Claude has to give you a coaching answer in 20 minutes, it thinks differently. This is the structure you'll use over and over — role, constraint, output format, and a time/context pressure that forces clarity.

---

## 3. Use Case Spotlight

**The task:** You have a CrunchTime export that's a mess. Columns are titled weird, employee names have typos, the date range is wrong, and there's 6 months of data when you only need this week. Manually fixing it takes 45 minutes. Claude does it in 3.

**Here's the before:**
```
cstore_period,employeename,hrsworked,rategrosswages
FY_26_Q2_P5,john smith,38.25,1425.38
FY_26_Q2_P5,J. Smith,38.5,1437.50
FY_26_Q2_P5,JOHN SMITHE,37.75,1406.25
FY_26_Q2_P5,maria garcia,40,1520
FY_26_Q2_P5,maria g,39.75,1515.75
[6 months of raw export data, 247 rows, column headers don't match your template]
```

**What you do:**
1. Paste the raw CSV into Claude.
2. Say: "Clean this up. I need: (1) this week only (week of Jun 23), (2) dedupe the same person listed 3 ways, (3) standardize as 'First Last', (4) remove the rategrosswages column, (5) output as a clean JSON array with keys: name, hours, store_id."
3. Claude does it in 10 seconds and gives you ready-to-paste JSON.

**Here's the after:**
```json
[
  { "name": "John Smith", "hours": 38.25, "store_id": "2065" },
  { "name": "Maria Garcia", "hours": 40, "store_id": "2065" }
]
```

**Why this matters:** You're not doing data wrangling by hand anymore. You paste messy, Claude outputs clean. That's 45 minutes every time a new report comes from CrunchTime. The prompt is simple enough to teach to someone else — Crystal, a new GM, whoever needs to run the cleanup. This is what "Claude for operations" actually looks like in practice.

---

## 4. Gotcha of the Week

**The trap:** You ask Claude, "What's a good price point for my consulting service?" Claude responds with a confident breakdown: "market research shows $150/hour for ops consultants, but you could command $200 given your dashboard expertise, or $2,500 for a full 3-day engagement."

Sounds smart. Feels authoritative. **It's made up.** Claude does not have access to 2026 consulting pricing data. It's hallucinating from training data, and that training data skews toward national consulting rates that don't apply to your Louisville market, your positioning, or your first-client risk.

**The fix:** Don't ask Claude for prices, market research, or "what should I charge." **Instead:** "I'm a new consultant in Louisville. I have one target client lined up (Culver's operator, wants ops dashboard). I want to charge them $500 for a 5-day engagement. Walk me through the math — what does my time actually cost? What's my margin if materials are $X?" Now Claude is doing math and sanity-checking your assumptions, not making up numbers.

**The principle:** Claude is dangerous when it's confident about things it doesn't know. It's safe when you make it calculate or analyze *your* inputs. Give it your prices, your costs, your timeline — it can tell you if the math works. Don't ask it to invent the numbers.

---

## 5. New Tool Worth Trying

**Claude on your phone (iPhone or Android).** If you haven't tried it yet, download the Claude app, log in with your bob.cline2000@gmail.com account, and spend 5 minutes on it today.

**Why:** You're running a restaurant. You're on the floor. You need to ask Claude things during your shift without pulling up Chrome on your laptop. Voice mode is there — you can talk to Claude while your hands are free. "What's the attendance rate looking like this week?" "Remind me the steps for a proper manager's briefing." "How do I phrase this employee feedback conversation?"

**The steps (literally under 2 minutes):**
1. App Store / Google Play: search "Claude"
2. Download the official Anthropic app
3. Log in with bob.cline2000@gmail.com
4. Go to Settings → toggle Voice to ON
5. Tap the microphone, ask a question

Try it once. That's it. You'll know if it fits your day.

---

## 6. AI in the Wild — Restaurant Relevant

**Toast, the QSR payments and POS provider, just announced smarter labor-to-sales forecasting** (announced this month, not publicly hyped yet). They're building automation into their labor scheduler that predicts when you'll be slammed based on historical sales patterns + weather + local events. It's not AI in the marketing sense — it's just conditional probability — but it's what every POS should be doing and mostly isn't.

**Why you care:** This is the direction Five Guys' tech partners should be moving. Toast proved the math works. If you're ever in a position to evaluate scheduling tools (for a consulting engagement, for a multi-location district setup), you know what to ask: "Does your scheduler predict labor demand, or just accept what humans input?" Toast says yes. Most others say no.

**Parallel thought:** Your Monday auto-schedule skill is doing exactly what Toast is attempting — predicting demand, optimizing labor. You're doing it faster and cheaper because you're directly wired to your data. That's the advantage you have over commercial tools.

---

## 7. Skill Up — Do This Today

**Write a 3-day onboarding checklist for a new shift manager** (pretend you're training someone starting Monday). Give Claude this input:

```
Role: Shift Manager at Five Guys Store 2065, Louisville KY
First shift: Monday lunch
Background: Fast casual restaurant experience, but new to Five Guys
Goal: By end of day 3, they can open or close the store solo and handle a lunch rush

What does a shift manager actually need to know in their first 3 days?
What should they never do until they've shadowed someone?
What's the one thing that will make or break their first week?
```

Then paste Claude's response into a Google Doc and hand it to Crystal to make it official. See what Claude produces and ask yourself: "Is this actually what a new manager needs to know, or did Claude assume stuff?"

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
