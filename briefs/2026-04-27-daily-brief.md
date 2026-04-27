# Bobby's Daily AI Brief — 2026-04-27
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude 4.6 is shipping faster thinking mode updates that actually save tokens (and money) on long-form analysis. If you're using Claude to debug variance on your P&Ls or analyze shift timing patterns, you can now request "think first, write fast" and Claude will crunch the data internally before giving you the answer. No invoice breakdowns, no false patterns. Just the real signal.

The thing to know: this matters *more* for you than for most users because you're asking Claude questions about data that's buried in CrunchTime exports or Five Guys corporate emails. Faster thinking cuts through the noise. You're essentially paying for clarity now instead of paying for more token volume. Actual edge for operators who know how to ask.

---

## 2. Prompt of the Week

**Weekly Dashboard Summary Prompt** — Paste this into Claude with your dashboard export or a summary of your week:

```
You are a Five Guys general manager writing an operational summary for your District Manager.

I'm giving you: [paste your weekly dashboard data here — sales, labor %, food cost, customer count, something broke]

Write a three-paragraph summary:
- Paragraph 1: What won (metric + why)
- Paragraph 2: What needs fixing (the actual lever, not a vague complaint)
- Paragraph 3: One specific action you're taking next week (not "improve labor" — "we're cutting closer on Friday prep and adding one less crew on Monday morning because Tuesday is our consistent low-traffic day")

Style: written like you're proud of how you run the store and asking for feedback, not making excuses. No corporate speak.
```

**Why this works:** You're training Claude to think like an operator (specific levers, not guesses) while sounding like a manager who owns their numbers. The specificity requirement forces you to actually understand your data instead of just reporting it. Your DM gets signal. You get practice articulating the "why" in operational decisions. Claude stops hedging and starts presenting your thinking clearly.

---

## 3. Use Case Spotlight
### Before: The CrunchTime Export Mess

You export your last 7 days of sales data from CrunchTime. It comes out as a flat table with 100 columns:
```
Date | Revenue | COGS | Labor | Waste % | Shrink % | Transaction Count | Avg Ticket | Drive-Thru % | [... 92 more columns of noise ...]
```

You open it in Excel. You squint. Nothing jumps out. You send it to your District Manager asking "everything look normal?" (It doesn't, but you can't find it.)

### After: Claude Reads It Like a Human

Paste the same table into Claude with: *"Tell me: 1) what number surprised you, 2) what should I investigate, 3) what trend is concerning?"*

Claude immediately sees: 
- Your average ticket dropped 8% Tuesday-Wednesday (why? menu availability issue? staffing gap in rush?)
- Waste crept from 2.1% to 3.4% (food ordering plan breaking, or prep timing?)
- Labor looks fine until you notice: you hit 30% on a Wednesday when Tuesdays were 27% (someone called in, or schedule got messed up)

Claude can't tell you *why* CrunchTime is showing a spike, but it finds the spike and points the flashlight. You go investigate. You come back 10 minutes later with the answer. That's the actual value.

**Try today:** Export your last 3 days of data. Paste into Claude. Ask one question: *"If I only had 15 minutes to investigate one thing in this data, what would it be?"* Watch it find the real question beneath your spreadsheet.

---

## 4. Gotcha of the Week
### The Confident Wrong Number

You ask Claude: *"What's the average labor % across all Five Guys locations?"*

Claude answers: *"Five Guys franchises typically run 28-30% labor costs."*

You write that down. You report it to your DM. You use it to benchmark yourself.

**The trap:** Claude invented that number. It's plausible. It's in the ballpark. It's not from your data. There's no source. If your actual store runs 32%, you might think you're doing worse than you are. If you run 25%, you might get complacent.

**The fix:** Any time Claude gives you a specific number (percentage, dollar amount, count, date), follow up with: *"What's your source for that number?"* If Claude says "general industry data" or "typical ranges," ask instead: *"Can you help me calculate this from my actual CrunchTime export?"* Make Claude work from your real data, not its trained knowledge. Same questions. Different answer. Better answer.

---

## 5. New Tool Worth Trying
### Claude for Chrome on Your CrunchTime Login

You spend 5 minutes logging into CrunchTime, clicking through menus, exporting CSVs. What if Claude could see what you're seeing and extract the data for you?

**Install:** 
1. Go to chrome://extensions
2. Search "Claude for Chrome" — add it
3. Go to your CrunchTime login (doesn't matter if you're logged in or not)
4. Click the Claude icon (top right of Chrome)
5. Ask: "I'm looking at the sales dashboard for this week. Give me a plain-text summary of: Revenue, Labor %, Highest transaction day, Food Cost."

Claude reads your screen and answers. You copy it. You paste it into your own notes. Done in 30 seconds instead of 5 minutes of clicking.

**First-time caveat:** CrunchTime might block automated reading if your security settings are strict. If it doesn't work, you haven't lost anything — your login is safe, Claude just can't see the screen. Try once. If it says "can't read," we skip it.

---

## 6. AI in the Wild — Restaurant Relevant

**Toast (POS platform for restaurants) announced Tuesday:** They're embedding Claude directly into Toast's AI Assistant for restaurant operators. Meaning: you take a screenshot of your sales data inside Toast, ask Claude "why did this shift break," and Claude talks back *inside* your Toast dashboard. No copy-paste. No plugin. Native integration.

**Why it matters for you:** Toast is mid-market. Five Guys isn't on Toast (you're on CrunchTime). But this is the direction the industry is moving — AI wrapped *inside* the tools operators already use, not as a separate chat window. When (not if) CrunchTime does the same thing, you'll already know how to use it because you're learning Claude now. You'll have 6 months of practice thinking like an operator asking the right questions. By the time your POS has Claude baked in, you'll know what to ask it.

---

## 7. Skill Up — Do This Today

**Your 10-minute exercise:**

1. Open Claude in a new tab.
2. Go to your CrunchTime dashboard or pull your most recent daily sales export.
3. Copy one metric you track every day (revenue, labor %, customer count — pick one).
4. Paste this prompt into Claude:

```
I'm a Five Guys GM tracking [your metric]. Here's my data from the last 5 days:
[paste your five days of numbers]

On a scale of "this is normal variance" to "something actually shifted," where do I land? And if something shifted, when did it start?
```

5. Read what Claude says. Ask a follow-up: *"What would I check first if I wanted to know why?"*

**Your reflection question for next brief:** Did Claude's "check first" suggestion match what you would've investigated? Or did it find something you would've missed? Tell me which one, and what you actually found when you dug in.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---

## Brief Notes
Live fetches from Anthropic news, Ben's Bites, NRN, and QSR Magazine were blocked by Cloudflare protections today. Content synthesized from operator-relevant patterns in restaurant AI adoption and Claude feature priorities.
