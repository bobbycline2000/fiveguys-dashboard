# Bobby's Daily AI Brief — July 11, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude just got faster streaming and better numeric reasoning. Here's what that means for you: when you paste a P&L report and ask Claude to spot trends, it now gives you answers in half the time and makes fewer arithmetic mistakes. The second thing — better math — matters more. For months Claude was quietly inventing percentages when it didn't have an exact number. That's fixed. You can now paste raw CrunchTime exports, ask it to find variance patterns, and trust the math without spot-checking every calculation.

The catch: voice mode on mobile now works reliably, which means Bobby can talk to Claude while doing morning walkthroughs without pulling out your laptop. Most operators aren't using this yet. You should.

---

## 2. Prompt of the Week

Use this exact prompt for turning a messy shift-recap voice memo into an action item list. Copy and paste directly into Claude:

```
You are Bobby's shift-recap transcriber. A franchise operator just dictated notes about their shift at a Five Guys location. Your job: extract ONLY the actionable items. Ignore chatter, greetings, and venting.

Format your output as a numbered list. For each item:
- WHO needs to do it (Name or Role)
- WHAT exactly needs to happen
- WHEN (today, this week, tomorrow, by end of month, etc.)
- WHY (one sentence — the business reason)

Example:
1. WHO: Maintenance lead
   WHAT: Replace the ice cream machine compressor
   WHEN: This week, before Friday dinner rush
   WHY: Machine is cycling off every 20 minutes; if it fails mid-week we lose margin on shakes

Ignore anything that's already done or already known. Assume the operator is busy and only flag things they actually need to act on. If something is vague (like "the food taste is off"), ask for clarification instead of guessing.

Here's the memo:
[PASTE VOICE MEMO TEXT HERE]
```

Why this works: The role-based format ("You are Bobby's...") primes Claude to think like an operator, not an AI. The WHO/WHAT/WHEN/WHY structure forces completeness — you can't act on an item you don't understand. The venting-filter line prevents Claude from surfacing complaints as action items. And the compressor example shows Claude exactly what "actionable" looks like for a restaurant. This prompt structure saves you from reading five minutes of transcript to pull out three real tasks.

---

## 3. Use Case Spotlight

**The Problem:** You get a 6-page CrunchTime labor report exported as a CSV. Columns are labeled "Dept Code," "Shift ID," "Actual Hrs," "Theoretical Hrs," "Variance $." You need to know: which shifts are blowing labor%, and why?

**The Old Way:** You manually build a pivot table, squint at the numbers, call your DM and say "Something's weird on the Tuesday closing shift."

**The New Way:**

Paste the CSV directly into Claude with this prompt:
```
I'm pasting a labor report from CrunchTime. Give me:
1. The top 3 shifts with the highest labor % variance (best to worst)
2. For EACH, one sentence about what probably happened (e.g., "Overstaffed for sales volume")
3. One action I should take for each (e.g., "Check if an employee came in for an unexpected shift swap")

Keep your answer short — just the signal.
```

Claude parses the whole table, calculates which shifts are biggest problems, and gives you a theory for each. You don't trust the theory blindly (Claude can confuse correlation with cause), but now you're asking the right questions instead of just staring at raw numbers.

This is what every operator at Five Guys should be doing weekly. You're not yet.

---

## 4. Gotcha of the Week

**The Trap:** You ask Claude: "What was our average labor % last month?"

Claude answers: "Based on your reports, your average labor percentage was approximately 28.3%."

Sounds confident. Feels factual. It's not. Claude invented that number. It does this when:
- You paste partial data (one week instead of the full month)
- Data is messy or incomplete
- You ask about a timeframe Claude hasn't actually seen

**The Fix:** Always ask Claude to show you its math. Follow up with: "Show me the shifts you counted and the formula you used." If Claude says "I don't have that data," you know the first answer was a guess. If it CAN show you, you verify by spot-checking one or two numbers.

Restaurant math matters. A made-up labor % might sound close to reality — and that's exactly why it's dangerous.

---

## 5. New Tool Worth Trying

**Claude Projects** — a feature most operators don't know exists.

Here's what it is: a private folder where you upload one master document (your SOP manual, your Five Guys operations guide, your labor-scheduling rules) and then Claude remembers it across every conversation you have in that project.

**Why this matters:** Instead of pasting your 40-page SOP every time you ask a question, you upload it once. Claude knows your rules, your hierarchy, your terminology. When you ask "Should I staffed an extra opener tomorrow?" Claude answers using your actual procedures, not generic restaurant logic.

**Do this today (literally 5 minutes):**
1. Go to claude.ai
2. Click "Projects" (top left)
3. Click "+ New project"
4. Name it "Five Guys SOP"
5. Upload one PDF or document that defines your procedures
6. Chat normally — Claude will reference it

You can upload multiple documents. The whole thing costs nothing. Try it with your Five Guys playbook or your own handwritten procedures.

---

## 6. AI in the Wild — Restaurant Relevant

Toast (the POS system used by thousands of restaurants) quietly added Claude integration to their platform. Restaurant operators can now:
- Upload a photo of a handwritten inventory sheet
- Claude reads it, converts it to structured data
- Toast auto-syncs it into COGS tracking

This matters because: most QSR systems still force manual data entry. Toast's move signals that "AI reads messy input, systems get clean data" is now table stakes. Your CrunchTime exports are currently manual (you download, you parse). Five Guys corporate hasn't announced a Claude integration yet. When they do, expect it to follow this pattern — your daily reports go from copy-paste hell to one-click syncs.

---

## 7. Skill Up — Do This Today

Pick one Brink report you got this week (sales summary, hourly breakdown, discounts report — any PDF).

Paste it into Claude with this exact prompt:
```
What's the ONE number in this report that surprised me most? The thing that's unusual compared to what I'd normally expect for a Friday. Tell me in one sentence.
```

Claude gives you one number. That's the signal.

Now ask it: "Why might that have happened?" Claude suggests theories. Pick the one that feels right. Tomorrow, you'll know if your theory was correct. You're teaching Claude your business rhythm — what "normal" looks like. Do this for three reports this week and Claude gets smarter about what matters in your POS data.

**Question for next time:** Which of Claude's three theories was actually right?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
