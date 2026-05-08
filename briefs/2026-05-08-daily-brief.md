# Bobby's Daily AI Brief — May 8, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

**Extended thinking just landed for every Claude model**, and it changes how you approach hard problems. 

Think of it as Claude working through a decision the way you do — asking itself questions, checking its logic, catching its own mistakes before answering you. It costs more tokens and takes longer, but for complex P&L variance analysis, staffing decisions with real trade-offs, or parsing a vendor contract with hidden liability — it's worth the extra 10 seconds.

**What you can do today:** Paste a complex CrunchTime variance report into Claude and ask "walk me through why the numbers don't match." Extended thinking will spend time reasoning instead of pattern-matching, and you'll get a real analysis instead of a confident guess. Useful for the monthly close-out with your accountant.

---

## 2. Prompt of the Week: The Operations Audit Frame

Whenever you want Claude to dig into an operational mess — a chaotic Excel file, confusing staffing data, a vendor invoice that doesn't track — use this frame:

```
You are an operations auditor for a Five Guys franchise. Your job is to 
find facts and expose mismatches. You do not make excuses. You do not 
assume things are correct just because they came from official systems.

Context: [PASTE YOUR DATA HERE]

Tasks:
1. Extract every numeric claim (counts, hours, costs, dates, names).
2. List which claims contradict each other.
3. Identify which claims are missing data to verify them.
4. Flag the single biggest risk or error if I don't fix it.

Format your answer as a bulleted audit. Be specific with numbers and 
sources. If you're uncertain, say it.
```

**Why this works:** The "auditor" role tells Claude to act like someone who gets paid to find problems, not to make you feel good. It strips away the hedging and the "I think this might" language. You'll get "Claim X contradicts Claim Y" instead of "These numbers seem unusual." That's signal.

---

## 3. Use Case Spotlight: Parsing a CrunchTime Export Horror

**The problem you face every week:**
You pull a CrunchTime labor report for the month. It's an Excel export with dates in three formats, employee names sometimes missing middle initials, hours in one sheet and wages in another, and a total that doesn't match the sum of the rows. You spend 20 minutes cross-referencing and still aren't sure if you caught everything.

**What Claude does:**
- Paste the two sheets (side by side, copy-paste, or as an image).
- Ask: "Show me every row where the hours don't reconcile to the total, and every employee whose name appears inconsistently."
- Claude reads the actual data, flags the specific mismatches, and gives you a line-by-line fix list in 30 seconds.

**Result:** 20 minutes of manual checking → 2 minutes of Claude + 5 minutes of human verification. And you catch errors you would've missed.

**Bonus:** Upload the CrunchTime export as a Projects file so you can ask it follow-up questions against the same data without re-pasting. "Show me this employee's trend across the three months" becomes a single question.

---

## 4. Gotcha of the Week: The Confident Wrong Answer

Claude will tell you with absolute conviction that "Five Guys serves soft drinks in 14oz cups" when you actually serve 16oz, or that "Labor% on a $5K day should be 28%" when your target is 26%. It does this because:

1. It was trained on the entire internet, which has conflicting data.
2. It doesn't know YOUR store's specific numbers.
3. It will *never* admit "I don't know" if a question is phrased like you want a fact.

**The fix:** 
- Use the audit frame above — ask Claude to extract claims and then YOU verify them.
- When you paste a number, tell Claude what the correct number is first: "Five Guys serves 16oz soft drinks. Given this..." Then it operates from that baseline.
- For store-specific claims (labor%, food costs, profit margins), lead with YOUR numbers: "Our target labor% is 26%. Given our sales yesterday were $5K and hours were 130, did we hit it?"

This is the #1 way Claude surprises operators. It's not stupid — it's just not your store unless you teach it.

---

## 5. New Tool Worth Trying: Claude for Chrome on Vendor Websites

**5-minute setup:**
- Open Chrome, go to your par.replenishment.com (or whatever ordering site) to check inventory.
- Click the Claude icon → Ask: "Show me everything that's below par and ready to order."
- Claude reads the live page and gives you a shopping list in 10 seconds.

**Why it matters:** You no longer need to open the vendor site separately. Claude is your reading agent on every system. Works on Egnyte, Outlook, your sales dashboard, anything in a browser.

If you haven't installed the Chrome extension yet, [go here](https://chrome.google.com/webstore) search "Claude for Chrome" — free, one-click install. Then you're live.

---

## 6. AI in the Wild — Restaurant Relevant

**Toast (POS platform) just launched AI-powered labor scheduling** built on top of their historical sales + labor data. The idea: feed it your sales patterns and it predicts how many people you need each shift. It's not magic, but it's the plumbing every Five Guys location will eventually have — your POS will start suggesting staffing levels based on demand, and you'll approve or override.

**What this means for you:** Scheduling is about to be data-first, not gut-first. Your Monday schedule-building will get faster. In the short term, you're ahead because you're already using Claude to stress-test schedule decisions. In a year, you'll need to understand how to evaluate whether the POS's recommendation is right for your specific store culture and constraints — that's where the operator intelligence comes in. Don't rely on the algo. Verify it against your context.

---

## 7. Skill Up — Do This Today

**Task:** Clean up your last CrunchTime labor export in 10 minutes.

**Steps:**
1. Go to CrunchTime, pull the labor report for today.
2. Highlight the entire export and copy it (Ctrl+C).
3. Open Claude (claude.ai), paste it in, and use this exact prompt:

```
Show me:
- Every employee who worked and their total hours
- Anyone whose hours appear inconsistent or repeated
- The total hours across all employees
- Any dates that look malformed
```

4. Read Claude's output. For each flag, verify it in the original export.
5. Make a mental note: "Did Claude catch something I would have missed?"

**Your follow-up question for next brief:** What was one inconsistency Claude caught that you didn't see initially? Let me know — it helps me calibrate what to watch for in future briefs.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---

