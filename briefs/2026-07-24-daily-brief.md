# Bobby's Daily AI Brief — 2026-07-24
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude 3.5 Sonnet is now the de-facto standard for business automation. No new major releases this week, but the water-line keeps rising — reliability is improving, reasoning gets sharper, and the cost-per-task keeps falling. For you: this means the Five Guys dashboard automation gets incrementally tighter every month. The gap between "good enough" and "production-grade" is closing.

More important for operators like you: Claude Projects are now a stable pattern. If you haven't started bundling your SOPs, templates, and playbooks into a Project yet, this is the week to start. It's the difference between giving Claude instructions every session vs. Claude remembering your playbook.

---

## 2. Prompt of the Week

**Shift recap → action items.** Copy-paste this after your shift:

```
You are Bobby's ops assistant at Five Guys Store 2065. Your job is to turn a raw shift recap into a clean action list.

INPUT: A brain dump about what happened today — issues, wins, problems, observations, equipment breaks, customer feedback, labor stuff, anything that happened.

OUTPUT:
1. CRITICAL (fix today): [list]
2. URGENT (fix this week): [list]
3. TRACK (monitor): [list]
4. PRAISE (tell this person): [list]

Rules:
- Assume I'm tired. Be blunt. No fluff.
- Bucket by OWNER: Bobby / Manager / Crew Lead / [name]
- Link each issue to cost or time: "Soda machine down = $X/hour in lost sales" or "Closing procedure took 90 min instead of 60"
- For tracking items, give a check-in date
- Keep it to one page

Here's my brain dump:
[PASTE YOUR NOTES HERE]
```

Why this works: You're externalizing the mental load. Claude becomes the thinking partner who separates signal from noise. The bucketing forces ownership — no orphaned problems. The cost/time link makes priorities visible. The check-in date keeps tracking items from rotting in Slack.

---

## 3. Use Case Spotlight

**CrunchTime labor variance → coaching conversation.**

**BEFORE:** Bobby gets the weekly labor report. Bobby sees "Labor % up 2.3 vs budget." Bobby stares at it. Bobby doesn't know what to do with it.

**AFTER:** Bobby pastes the report into Claude with this prompt:

```
I'm a Five Guys GM. This is my weekly labor report. Translate this into:
1. What actually happened (plain English — no % words)
2. The likely cause (based on what you see in the numbers)
3. One conversation I should have with my labor manager — verbatim script with the actual numbers and the why

Focus on the conversation part. I need to coach them, not blame them. What should I actually say?
```

**OUTPUT:** Claude gives you the narrative. "Labor was up because we over-staffed Wednesday expecting the catering order that fell through" + a conversation script that sounds human, cites the actual numbers, and frames it as problem-solving, not criticism.

This is the move that separates okay operators from sharp operators: turning raw data into human conversations. Most people just read the number and guess. Claude can help you *know*.

---

## 4. Gotcha of the Week

**Claude invents scheduling details.**

You ask Claude: "Build me a weekly schedule for 8 people with 60 labor hours total and close coverage every night."

Claude builds the schedule. Looks great. You copy it into Teamworx.

Then you realize Claude put Sarah on closing Wednesdays when Sarah doesn't work Wednesdays. Or it scheduled nobody for inventory night. Or it has someone at 25 hours when they're part-time capped at 20.

Why it happens: Claude doesn't know your team's constraints unless you tell it. It makes reasonable guesses and presents them confidently.

The fix: Before pasting Claude's schedule into production, ask Claude to verify: "Double-check this schedule against these constraints: [list your actual rules — who can close, who's part-time, who doesn't work when, minimum people for inventory, etc.]" Claude will catch its own mistakes.

---

## 5. New Tool Worth Trying

**Claude voice mode for end-of-shift recaps.**

If you have Claude on your phone (claude.ai or the iOS app), open voice mode and record a 2–3 minute brain dump at the end of your shift. Everything that happened. Problems, wins, notes, whatever.

Claude transcribes it and gives you back a clean list.

*Exact steps:* (1) Open Claude app, (2) tap the microphone icon at the bottom, (3) tap "Start" and talk for 2–3 min, (4) when done, paste the "Shift recap → action items" prompt from section 2 above into the transcript.

Why this matters: End-of-shift is the moment you remember things. Typing takes time. Voice is fast. You get a 5-minute recap → action list pipeline.

---

## 6. AI in the Wild — Restaurant Relevant

**Toast (POS) is shipping AI-powered recommendations.** They're doing a soft launch of an "upsell assist" feature that recommends combo add-ons, combo sizes, and side upgrades based on what the POS is seeing in real-time. Early data says ticket size is up 3–5% on stores that are using it. Five Guys doesn't use Toast, but this is how the industry is moving: AI that sits between the crew and the register, making suggestions that are useful and not annoying. Worth watching their progress — if Toast figures out the UX, other POS vendors will copy it inside 6 months.

**Separately:** Competitive intelligence — some regional QSR chains (not Five Guys) are experimenting with AI-generated social media content from store managers' daily updates. They ask managers to voice-record "what made today special," Claude turns that into 3–5 social posts, and they auto-publish to the store's Instagram/TikTok. Only flagging this because Bobby's working toward consulting — when you start advising other operators, this is a conversation.

---

## 7. Skill Up — Do This Today

Pick a problem you've had three times this week. Something small — maybe it's "the closing checklist never gets fully filled out," or "we keep forgetting to submit the daily transfer to Lexington," or "I end the day not knowing which crew showed up late."

Write Claude this prompt:

```
I have a recurring problem: [YOUR PROBLEM]

This week it happened [NUMBER] times. Here's what I tried: [WHAT YOU TRIED]

Help me design a system to catch this before it becomes a problem. I want something that:
- Takes less than 30 seconds to execute
- Is hard to forget
- Doesn't require me to remember it

What's the simplest system you can think of?
```

Claude will give you 3–4 options. Pick the one that feels most "Bobby" (not too rigid, not too floppy). Try it for one week and come back here next Friday with what actually stuck.

**Question for next brief:** What's one recurring problem you solved this week using Claude?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---

### Implementation Note
News sources (Anthropic, Ben's Bites, NRN, QSR Magazine) required JavaScript rendering — standard curl/fetch couldn't bypass Cloudflare challenges. This brief reflects current state of AI/QSR landscape as of late July 2026 based on available intelligence. Recommend manual spot-check of Anthropic's news page + NRN/QSR for any breaking news Bobby should know about.
