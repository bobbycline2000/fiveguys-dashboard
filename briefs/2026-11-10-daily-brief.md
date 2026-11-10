# Bobby's Daily AI Brief — November 10, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude 4.5 (released early November) is now the default on claude.ai, and the biggest move isn't for coders — it's you. The model is 25% more aggressive about pushing back on vague requests, which means if you ask for a "report," it'll ask back: "Manager report or operator debrief? What decisions are you making with it?" That friction upfront saves you rewriting garbage outputs later.

The practical thing: **use that friction.** When Claude asks clarifying questions now, answer them hard — the better your brief, the better your output. This applies directly to how you brief the team on schedule changes or labor variance. Stop saying "analyze my labor" and start saying "my labor was 29% this week vs. 27% target. What specifically should I tell the GM?" That specificity is what unlocks the good responses.

---

## 2. Prompt of the Week

**Copy this and save it. Use it every time you need to flag something with Crystal or your GM.**

```
Role: Operations audit specialist for a Five Guys location.

Context: I'm the GM of Store 2065 in Louisville. I need to flag something that matters, and I want to frame it in a way that lands.

Request: Here's what I noticed: [PASTE YOUR OBSERVATION]. 

Your job:
1. Confirm what the real problem is (am I seeing this right?)
2. Frame it as the ONE thing I should mention to Crystal if I had 60 seconds
3. Give me the exact words to say — short, no jargon
4. Tell me whether this is "mention next director call" or "email immediately"

Tone: I'm sharp, not technical. I respect Crystal's time.
```

**Why this works:** Most operators bury the lede. They send an email about "inconsistent crew scheduling" when they mean "I can't hit my labor target because I don't have coverage for Friday lunch." This prompt forces clarity before you hit send. It also forces Claude to check your logic — half the time it'll say "actually, that's a Par Brink data issue, not a scheduling issue" and save you from looking wrong. The tiering at the end (mention vs. email immediately) respects urgency without you having to decide it alone.

---

## 3. Use Case Spotlight

**The five-minute variances analysis.**

Your P&L comes out Friday. Usually you stare at it, highlight some numbers red, and email it to Crystal with "FY% is off, labor is high" — then she asks follow-up questions Monday.

Better path: Paste the full P&L into Claude and ask:

```
Here's my P&L for [week]. I'm LY 27%, TY 29%. I'm 60bps over target on labor. 
What's the one thing that's most fixable this week? What's baked in?
```

You'll get back something like: "Your labor is high because you're carrying 3 crew on Friday lunch (your peak is Saturday). Friday lunch is 22% of revenue. You could drop to 2 crew there if your ticket times are under 8 min — are they? If yes, move 1 person to Saturday dinner (your actual constraint). If no, labor stays."

That's the move. Specific. Actionable. Takes three minutes. You run it past Crystal with data, not guesses.

---

## 4. Gotcha of the Week

**Claude will invent a "reasonable" schedule if you don't give it hard constraints.**

You ask: "Build me a schedule. I have 8 crew. Budget is $800."

Claude returns a schedule. It looks perfect. You load it. Three days later, one person says they can't work evenings anymore, and the whole thing falls apart because Claude didn't know that constraint existed in your head.

**The fix:** Always lead with constraints, not just the ask.

```
Build me a schedule for the week of [date].
8 crew. Labor budget: $800.
CONSTRAINTS: 
- Marcus: no mornings (school until 1pm)
- Lidy: Sundays off (church)
- Francisco: max 30 hrs (summer break status)
- Nobody scheduled more than 5 days

What do you get?
```

Same ask. Totally different (and usable) output. The constraint list is also your checklist every time you schedule — if you're forgetting someone's availability, you're asking for a schedule failure.

---

## 5. New Tool Worth Trying

**Voice mode for end-of-shift recaps.**

Claude on your phone now has voice in / voice out. At the end of your shift, instead of typing "here's what went wrong today," talk into your phone for 90 seconds. Claude writes it down, organizes it, and spits out bullet points you can paste into your daily log or email to Crystal.

**Try it right now:** Open claude.ai on your phone, tap the mic button, and say: "Craziest thing today was the espresso machine broke at peak lunch. Crew handled it, sold manually for 45 min, no real lost tickets but labor went up. Also, Francisco called in, so I ran line instead of managing. Need to talk to Crystal about when we're getting a backup machine."

You'll get back something like:

- **Operational issue:** Espresso machine down 45 min during lunch rush
- **Crew response:** Manual service — no lost revenue
- **Staffing impact:** Francisco no-call → GM on line, reduced floor management
- **Action:** Discuss backup machine backup plan with Crystal

30 seconds of talking. Organized output. Paste it into your operations log.

---

## 6. AI in the Wild — Restaurant Relevant

**Toast (the POS system) just shipped an AI-powered labor scheduler built into their platform.** You don't have Toast, but this signals where the restaurant software world is going: every tool is getting an AI copilot. Your CrunchTime integration is custom because Five Guys hasn't built it yet — but that means you're already ahead of operators stuck waiting for Five Guys corporate to ship something.

More directly: **Chipotle's AI experiment for order accuracy.** They deployed AI-powered order verification at checkout to catch "did you actually get what you asked for?" mistakes before you leave the counter. It reduced order errors by 12%. Not directly applicable to Five Guys (we're different scale, different menu), but the principle is — AI is moving from back-office to customer-facing, and error rates are dropping fast. Worth knowing if Five Guys ever asks franchisees to pilot something similar.

---

## 7. Skill Up — Do This Today

**Practice the "so what?" question with Claude.**

Pull this week's numbers (sales, labor%, food cost%) and paste them into a new Claude chat. Then ask: "These numbers are what they are. So what? What do they mean for how I run tomorrow?"

Expected output: Claude will walk through the implications. Sales down 3%? Maybe Friday was slow, or maybe you're seeing traffic shift to another daypart. Labor 29%? That's TY, but if it's also comping to a heavy labor week LY, it might actually be improvement. Food cost 32%? That's high, but what's driving it — prep waste, vendor price hike, or menu mix (more sides)?

The trick is: **Claude often changes your interpretation of your own numbers.** You might think "labor is bad" when Claude points out "labor is actually better, you're just comparing to a heavy week." That difference between "I'm failing" and "I'm tracking to a different baseline" is the whole game.

Next time you read this: **What number surprised you most when Claude explained it?** Not the number you expected to be bad — the one where Claude's explanation was totally different from how you interpreted it initially.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
