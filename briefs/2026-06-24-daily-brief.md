# Bobby's Daily AI Brief — June 24, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Two things shipped that matter to you:

**Claude Tag** (launched yesterday) is Claude for group work. If you're building something that Crystal, your managers, or an external consultant need to see and edit in real-time, Tag is where you do it. Same Claude quality, collaborative edit surface. Useful later when you're scaling the consulting business — clients can see what you're building live instead of waiting for email hand-offs.

**Opus 4.8** is the engine update. Faster, more reliable on long reasoning chains (like the tip-entry pipeline or the P&L cascade you're building). You don't do anything — your next Claude conversation just runs a touch sharper. The update is already live.

One note: the government just blocked export of Fable 5 and Mythos 5 to some regions. Doesn't affect you — Opus 4.8 is the production model you should be using anyway.

---

## 2. Prompt of the Week

**End-of-Shift Manager Recap — Dictation to Action List**

Copy this prompt exactly. Paste it into Claude when you're finishing a shift and want to dump notes without writing them up yourself:

```
You are a Five Guys Store Manager turning a voice memo into a formatted shift recap and action list.

Input: Raw voice memo/notes from the manager about the shift — what went well, what broke, what needs follow-up.

Output: Two sections:
1. **Shift Summary** (3-5 bullets): what happened, was it normal or unusual, any patterns
2. **Action Items** (numbered list, due dates): what needs to happen before the next shift, who owns each, what's urgent vs. can wait

Rules:
- Keep it terse. No corporate speak.
- If something happened twice today, call it a pattern.
- If someone's name comes up in a problem context, include it — context matters.
- Separate "fix tonight" from "report to Bobby/Crystal tomorrow."
- If the manager mentioned a number (food cost, labor %, time a task took), include it in the summary.

Here's the voice memo:
[PASTE YOUR NOTES HERE]

Format the output as a markdown file I can paste into my team notes.
```

**Why this works:** The prompt creates a role (manager → AI), a clear input/output shape, and rules that prevent Claude from softening problems or making things polite instead of accurate. The "patterns and names" rules keep context that usually gets lost in summarization. You can paste this directly into a Slack message or your team notes, which is the bar for "actually useful."

---

## 3. Use Case Spotlight

**Turning a CrunchTime export disaster into a clean P&L**

Most weeks you export CrunchTime's P&L data and it arrives as a table with merged cells, blank rows, headers in weird places, and numbers formatted three different ways. An hour of manual cleanup to make it usable.

**Better approach:** Paste the raw export into Claude with this prompt:

```
Clean this CrunchTime P&L export so it's usable in Excel. Return ONLY a CSV with these columns:
- Category (Sales, COGS %, Labor %, etc.)
- This Week
- Last Week
- Variance
- % of Sales (if applicable)

No commentary. Just the clean data.

[PASTE THE MESS HERE]
```

Claude outputs a CSV you can paste directly into a spreadsheet. Takes 30 seconds instead of an hour. Try it on your next export — note how many times you would have normally had to manually fix the data.

---

## 4. Gotcha of the Week

**Claude invents numbers that sound right.**

Last week you asked Claude to estimate your labor savings from a scheduling change. It said "approximately $2,400 per month based on typical QSR averages." You almost quoted that to Crystal. It was wrong. Claude had never seen your actual payroll, labor mix, or store specifics — it was pattern-matching to "typical" and presenting it as your number.

**The trap:** When Claude starts with "Based on industry standards" or "Typical operators see," it's not wrong — it's generic. It works for teaching, never for your actual business decisions.

**The fix:** When you want a number that matters, always say: "I'll give you my actual data. Use only that. Don't use industry averages." Then paste your real CrunchTime or payroll data. Make Claude math off YOUR numbers, not guesses about restaurants like yours.

---

## 5. New Tool Worth Trying

**Claude on your phone — voice input for end-of-shift notes**

If you have an iPhone or Android: download Claude, open the app, hit the mic icon, and start talking. "Ran out of beef at 8 PM, had to call the supplier, add to breakfast meeting notes, labor was over by 2 hours because of lunch rush."

Claude transcribes it live. You can edit before sending or just let it go. Hit the mic icon again. It works.

Why: you're finishing a shift tired. Typing is friction. Voice is not. Spend 60 seconds talking instead of 10 minutes writing, and Claude handles the transcription. Try it on one closing shift and see if it sticks.

Time to try: 2 minutes (download) + first use (60 seconds).

---

## 6. AI in the Wild — Restaurant Relevant

**Chipotle's World Cup play hit the mark** — their BOGO promo tied to World Cup matches drove nearly 60% more traffic on game days. Same meal. Different reason to come in. Event marketing works better than you'd expect.

But the deeper story: **kitchen automation is moving fast**. Miso (owner of Flippy, the robotic fryer) just acquired Zume's pizza technology. That's the second-generation automation play — not just "robot does one thing," but "acquire the proven tech, integrate it across the chain." Five Guys has not moved on automation yet. When it does (and it will), you'll see it via corporate directives, not the news. But watch it in the industry. Your competitors are moving.

---

## 7. Skill Up — Do This Today

**Practice: Ask Claude for a labor schedule variance analysis.**

Do this right now:

1. Export your Par Brink labor report for last week (Actual Hours).
2. Export your Teamworx scheduled hours for the same week.
3. Paste both into Claude with this prompt:

```
Compare scheduled vs. actual labor hours. For each day, show:
- Scheduled hours
- Actual hours
- Variance (over/under)
- Which shift (open/mid/close) had the biggest miss

Then tell me: what one pattern jumps out? Not "we went over," but "what time of day or what situation causes the miss?"

[PASTE YOUR DATA]
```

4. Look at Claude's answer. Did it spot something you already knew or something you missed?

**Your question for next time:** Did Claude's pattern match what you expected, or did it spot something you should investigate further?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
