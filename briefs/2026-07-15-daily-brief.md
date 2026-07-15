# Bobby's Daily AI Brief — July 15, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Two things shipped that matter: **Claude Sonnet 5** (last week) hit the market and is now your default. It's faster and sharper on the work you do — spreadsheets, reasoning, coding tasks. Use it when the stakes are high.

The second: **Claude Science** launched this week. It's a workbench with customizable tools and auditable artifacts. For you, this means you can now take a messy restaurant spreadsheet, run it through Claude, and get back not just the answer but a logged chain of what Claude actually did — the math, the decisions, the step-by-step. Health inspectors and auditors will like that trail. Five Guys corporate might like it too.

Nothing else this week was built for you. Claude for Teachers targets schools. Reflect with Claude is navel-gazing. The signal: Anthropic is shipping deeper, cleaner versions of what works, not adding hype features.

---

## 2. Prompt of the Week

**Use case:** You've got a staffing problem. Someone's struggling, underperforming, or needs a performance conversation. You don't know how to frame it fairly. Here's the exact prompt:

```
You are a restaurant operations coach. I'm managing a Five Guys team member who is [briefly describe the issue — e.g., "arriving 5 min late consistently", "order accuracy is 82%", "conflicts with the drive-thru team"].

I need to have a conversation with them about this. Your job: write me the EXACT WORDS I should use in a 1-on-1 meeting that:
1. Names the specific behavior clearly (no sugarcoating, no exaggeration)
2. Explains why it matters to the team and to them
3. Asks ONE question that makes them think about the impact (not accusatory)
4. Ends with clear expectation going forward

Keep it to 3-4 sentences. Sound like me — direct, fair, interested in them as a person.

The tone matters: I want them to hear "I see this and I want to help you fix it" not "I'm waiting to fire you."
```

**Why this works:** Claude is a master at tone. Most managers either go too soft (the problem never lands) or too hard (the person shuts down). By asking Claude to mirror your voice and frame the conversation around *impact* (not blame), you get something that actually moves behavior. The single question at the end—that's what makes a difference. People change when they see for themselves why it matters, not when you tell them.

---

## 3. Use Case Spotlight

**Before:** You pull the Par Brink PDF at the end of your shift. It's a mess—hourly sales, labor %, discounts, all mixed formats. You copy numbers into your mental model to see if the day tracked. Takes 10 minutes. You still miss patterns sometimes.

**After:** Upload that PDF to Claude. Prompt: `"Break down today's hourly sales, labor %, and discount rate by hour. Highlight any hour where labor % exceeded 32% or sales dropped >15% from the prior hour. Flag trends I should brief the DM on."` 

Claude extracts the numbers, finds the anomalies, hands you the 3 things that actually matter. Takes 30 seconds.

**The multiplier:** Do this every shift. After two weeks, you start seeing YOUR patterns—when labor creeps, why certain hours tank, what your team actually does in the slow stretch. By month two, you're making staffing calls before the problem shows up, not after. That's not work—that's intelligence.

---

## 4. Gotcha of the Week

**The Trap:** You ask Claude for next week's schedule. It generates one. It looks reasonable. You use it. By Wednesday, two people are upset because Claude didn't know Kayla has Sundays off or that Francisco does doubles on Thursdays. The schedule wasn't wrong—it was built blind.

**The Fix:** When you ask Claude to generate something operational (schedule, inventory order, PTO calendar), start with the constraints:

"Before you schedule, here's what you need to know:
- Kayla: No Sundays, max 40 hrs/week
- Francisco: Prefers doubles (back-to-back shifts), available Mon-Thu
- [Add every actual constraint]

Now build the schedule."

Claude is a blank slate. Constraints are what makes the difference between "looks good" and "actually works."

---

## 5. New Tool Worth Trying

**Claude on your phone** — five minutes to set up, then text Claude a photo of inventory mess, a receipt you need to parse, or a question at 11 PM.

Steps: Open claude.ai in mobile browser → tap your profile (top right) → "Get Claude mobile app" → install app (iOS or Android) → log in. Done.

**Why this matters:** You're walking the back, see an issue, snap a photo, text Claude right then. Gets you answers without a laptop. Screenshot your Par Brink, ask "what hours underperformed," get the answer in your pocket.

---

## 6. AI in the Wild — Restaurant Relevant

**The Toast AI Chatbot Trend:** Independent restaurants are adopting Toast's AI chatbot for operations—shift coordination, inventory questions, SOP lookups. The pattern: restaurants stop asking managers the same question 15 times and let the AI answer it.

**What it means for you:** The industry is moving toward "ask the AI first, escalate to humans if needed." That's not sci-fi—it's what smart operators are doing today. By the end of 2026, the restaurants still making every decision human-to-human will be the slow ones.

**Also moving:** Chains are doubling down on nostalgia pricing (KFC's Popcorn Chicken comeback, Pizza Hut's throwback menu). That's not AI, but it's signal—consumers want value + familiarity. Your promotions strategy should track this.

---

## 7. Skill Up — Do This Today

**The Exercise:** Pull your three slowest shifts from this week (lowest sales). For each one, upload the Par Brink PDF to Claude with this prompt:

`"This was one of my slowest shifts. Break down: (1) What time did sales drop most? (2) Was it because of labor %, pricing, or something else? (3) What ONE thing would I change for next week to improve it?"`

Run it three times. You're going to see patterns. Maybe you're overstaffed on Tuesday lunch. Maybe you're underpriced on Thursday dinner. Maybe the drive-thru gets swamped at 6 PM and no one's there.

**One question for next time:** After you run this three times, what pattern surprised you most?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
