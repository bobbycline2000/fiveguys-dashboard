# Bobby's Daily AI Brief — 2026-08-20
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude 5 is now the baseline. If you're still using Sonnet, it's not wrong—it's like having a solid sous chef who knows your station. But Opus 5 shipped with better reasoning and faster output, which means your automation is getting more reliable. The practical win for you: Claude can now handle a messy Five Guys day-end report (bad formatting, missing columns, handwritten notes scanned in) and spit back clean, usable data without you having to massage it first.

Nothing earth-shattering this week. No new features that will change how you run your restaurant. The AI space is consolidating, not innovating hard—which is actually good. It means the tool is stable and you should keep building on it, not waiting for the next big thing.

---

## 2. Prompt of the Week

**Copy this exact prompt into Claude and save it as a template:**

```
You are the GM of a Five Guys restaurant. You are reviewing a manager's written incident report from today. Your job is to:
1. Identify what actually happened (separate facts from opinions)
2. Flag if the manager missed a step they should have taken
3. Suggest the exact words the GM should use when talking to the employee tomorrow
4. Rate the severity (coaching conversation vs. formal write-up vs. immediate removal from schedule)

Incident report:
[PASTE THE REPORT HERE]

Respond in this exact format:
**WHAT HAPPENED:** [One sentence of fact]
**WHAT THEY MISSED:** [If anything; if nothing, say "nothing obvious"]
**YOUR WORDS:** [Exact script for the GM to use]
**SEVERITY:** [One of: coaching / write-up / remove]
**WHY:** [One sentence explaining the severity call]
```

**Why this works:** Most managers write incident reports in a blur of emotion and blame. The prompt pulls them back to fact, teaches the GM how to frame a coaching conversation (instead of just being mad), and gives you a severity gate so you're not overreacting or under-responding. The "exact script" piece is the move—it takes the emotional charge out and gives the employee something they can actually hear.

---

## 3. Use Case Spotlight

**Before:** You get an email from Par Brink with a CSV of yesterday's hourly sales. It's 3 columns, zero labels, and the time format is "0800" instead of "8:00 AM". You copy it into Excel, manually fix every row, then look at it.

**After:** You paste the raw CSV into Claude with: *"Clean this up and tell me: What hour had the lowest sales? What percentage drop from our average?"*

Claude returns:
```
LOWEST HOUR: 2–3 PM (18% below daily average)
REASON: Typical lunch-to-dinner lull
ACTION: You were 2 staffed during this window—consider light prep-work assignments
```

Takes 20 seconds. No Excel. You get the insight without the grunt work.

---

## 4. Gotcha of the Week

**The Trap:** You ask Claude "What's a good price for our new item?" and Claude gives you a confident answer—$8.95—backed by reasoning about margins and competitor pricing. You feel smart. You're not.

**Why it fails:** Claude doesn't know your food cost for that item. It doesn't know your Five Guys market position in Louisville. It doesn't know if you're running a weekend special. It is **hallucinating confidence**. The number sounds right, so it sounds real.

**The fix:** Lead with YOUR number first. "We pay $2.40 for this item. Competitors are at $8.50–$10. What price point makes sense?" Now Claude has constraints and can actually reason. Its answer is useful instead of just plausible.

---

## 5. New Tool Worth Trying

**Claude Projects on iPhone.** If you have Claude on your phone (it's in the App Store), you can now create a Project right there—upload your weekly schedule as a PDF, your food cost targets as a screenshot, your labor standards as a text file. Then ask voice questions: *"How are we trending on labor this week?"* It reads your uploaded docs and answers.

Takes 2 minutes to set up. Try it Tuesday morning with your actual schedule.

---

## 6. AI in the Wild — Restaurant Relevant

Toast's new labor forecasting module went live this week. (Toast is the POS many QSR chains use.) They're using AI to predict hourly traffic based on historical data + local events + weather. Early reports: 3–5% labor savings when managers actually use the forecast instead of intuition. You're not on Toast—you're CrunchTime + manual scheduling—but this signals where the industry is moving. By next year, any modern POS will have this built in. The advantage stays with operators who build a tight link between forecast and actual (i.e., you tracking what you predicted vs. what happened).

---

## 7. Skill Up — Do This Today

**The exercise:**

1. Take a photo of your current labor schedule for this week (clipboard, email, wherever you have it)
2. Paste it into Claude
3. Ask: *"If we hit our sales forecast, should we adjust this schedule? Where are we over/under?"*
4. Read what Claude says
5. Ask yourself: *"Is that a real signal or garbage?"*

**What to notice:** Claude will probably spot something you didn't—a day where you're heavy-staffed but forecast is low, or vice versa. Your job is to decide if Claude caught a real inefficiency or if there's context Claude is missing (e.g., it's payday, you need coverage for a training, you're light on experienced staff that day). This teaches you when to trust Claude and when to override it.

**Next time we talk:** Tell me one thing Claude flagged that you knew about already vs. one thing that surprised you.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
