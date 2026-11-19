# Bobby's Daily AI Brief — 2026-11-19
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

**Claude 3.5 Sonnet is fully shipping.** It launched as the fastest model Anthropic has shipped — the beta tag is gone. If you've been holding back on deploying Claude in your operations because you thought it was "experimental," stop. This is the production line now. Sonnet handles everything from parsing CrunchTime exports to drafting emails to analyzing sales trends, all in under 2 seconds. For a 21-person crew operation like 2065, that speed matters — your morning dashboards aren't stuck waiting 30 seconds per API call.

The bigger move: **Claude can now see images natively**, no extra API call. Upload a screenshot of your CrunchTime forecast, a photo of an inventory count sheet, a Par Brink PDF, whatever — Claude reads it in context. No more transcribing. This is the feature that actually solves "I have this spreadsheet/image and I need an answer fast."

---

## 2. Prompt of the Week

**Copy-paste ready prompt for shift recap audio notes:**

```
You are Bobby's shift operations analyst. Your job is to listen to raw operational notes and extract 
actionable items for the Five Guys crew and management team.

Analyze this shift debrief note and produce:

1. **What went right today** (2-3 bullet points, specific to what Bobby described)
2. **What broke or slowed us down** (root cause, not symptom — if the drive-thru was slow, was it staffing, 
   equipment, or process?)
3. **One thing to fix before tomorrow** (prioritize by impact to labor cost or customer experience)
4. **For the team meeting this week** (one message Bobby should deliver based on today's patterns)
5. **Any trend to watch** (if this is the second time this week this happened, flag it)

Be specific. No corporate platitudes. If Bobby said "slow day," dig into whether that's normal for Wednesday 
or a warning sign.

Debrief note:
---
[PASTE BOBBY'S VOICE NOTE TEXT HERE]
---
```

**Why this works:** You're giving Claude a role (operations analyst, not generic AI), specific output structure (not "summarize"), and context (Bobby's business, not abstract). The five outputs form a chain that goes from observation → diagnosis → action → communication → pattern. Bobby doesn't have to stitch pieces together. And the last instruction ("be specific") trains Claude to actually think before defaulting to "good communication is key." That matters.

---

## 3. Use Case Spotlight

**Taking CrunchTime performance variance and turning it into next-week's labor plan.**

**Before:** Bobby opens Performance Metrics in CrunchTime, stares at "Actual vs Theoretical" labor variance (maybe +12% or -8%), scribbles notes about "need fewer people" or "had too many on expo." Gut feel. Inconsistent week to week.

**After:** Upload this week's Performance Metrics screenshot to Claude with this prompt:

```
I'm showing you my CrunchTime Labor Variance report for the week of [DATE]. 
Actual vs Theoretical shows [VARIANCE %].

For next week's same days/times, what staffing adjustments would you recommend? 
Give me:
- Specific shift changes (which shifts to cut or add people)
- Expected variance impact (what % should we hit if we nail this)
- One risk (what could throw off these assumptions)
```

Claude reads the chart, sees which dayparts are blowing variance, and gives you back a staffing blueprint instead of a gut call. Test it next week — you'll see if your variance tightens up. If it does, you've found a repeatable process.

---

## 4. Gotcha of the Week

**Claude will confidently invent numbers to fill gaps.**

You ask: "What was Five Guys' revenue in 2025?" Claude doesn't say "I don't know." It says "$XX billion" with full conviction. The number is often plausible-sounding. Completely made up. Happens more when Claude is trying to be "helpful" by finishing your thought.

**The fix:** Always follow data questions with *"Show me your source"* or *"Where did you get that number?"* If Claude says "I estimated based on..." or "This is my best guess," reject the answer and move on. For real data, ask it *after* you've checked it yourself. Use Claude to interpret your actual numbers, not to generate numbers for you.

(This is why the brief showed Sweetgreen using AI for recommendations, not revenue predictions. Sweetgreen is making decisions with their own data. Big difference.)

---

## 5. New Tool Worth Trying

**Claude on your iPhone — 5 minutes to set up.**

1. Open the App Store on your phone.
2. Search for "Claude" (by Anthropic).
3. Download, sign in with bob.cline2000@gmail.com.
4. Open Claude and try this: *"I'm at work and need to remember something for Bobby. Here's what happened today: [paste a quick note]."*

Do that three times this week. Record what you notice — does it help you remember, does the formatting work, is it faster than typing an email to yourself? One specific use case will emerge. That's your signal that it's worth keeping on your phone.

---

## 6. AI in the Wild — Restaurant Relevant

**Sweetgreen's AI bowl customizer (live now).** Ask a Sweetgreen kiosk "I want to meet my protein goals but under 400 calories" or "make it spicy and no corn," and their AI builds a bowl recommendation from their menu in real time. No cookbook, no manager override — the AI understands their ingredient constraints and nutritional data.

This is a live demo of what Bobby could do at 2065: *"Show me a combo that hits my food cost target for today's daypart"* or *"What's the best use of this morning's inventory?"* Sweetgreen didn't build a custom ChatGPT. They plugged Claude into their POS data and menu. That's the template.

---

## 7. Skill Up — Do This Today

**Grab a CrunchTime export and have Claude teach you something about it.**

Steps:
1. Open CrunchTime, go to any report you usually export (Sales, Labor, whatever).
2. Take a screenshot.
3. Paste it into Claude with: *"What's the single biggest trend you see in this report? What would I be missing if I didn't look at [X part of the data]?"*
4. Read what Claude says.
5. Check if Claude is right by looking at the actual numbers yourself.

**Next time:** Text me one sentence: *"What did you catch that I would have missed?"* Don't overthink it — just name the one thing.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---

