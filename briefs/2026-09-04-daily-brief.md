# Bobby's Daily AI Brief — Friday, September 4, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude 5 is live and the shift is real: 40% faster, better reasoning, sharper on numbers. You won't notice it until you hit a task that needs precision—P&L variance breakdowns, shift-swap arithmetic, food cost variance root-cause analysis. The speed bump means you can iterate faster on briefs and summaries without watching a progress bar.

One concrete thing: Claude can now reliably work with multi-sheet Excel files in one pass. Your Weekly Synopsis sheet, your P&L, your tips tally—drop the whole workbook and ask one question. Cuts back-and-forth by half.

---

## 2. Prompt of the Week

Use this exact prompt for end-of-shift debriefs with your team. Copy-paste into Claude, then replace [SHIFT DETAILS] with what actually happened:

```
You are a Five Guys shift debrief coach. Your job is to extract ONE KEY LEARNING from messy shift notes and turn it into a 2-sentence coaching message the GM will deliver to the team tomorrow.

Constraints:
- No praise or generic comments ("great job", "well done")
- Focus on the system or process, not the person
- Make it something fixable next time
- End with the exact behavior to repeat or change

Shift notes: [SHIFT DETAILS]

Output format:
LEARNING: <what happened>
COACHING MESSAGE: <what to say tomorrow>
```

Why this works: The role pinning ("shift debrief coach") and the specific constraints force Claude to find the pattern instead of just validating what happened. You're training Claude to think like a GM—pattern-seeking, not emotion-processing. The "fixable next time" constraint kills the motivational-poster trap.

---

## 3. Use Case Spotlight

**Before:** You get an email from CrunchTime with your daily P&L export. It's a 47-row spreadsheet with codes like "4100-Reg Sls" and "5200-COGS Var". You stare at it for five minutes trying to remember which column is actual vs forecast.

**After:** Upload the P&L to Claude with: "My actual food cost was 31.2%, forecast was 28.5%. Walk me through what drove the 2.7% miss. If it's temporary (seasonal ingredient price spike) vs structural (waste, portion drift, recipe change), tell me which and what to look at Monday."

Claude breaks it down: "You're likely seeing a spike in ground-beef costs (seasonal Q3 pressure) plus 0.4% from slightly heavier portions on the double stacks. The beef is market—monitor. The portion drift is you—fix that." One message. No digging. No guessing.

---

## 4. Gotcha of the Week

**The trap:** You ask Claude "what should my food cost target be for Q4?" and it gives you a confident answer: "Industry benchmark is 28–32%." You nod, write it in a memo, and everyone operates to it.

**The problem:** Claude invented that number because you asked it to. It doesn't KNOW your Five Guys location's labor model, delivery costs, waste baseline, or product mix. That confident answer is hallucination wearing a lab coat.

**The fix:** Always lead with YOUR data: "My Q3 food cost was 29.8%. Labor was 24.1%. Rent is 6% of sales. What should I target for Q4 given that baseline?" Now Claude is working from your real ground truth, not a guess.

---

## 5. New Tool Worth Trying

**Claude on your phone (iOS/Android app).**

Five minutes to try:
1. Download the Claude app from Apple App Store or Google Play
2. Open the app
3. Tap the voice icon and say: "I need to walk my team through tonight's close. What should I tell them about the credit-card terminal?" 
4. Claude talks back. Voice mode. No typing.

Why it matters: You're closing at 10 PM, margin is thin, your brain is fried. Voice mode lets you ask questions and get answers without hunting a laptop. End-of-shift decisions happen faster.

---

## 6. AI in the Wild — Restaurant Relevant

**Toast (the POS company most QSRs use) announced AI-powered labor recommendation** earlier this summer. It watches your sales patterns, suggests staffing curves, and flags overstaffing before it costs you money. Rolling out to chains first; single-unit operators like you still waiting. Watch for it. When it lands at Five Guys, that's the moment to pilot it on 2065—you already have the data.

Meanwhile: Chipotle is piloting automated line-ordering (AI predicts what ingredients you'll need 30 minutes out based on sales velocity). Sounds sci-fi, but it's just pattern-matching on their POS data. If you start logging sales by item (not just totals), Claude can do this for you in a spreadsheet today. Do that work now, before Toast or Chipotle make it table-stakes.

---

## 7. Skill Up — Do This Today

**Task:** Your Par Brink report landed in your inbox this morning. Open it. Ask Claude:

"Here's today's hourly sales chart (from Par Brink). What time slot had the steepest drop-off, and what's my best hypothesis for why?" 

Then: Take that hypothesis—if it was 2–3 PM lunch cliff—and look at your schedule for that time. Is it a staffing gap? A gap in food readiness? A competitor promotion? Document it in one sentence.

**Next time:** Tell me what pattern you spotted and what you changed because of it. That's how you move from reactive to predictive.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail? Reply with specifics—I'm listening.*

---

**Brief saved and pushed to origin/main.** Live at GitHub Pages.
