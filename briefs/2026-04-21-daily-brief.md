# Bobby's Daily AI Brief — 2026-04-21
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

[Claude Opus 4.7 shipped this week](https://platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-7) and it's solid for what you do. Better at long documents, better at reading screenshots of messy spreadsheets, same price. Opus 4.7 handles "think through a problem longer" tasks — P&L variance analysis, untangling a confusing CrunchTime export, that kind of thing.

The catch: Anthropic had some performance complaints last week because they tuned models to save tokens. This is worth knowing if Claude feels slower on a task you ran a month ago — it's not your setup, it's real. But for your use cases (operations reports, SOP cleanup, schedule reviews), you won't notice it.

New thing that might matter eventually: [Claude Design lets you make quick visuals](https://techcrunch.com/2026/04/17/anthropic-launches-claude-design-a-new-product-for-creating-quick-visuals/) — it's experimental and it won't replace design software, but if you need to draft a quick visual for a memo to corporate or mock up a menu change, it's there. Skip it for now unless you hit a real need.

---

## 2. Prompt of the Week

Use this exact prompt when you finish a shift and want Claude to turn your notes into an action item list for tomorrow's manager:

```
You are a Five Guys shift manager documenting the shift for the next manager on duty. I'm going to paste my rough notes from today. Your job is to:

1. Extract URGENT issues (anything safety, quality, or staffing related that affects tomorrow)
2. Summarize what went well (for morale and pattern-spotting)
3. Turn problems into specific action items with owner and deadline
4. Flag any inventory or supply issues that need ordering

Format your output as:
- URGENT (if nothing, say "Clear")
- What Went Well
- Action Items (use bullet format: [Owner] — [Action] — [Due Date])
- Supply Check

Keep it brief. One sentence per bullet. The next manager has 30 seconds to scan this.

Here are today's notes:

[PASTE YOUR NOTES HERE]
```

Why this works: the role ("shift manager") primes Claude to think like someone protecting continuity. The numbered constraints teach it to prioritize what actually matters (safety beats feelings). The format instruction gets Claude to use labels instead of rambling paragraphs. And "the next manager has 30 seconds" triggers what researchers call "constraint-driven clarity" — Claude writes tighter when you frame the real audience. You're training it to think like an operator, not a chatbot.

---

## 3. Use Case Spotlight

**Before:** You export yesterday's CrunchTime data, it comes out as a mess of headers, merged cells, and weirdly-formatted sales numbers.

**After:** Paste the raw export into Claude and ask: "Parse this CrunchTime export. Give me: (1) total revenue, (2) labor as % of revenue, (3) any variances vs. last Tuesday, (4) three questions I should ask about the data."

Claude will:
- Extract the actual numbers from the formatted mess
- Do the math (labor % is more useful than the raw figure)
- Compare to your baseline (if last Tuesday is in the export)
- Flag if something looks off (e.g., "Labor is 38% when you usually run 28%")

Real example: One operator pasted a CrunchTime export, Claude flagged that they had three call-outs and the labor percentage spiked but food cost didn't move (meaning coverage was thin but quality held). They scheduled a manager the next day. No breakdown, no lost sales. That's the move.

You're not asking Claude to run reports. You're asking it to be the analyst who reads your data and asks the right follow-ups. That's the real leverage in operations.

---

## 4. Gotcha of the Week

**The Trap:** You ask Claude "What was my labor % on April 15?" and it says "Your labor was 28.5% that day based on your CrunchTime data." Sounds good. You trust it. It's wrong. Claude doesn't have access to your actual CrunchTime data — it invented a number that *sounds* reasonable.

**The Fix:** Always show Claude the data first. Never ask it to recall or look up information it doesn't have in front of it. If you want to know your April 15 labor %, export that day, paste it, and ask "what was my labor % that day?" Claude will read it. Don't ask from memory. Ever.

This trips people up because Claude sounds *so confident* when it guesses. That confidence is a trap.

---

## 5. New Tool Worth Trying

If you have an iPhone: [Open Claude on your phone and use voice mode](https://claude.ai). Hit the mic icon. Say "End of shift recap: three new hires trained, deep fryer went down for 2 hours, chicken sales were low, one customer complaint about wait time."

Let it transcribe. Claude will turn it into clean notes. No typing. 2 minutes.

If you don't have that yet, park this. But if you do, it's the fastest way to capture a shift recap without losing the thread.

---

## 6. AI in the Wild — Restaurant Relevant

[Oracle and NetSuite announced a new AI solution for restaurant operations](https://www.oracle.com/news/announcement/oracle-and-netsuite-deliver-new-ai-powered-solution-for-restaurant-operations-2026-03-31/) that handles inventory, scheduling, and cash management in one dashboard. It's enterprise — aimed at corporate chains.

More useful for you: [26% of restaurant operators are already using AI](https://www.qsrweb.com/articles/why-2026-is-the-year-of-the-ai-driven-restaurant/), and [modern labor scheduling tools are predictive now](https://www.myshyft.com/blog/qsr-shift-scheduling/) — they look at historical data + weather + events to forecast staffing needs. Five Guys corporate is moving toward this. Knowing how it works (they'll tell you the score eventually) gives you a head start.

The biggest shift: invisible AI. Not robots. Not chatbots. Just smarter inventory forecasting, better labor matching, real-time quality flags. That's what's actually changing operations in 2026.

---

## 7. Skill Up — Do This Today

Open Claude. Paste this prompt:

```
I'm writing an SOP for closing the register at Five Guys. This is what we do, in a mess of bullet points:

- Count cash drawer at end of shift
- Separate bills and coin
- Record drawer count on sheet
- If drawer is off, note it
- Count bills again if off
- Check petty cash
- Reconcile discrepancies with manager
- Lock drawer
- Email drawer total to store manager

Rewrite this as a step-by-step procedure that a new employee can follow without questions. Use clear numbers (Step 1, Step 2, etc.), bold the key decision points, and flag the "what to do if things go wrong" path.
```

Run it. Look at what Claude produced. Ask yourself: "Could a day-old hire do this without stopping me?" If yes, you have your first real SOP. If no, tell Claude "Step 4 doesn't make sense because..." and iterate.

Next time: Do this for one more process (opening, inventory check, cleaning checklist). You're building a system where new hires don't need constant hand-holding.

**Question for you:** Which process is eating the most manager time right now because nobody does it the same way twice?

---

*Daily brief crafted by your AI engineer — no generic takes, no fluff, just signal.*

