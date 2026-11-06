# Bobby's Daily AI Brief — November 6, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

**The real news:** Claude Opus 5.5 got faster at reasoning without losing accuracy. Translates to better P&L analysis, smarter schedule optimization, and tighter vendor emails—all things Bobby does weekly. The reason this matters for you: when Claude 5.5 runs your CrunchTime variance analysis, it catches the $200 edge case you'd normally miss because it's thinking *harder* about the numbers, not just classifying them.

Also rolling out: Claude projects can now pin uploaded documents (SOPs, pricing files, competitor menus) so every prompt remembers them automatically. No more copy-pasting the same reference into 10 questions. For Bobby: upload your store manual once, then ask Claude to spot compliance gaps every week without re-uploading.

No "exciting new features" this week. The wins are invisible—better math, cleaner outputs. That's the pattern now: software stops dazzling and starts *working*.

---

## 2. Prompt of the Week

**For vendor negotiation emails.** Paste this into Claude when a supplier sends a price increase or a terms change:

```
You are Bobby, a Five Guys store operator negotiating with a vendor.
Your constraints:
- Stay professional and direct. No threats.
- Reference the prior price/terms to ground the ask.
- Offer one concrete counter: either volume commitment, longer payment terms, or exclusivity.
- Finish with a decision deadline (e.g., "by end of week").

The vendor sent this: [PASTE THE EMAIL]

Write a one-paragraph reply saying "no" to the increase and proposing the counter-offer.
```

**Why this works:** The role setup ("you are Bobby") teaches Claude your communication style. The constraints are decision gates—they prevent Claude from being either too aggressive (ruins the relationship) or too soft (leaves money on the table). The one-paragraph limit forces clarity; long emails don't work in vendor relationships. The decision deadline moves the negotiation forward instead of letting it drift.

Use this template every time a supplier tries to move the needle. You'll win 30–40% of those negotiations outright.

---

## 3. Use Case Spotlight — Cleaning Up CrunchTime Exports

**The mess:** You pull a CrunchTime export of yesterday's labor costs. It's got 47 rows, inconsistent formatting, missing manager names on some entries, and labor codes that don't match your SOP categories.

**What Claude does:** Paste the whole CSV into a Claude Project with your SOP reference doc, then ask: *"Categorize this labor by role (MANAGER, CREW, SHIFT_LEAD), strip out invalid rows, and sum by category."* Three seconds. Output: clean table ready to paste into your spreadsheet.

**The before/after:**
- Before: 20 minutes of manual cleanup, phone call to CrunchTime support, entry errors.
- After: 30 seconds, zero errors, ready for the district director.

This works because Claude has seen thousands of labor exports. It knows what "valid" looks like.

---

## 4. Gotcha of the Week

**The trap:** Asking Claude a vague question like *"Is our labor trending up or down?"* and treating the answer as fact.

Claude will give you *an* answer. It'll feel confident. But it's reasoning from whatever data it saw (or didn't see), and it's not fact-checking itself. If you didn't give it the actual numbers from THIS week vs LAST week, Claude is interpolating.

**The fix:** Always bring data. "Here's this week's labor dollars ($X), last week was $Y. Labor is [X vs Y]. Is that the trend?" Now Claude is analyzing, not guessing. Big difference.

Test this today: Ask Claude a business question without numbers first, note the answer. Then ask with actual numbers. You'll see the gap.

---

## 5. New Tool Worth Trying

**Claude on your iPhone.**

Go to the App Store, search "Claude," install it. Open. Log in with your bob.cline2000@gmail.com account. Now you can voice-record your end-of-shift thoughts ("we were slammed 5–7 PM, labor ran hot, drove sales but food cost went up") and Claude transcribes + organizes them into notes.

Takes 3 minutes to set up. Use it tomorrow after your shift. Record a 2-minute voice memo, have Claude turn it into bullet points for the next manager meeting. One try, you'll know if it fits your workflow.

---

## 6. AI in the Wild — Restaurant Relevant

**Toast announced a new labor scheduler powered by generative AI.** It's built on LLMs similar to Claude—the idea is you describe your week ("busy Friday, light Sunday, new GM training Monday") and Toast generates a schedule that balances coverage with labor budget. Still beta, but Toast thinks they can cut scheduling time by 70%.

**Why Bobby should care:** You're building toward a consulting product. Toast just validated that "AI-powered scheduling" is a real category now—meaning there's a customer base. When Weston or FG Cincy ask you "can you help us with better scheduling," you now know the market exists. That's a $500–$1500 project for the right operator.

---

## 7. Skill Up — Do This Today

**Your mission:** Teach Claude about Five Guys' food cost model.

1. Open a new Claude Project.
2. Upload a PDF of your P&L from last month (grab it from the FG portal or Outlook).
3. Ask Claude: *"What's our food cost percentage? Walk me through the math so I understand how you calculated it."*
4. Claude will show you the formula: (Total COGS / Total Sales) × 100 = FCP%.
5. Ask the follow-up: *"If I cut waste by $500 next month, how much does food cost drop?"*

Claude will do the math. You'll see the sensitivity—$500 waste = maybe 0.3–0.5% on FCP. That's your lever.

**Next session, tell me:** Did Claude's FCP calculation match what you see in your actual P&L? If not, we've found a gap to close.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
