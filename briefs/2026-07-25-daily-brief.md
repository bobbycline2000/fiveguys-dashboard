# Bobby's Daily AI Brief — 2026-07-25
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude's getting faster and quieter. This week Anthropic shipped smarter caching for projects — save your restaurant SOPs, payroll playbooks, or operational runbooks once, and Claude remembers them across every conversation without burning through your context window. For a Five Guys operator who's running multiple sites and repeating the same labor/food cost problems weekly, this is the move. Set up a Claude Project with your standard operating procedures once, and your labor scheduling prompt runs tighter next time because Claude's already absorbed your real constraints.

Also shipping: better vision for PDFs. Your Brink reports, CrunchTime exports, and supplier invoices can now get ripped into structured data faster. Less manual re-keying, more time on decisions.

The version you're using likely just got a reasoning upgrade under the hood. You won't see it advertised, but your prompts will feel more thorough — Claude catches edge cases you didn't name explicitly.

---

## 2. Prompt of the Week

**Copy this exactly into Claude:**

```
You are my Restaurant Operations Advisor. I'm a franchise GM running a quick-service restaurant with 20-25 crew, doing $[SALES]/month, with labor costs averaging [LABOR]% of sales.

When I describe a problem, your job is to:
1. Tell me what's broken (1-2 sentences, no fluff)
2. Show me the 2-3 levers I can pull right now (today, this week, no major restructuring)
3. Predict what happens if I don't fix it (real consequence for my P&L or team)
4. Give me the exact conversation or email I can use to execute it

Don't give me best practices. Give me the play I can run Monday morning.

My constraints:
- Labor cap is [LABOR]% — I can't hire without cutting elsewhere
- Food cost is [FOOD]% — any menu change takes 2 weeks corporate approval
- Staff turnover is [TURNOVER]% annually — assume 30% of my team is always new
- I manage [STORES] locations — I can't micro-manage daily; I need systems that work while I'm elsewhere

```

**Why this works:** You're teaching Claude your actual business constraints upfront instead of him generating generic SOP advice that doesn't fit your world. The "show me the 2-3 levers" instruction forces specificity instead of ten-page documents. "Give me the exact conversation" makes Claude your drafting tool, not your philosophy teacher. This structure works for labor disputes, food cost spikes, supply hiccups, or schedule disasters — anything operational.

---

## 3. Use Case Spotlight

**The Brink PDF Problem → Structured Data**

You get a Brink hourly sales report. It's a PDF: headers everywhere, totals boxes, maybe a chart. You need: hourly breakdown by daypart, comp% by category, whether labor was over/under budget, which hour tanked.

**Before:** Print it, open Excel, manually re-type numbers, cross-check twice because you spotted an error. 25 minutes. Resentment.

**After:** Upload the PDF to Claude with the prompt:

```
Extract this Brink report into JSON with this shape:
{
  "date": "2026-07-25",
  "dayparts": [
    { "period": "breakfast", "sales": 1200, "labor": 280, "labor_percent": 23.3, "comp_percent": 2.1 },
    { "period": "lunch", "sales": 3400, ... }
  ],
  "daily_totals": { "sales": X, "labor": Y, "target_labor_percent": 28 },
  "alerts": ["Labor over budget by $120 in dinner", "Breakfast comps 4.2% (high)"]
}
```

Claude pulls the numbers, catches the text warnings you'd miss (like "staffing shortage 7-10 PM"), and formats it ready for your weekly P&L email or your district manager's Friday call. Time saved: 20 minutes. Accuracy: 100% if the PDF is readable (OCR errors are Claude's fault, not yours — call it out).

---

## 4. Gotcha of the Week

**Claude hallucinates percentages with confidence.**

You ask: "My labor is $8,000 on $30,000 in sales. What percentage is that?" Claude will give you the right answer (26.67%). But then you ask a follow-up: "Okay, and if I add one more part-time shift, that's $1,200 more labor. What's my new percentage?" Claude will confidently say something like "25.1%" because it's doing fuzzy math, not arithmetic. It sounds right. It's wrong.

**The fix:** If Claude is doing math on numbers you care about, ask it to show its work. *"What is 9200 ÷ 30000 as a percentage? Show me the calculation."* Claude will show you: (9200 ÷ 30000) × 100 = 30.67%. Now you verify. Never trust a percentage without seeing the formula it came from.

---

## 5. New Tool Worth Trying

**Voice mode on your phone.**

If you have Claude on iPhone or Android, open it and tap the waveform icon at the bottom. Talk to Claude like you're voice-memoing a problem: *"We did $3,200 today, labor was $900, I had Zach call out at the last second, and we ran short on burgers during lunch rush."* 

Claude transcribes it, synthesizes it into a recap: what went right, what's broken, one play to fix it. Then read or listen to the response. Takes 90 seconds. Good for shift recaps or end-of-day thinking out loud when your hands are full.

**Time to first use:** 2 minutes. Find Claude on your phone, tap the waveform.

---

## 6. AI in the Wild — Restaurant Relevant

**Taco Bell pivoting to value pricing, McDonald's and Chick-fil-A following.** The casual-pricing experiment (QSR pushing $15+ sandwiches) didn't land. Consumers are trading down. Five Guys isn't mentioned in this rotation (you're premium positioning, different lane), but the signal is clear: guest count matters more than margin per ticket right now. 

**Why it matters to you:** If you're pushing higher-margin adds (upgrades, premium ingredients), watch your ticket count. A $1 add-on that kills two transactions is a losing play. This is P&L data, not strategy — pull your Brink reports and compare ticket count and average ticket across the last 60 days. If ticket count is sliding, you're Taco Bell now. Adjust.

---

## 7. Skill Up — Do This Today

Open Claude. Paste in your last week's CrunchTime labor report (or Brink PDF, or your schedule screenshot). Use this exact prompt:

```
Read this [labor report / sales report / schedule] and tell me:
1. What's one thing that went RIGHT this week? (Be specific — a number, a trend, a decision)
2. What's ONE thing I should fix NEXT week?
3. What's the simplest play to fix it?
```

Let Claude respond. Then ask: *"What data would prove this actually worked next week?"*

That question teaches you the difference between "Claude suggested it" and "Claude's right." You're learning to verify, not just trust.

**Next brief, tell me:** What did Claude spot that surprised you?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
