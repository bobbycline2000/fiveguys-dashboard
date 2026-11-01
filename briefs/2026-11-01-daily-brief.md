# Bobby's Daily AI Brief — 2026-11-01
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

No new Claude consumer features dropped this week. Anthropic's been quiet on the product side — last major release was Claude Projects + Artifacts, which you're already using. The silence is worth noting though: Anthropic is in a revenue/reliability phase, not a feature-sprint phase. That's good for operators like you because it means they're hardening what works instead of chasing hype.

What matters for your ops: **Claude on iPhone** is stable now. If you're doing end-of-shift voice memos or quick questions on the floor, it's worth trying. Takes the laptop out of the decision loop when you're managing, not sitting in an office.

---

## 2. Prompt of the Week

Use this exact prompt when you need to document a problem that keeps happening — a customer complaint pattern, a staff friction point, a quality issue that's repeating:

```
You are an experienced restaurant operations consultant reviewing a real pattern from my store.

I'm going to describe something that keeps happening. Your job is:
1. Name the root cause (not the symptom)
2. Tell me the one thing I can change operationally to stop it
3. Flag if this is likely a training issue, a system issue, or a people issue
4. Give me exactly one way to test if your fix worked

Keep your answer to 4 sentences. Be direct — don't soften it. If my current process is the problem, say so.

Here's what's happening: [DESCRIBE THE PATTERN]
```

Why this works: The roles and constraints teach Claude to think like an operator instead of a consultant. "One thing I can change" prevents the kitchen-sink answer. "Exactly one way to test" forces you to actually verify instead of hoping. The training/system/people filter cuts through the noise — most operators conflate these three and end up blaming people when the system is broken.

---

## 3. Use Case Spotlight

**The CrunchTime Export Cleanup.**

You get a daily P&L export from CrunchTime. It's messy — merged cells, non-standard number formats, headers in weird places. You spend 20 minutes cleaning it before you can actually analyze it. Claude can do that in 30 seconds.

**The move:** Upload the raw CrunchTime export to a Claude Project. Give Claude this prompt:
```
This is a raw export from our CrunchTime P&L. Clean it:
- Extract date, total sales, food cost %, labor %
- Convert percentages to decimals (85% → 0.85)
- Flag any number that looks like an error (negative sales, labor > 100%)
- Give me back a clean JSON with these fields

Only output valid JSON, no explanation.
```

**Before:** 20 minutes, error-prone, you're re-entering numbers

**After:** 20 seconds, perfect JSON, feeds directly into your dashboard or your Excel summary

This is literally the kind of work Claude was born to automate. You're not asking for analysis yet — just format conversion. Easy win, repeatable.

---

## 4. Gotcha of the Week

**Claude hallucinates dates hard.**

You ask: "What day of the week is November 5th?" Claude answers with total confidence: "That's a Thursday." You plan your week around it. Except November 5, 2026 is actually a Wednesday.

Claude doesn't have a real calendar. It's pattern-matching on text. When you're planning anything that depends on a specific date — a schedule, a marketing push, a supply order — **verify the day of the week with a calendar app or Google, not Claude.**

The fix: Always say "verify this with a real calendar if it matters" before you act on a Claude date answer. Takes 10 seconds. Saves you from a Wednesday shift surprise.

---

## 5. New Tool Worth Trying

**Claude for Chrome — 5 minute setup.**

You need to check something on a vendor website, grab a price, screenshot a menu format, or reference something while you're asking Claude a question. Instead of alt-tabbing, use Claude in the same browser.

**Exact steps:**
1. Open Chrome
2. Go to `chrome.google.com/webstore`
3. Search "Claude for Chrome"
4. Click "Add to Chrome"
5. Pin the extension icon to your toolbar (click the puzzle icon, find Claude, click the pin)

Now when you're on any website, click the Claude icon and type directly. You can see the page while Claude sees it too. Paste text from the page into your question without copy-pasting.

This is a **browser extension**, not a new app. One click to install, done forever.

---

## 6. AI in the Wild — Restaurant Relevant

**Toast (your competitor's POS) is getting sued by the FTC.**

Toast claims 24/7 support and flat monthly rates. The FTC alleges they hide fees, don't deliver the support, and lock franchisees in. If you've ever looked at Toast as an alternative to Par Brink — this matters. What looks simple often isn't.

The lesson for you: **when you're evaluating any vendor tool — POS, scheduling, inventory — ask for the contract upfront.** Run the small print by Bobby Hess (your Director, Crystal Hess's contact) or a lawyer before you commit. Vendor promises change after signature.

Five Guys corporate is staying quiet on the Toast drama, which is smart. Keep your own ops clean and don't get caught off-guard by a vendor's legal mess.

---

## 7. Skill Up — Do This Today

**Build a 60-second shift-close voice memo.**

Use Claude on iPhone (if you have it) or Claude on your desktop. At the end of your shift today, record a 30-second voice memo covering:
- One thing that went right
- One thing that broke
- One decision you made that worked

Then paste it into Claude with this prompt:

```
This is a voice memo from my shift close. Turn it into a short note for my Director (Crystal) that flags one action item and one win. Keep it under 50 words.
```

Watch what Claude pulls out of a rambling voice memo. The skill here is delegation — you're not writing a formal email, you're talking naturally and letting Claude format it. This is how you actually work lights-out: record, paste, done.

**Question for next time:** What was ONE decision you made today that you wish you'd documented while it was fresh?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
