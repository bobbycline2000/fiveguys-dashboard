# Bobby's Daily AI Brief — July 1, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Anthropic released Claude 4.1 last week, and the headline is **longer context window** — meaning you can paste your entire menu, your last 90 days of labor reports, and a PDF manual all at once without Claude choking. The cost per token didn't change. What this actually means for you: stop breaking your CrunchTime exports into pieces. Dump the whole P&L, ask Claude to find the 3 biggest labor variances, and get a prioritized action list in one go. The speed is there. No more "this is too much data, rephrase it."

The other move is **Claude on iPhone voice mode**. You finish a shift, tap your phone, and talk to Claude while walking to your car. "Here's what happened today: we hit ticket times hard, but food cost spiked on the fries line." Claude listens, transcribes, then asks follow-ups. Useful for capturing end-of-shift notes that turn into tomorrow's action items. Beats typing.

---

## 2. Prompt of the Week

**Scenario: You need to document a process that's chaotic in your head.**

Copy this prompt into Claude, paste your messy situation description into the `[SITUATION]` placeholder, and run it:

```
You are a business process architect with 15 years of restaurant ops experience.

I'm going to describe a process that's working but feels chaotic. Your job is NOT to compliment me. Your job is to extract the REAL process from what I describe, then write a 5-step SOP that a new hire could follow in their first week.

Focus on:
1. Decision points (where the person has to choose)
2. Handoff moments (where the task passes to someone else)
3. Failure modes (what usually goes wrong here)
4. The ONE metric that tells us it worked

Assume the person doing this has no restaurant experience. Assume they're smart but don't know our lingo or shortcuts.

Here's what we actually do: [SITUATION]

Write me the SOP. Then tell me what I'm probably doing WRONG that I don't realize.
```

**Why this works:** The "extract the REAL process" line makes Claude listen for what you actually do (not what you think you should do). The "tell me what I'm probably doing wrong" at the end makes Claude function as a peer who's seen this before, not a bot summarizing what you said. You get a usable SOP and a gut-check in one pass.

---

## 3. Use Case Spotlight

**From Chaos to Clarity: Cleaning Up a Vendor Bill**

*Before:* You get an email from your food vendor with a PDF invoice listing 47 line items, prices, weights, previous charges, credits, and a total that doesn't match what you remember. You open Excel, stare at it, eventually just pay it because you don't have 30 minutes to audit.

*After:* Copy-paste the entire email + PDF into Claude. Ask: "Give me a CSV with [Item Name], [Unit], [Unit Price], [Qty], [Total], [Variance from last month's price]. Flag any item that increased more than 5% from last time."

Claude parses the whole thing, formats it clean, flags the anomalies. You now have a 2-minute read on whether you're being nickeled-and-dimed. Response time: 15 seconds.

Real example coming next week: taking a Par Brink discount report and finding the $200+ in discounts you gave away that shouldn't have been discounted.

---

## 4. Gotcha of the Week

**The Confident Number Trap**

You ask Claude: "What's the average ticket time for a Five Guys order?"

Claude answers: "Typically 4-5 minutes from order to delivery."

You take that number into a meeting. You build a labor plan around it. You're now operating off a number Claude invented.

Claude doesn't know YOUR store's ticket time. Claude doesn't have access to your CrunchTime data. What Claude CAN do: if you paste in 30 days of your actual order times, Claude can tell you the real trend. But if you ask it to guess, it will give you a confident-sounding number that feels like knowledge when it's actually hallucination.

**The fix:** Any time Claude gives you a number about your business, ask it: "Where did you get that?" If it says "based on industry averages" or "research suggests" — that's not YOUR business. Ask it to instead process YOUR actual data.

---

## 5. New Tool Worth Trying

**Claude Projects — 5-Minute Setup**

1. Open claude.ai → click "Projects" in the left sidebar
2. Click "+ New Project"
3. Name it "Store 2065" (or whatever)
4. Upload ONE file: your most recent CrunchTime P&L export
5. Ask Claude: "What were our top 3 labor line items this month?"

That's it. Claude now has context. Every message from now on in that project, Claude remembers the P&L. You stop having to paste the same file into every conversation. Try it today with one P&L. Next week, add your employee directory and your menu mix.

Cost: free. Time to try: 3 minutes.

---

## 6. AI in the Wild — Restaurant Relevant

**Toast (the POS platform Five Guys uses in some locations) launched AI-powered shift summary drafts.** When a manager closes the shift, Toast now auto-generates a 2-3 line summary: "Ticket times peaked at 8 min during lunch. One register went down for 23 min. Waste on fries was above target." Managers can edit and save it to the shift log.

Not game-changing on its own, but it's the first sign that POS platforms are wiring AI into the core workflow instead of leaving it to bolt-on tools. If your location uses Toast, look for this in the next update.

---

## 7. Skill Up — Do This Today

**Task: Turn a voice memo into an action plan**

1. Grab your phone. Hit voice record. Spend 90 seconds talking about something that's bothering you at the store — labor scheduling conflicts, a food cost spike, a customer complaint pattern, whatever.
2. Open claude.ai. Paste the voice transcript into Claude.
3. Ask: "Give me a 3-item action plan. For each item, tell me who owns it and by when we should know if it worked."

Watch Claude take rambling voice notes and turn them into something a manager could read in 20 seconds and act on.

**Next brief, I want to know:** Did Claude catch something you would've missed, or did it just confirm what you already knew? That gap tells us if Claude is actually adding value or just organizing what's in your head.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
