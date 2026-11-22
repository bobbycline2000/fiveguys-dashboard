# Bobby's Daily AI Brief — 2026-11-22
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Anthropic just closed its IPO on November 20th. That's not abstract — it means Claude's funding structure has changed, the company is public now, and expectations are different. What actually shipped? Claude Fable 5.2 and Claude Mythos 5.2 (Nov 9) — their most capable models for heavy technical work. For you as an operator, the real shift is **Claude is now betting its shareholder value on enterprise and government use cases**. GSA expanded the partnership to bring Claude to all levels of government (Oct 27). That's not a consumer play. That means the product direction is hardening around reliably-deliverable workflows for structured work — exactly the shape of what you're building. Claude doesn't get more experimental or sketch-heavy. It gets more reliable and more integrated into workflows that matter. Fable 5.2 is faster and cheaper than Opus for most work. If you're running tasks on Opus and paying the premium, Fable is worth a trial.

---

## 2. Prompt of the Week

**Scenario:** You're doing end-of-shift labor analysis. Your closing manager sends you a voice memo summarizing the night. You need an action item, the gap identified, and the follow-up for tomorrow.

```
You are Bobby Cline, GM of a Five Guys location in Louisville, KY. 
Your job is to extract insight from operational chatter and turn it into 
tomorrow's action.

I'm going to give you a voice memo from a closing manager. 
Extract:
- ONE thing that worked
- ONE thing that broke or felt wrong
- The root cause (why it happened, not just that it happened)
- Exactly what I should tell the opening manager tomorrow morning to prevent recurrence

Style: Direct. No corporate speak. The opening manager is busy. 
If I can't execute the action in under 60 seconds, tell me it's too complicated.

Here's the memo:
[PASTE THE VOICE MEMO TRANSCRIPT HERE]
```

**Why this works:** The opening lines establish role + authority (you, running a store). The extraction template is concrete — not "summarize" but "one good, one bad, root cause, action." The style constraint kills padding. The 60-second rule forces prioritization — if it's hard to fix, say so instead of sending the manager on a wild goose chase. This is what good feedback looks like in a restaurant: specific, actionable, respectful of time.

---

## 3. Use Case Spotlight

**Before:** You get a CrunchTime performance report as a CSV export. 350 rows of labor costs, hourly breakdowns, percentages. You squint. You paste it into Excel. You try to pivot it and get lost.

**After:**
```
Paste the CrunchTime export here:
[CSV data]

Bobby runs a Five Guys franchise in Louisville, KY. 
He cares about:
1. Where did labor creep this week vs last week (by hour)?
2. Which daypart is bleeding the most?
3. Is it a scheduling issue or a performance issue?
4. What's one thing to tell the team tomorrow morning?

Format the answer as a one-page summary with:
- Headline (one sentence that matters)
- The three numbers (this week vs last week, what shifted, by how much)
- The fix (concrete)
```

Bobby pastes it once. Claude returns a typed summary in 30 seconds. No Excel. No squinting. The CrunchTime export becomes a signal in a few seconds instead of a data fog. This is the highest-ROI use of Claude for an operator — taking the stuff the system spits out and turning it into a decision.

---

## 4. Gotcha of the Week

**The trap:** You ask Claude "How much did labor cost last month?" — a vague question. Claude returns vague: "Labor costs vary by location and daypart. Typically 25-30% of sales. To get your exact number, you'd need to..."

You feel like you asked the right question. You didn't. You got a non-answer because you asked a non-question.

**The fix:** Be specific. "My CrunchTime P&L shows labor at $X in October. This week it's $Y. Why? Is that normal? What should I expect?"

Now Claude can answer. You've given it the data. It doesn't have to theorize. When you ask vague, you get vague. This is the #1 failure mode for operators. You have the numbers sitting right in front of you. Put them in the prompt. Claude becomes 10× more useful the second you do.

---

## 5. New Tool Worth Trying

**Claude on iPhone — voice mode (5 minutes to try):**

1. Download Claude from the App Store (free tier works).
2. Open it.
3. Tap the microphone icon in the input box.
4. Record yourself: "What do I need to check before opening tomorrow?" or "Walk me through closing checklist in 2 minutes."
5. Claude speaks back.

That's it. You close, start voice memo, 60 seconds of audio, and Claude returns it verbally while you're doing other stuff. This is the highest-friction-to-reward tool we have — almost no lift, immediate payoff if you treat it like a voice journal. Not for strategy. For checklists, recaps, and "did I forget anything" at 10 PM when you're tired.

---

## 6. AI in the Wild — Restaurant Relevant

**Sweetgreen using AI for custom bowls** (NRN, Nov 18): Fast-casual chain announced they're running AI recommendations when customers build bowls — dietary filters, allergen avoidance, protein-to-veg ratios. The AI is consumer-facing; it's reducing decision friction at POS. Takeaway: QSR chains are not debating whether to use AI anymore. They're deploying it in the customer flow. Five Guys hasn't announced anything like this (yet). But Chipotle is pushing it (single-day sales records this month), Sweetgreen is rolling it, and the expectation-setting is loud. If you're running a franchisee dashboard, thinking about POS integration, or positioning for the consulting piece, this is the direction. The chains that move on this first win pricing power ("we know what you want before you order it = faster + higher average check").

---

## 7. Skill Up — Do This Today

**The exercise:** Use Claude to design a one-page "Closing Manager Checklist" that's specific to your store + your team.

Paste this into Claude:

```
I'm Bobby, GM of Five Guys 2065 in Louisville. 
My closing managers are: [names], and they vary in experience.
My biggest closing-time friction point is: [your biggest gap — delayed opens, 
  inventory discrepancies, labor creep, missed deposits, food waste, whatever stings].

Write me a one-page closing checklist that:
- Hits every section (cash, food, labor, prep, safety, security)
- Calls out MY specific problem (not generic)
- Uses checkboxes, not paragraphs
- Assumes the manager is tired and brain-fried at 10 PM
- Includes one "if X, then Y" conditional (how to handle a scenario)

Format: printable. 8.5x11, monospace, fits on one page.
```

Print it. Tape it by the door. Run it for a week. Watch what happens.

**Question for next time:** Which line item got checked off every shift and which one got skipped? That's where you're leaking.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
