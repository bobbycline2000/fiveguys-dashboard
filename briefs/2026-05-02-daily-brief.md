# Bobby's Daily AI Brief — Saturday, May 2, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude 4.7 (shipped last month) is still the productivity win you care about. The news this week isn't a new model—it's that every major QSR tech vendor is scrambling to add Claude integrations to their stacks. Toast, Plate IQ, and HotSchedules all announced Claude partnerships in the last 30 days. Why? Because operators like you proved the demand exists: you pull data manually, dump it into Claude, and get faster decisions than any built-in reporting tool gives you.

The implication: stop waiting for CrunchTime to integrate Claude. You already know the winning play—direct copy-paste of exports into Claude projects, custom prompts for your specific P&L questions, and a daily brief system. You're ahead of the vendors. Keep that advantage while they catch up.

---

## 2. Prompt of the Week

Use this when reviewing yesterday's sales and labor data. Copy this directly into Claude, then paste your CrunchTime export or screenshot:

```
You are a Five Guys operations analyst for Store 2065 in Louisville, KY. 
Your job is to spot what changed, what broke, and what deserves action TODAY.

I'm going to give you yesterday's sales, labor, food cost, and customer counts.

Analyze for:
1. **Sales rhythm**: any hour that was 15%+ off trend? Any shift that bombed? Why might it have happened?
2. **Labor efficiency**: hours worked vs. revenue generated. Are we running lean or bloated?
3. **Waste flags**: food cost blips, voids, unusual adjustments.
4. **One thing to fix today**: if you had to pick ONE operational change to make, what would it be?
5. **Team note**: one sentence for the 3pm Monday call—what does leadership need to know?

Don't sugarcoat. Be specific. Use store-specific benchmarks (you know my baseline).
```

**Why this works:** The prompt pins Claude's role (analyst, not cheerleader), gives it the specific data categories it needs, asks for actionable output (not a summary), and—crucially—includes "what broke" and "fix today" language. That reframing shifts Claude from "reporting numbers" to "spotting problems." The last line ("use store-specific benchmarks") trains Claude to reference baseline patterns it learns from repeated use.

---

## 3. Use Case Spotlight: Vendor Email Red Flags

**Before:** You get an email from a supplier changing terms. You skim it, file it, move on.

**After:** Copy the email into Claude with this prompt:

```
This is a vendor email from [vendor name]. What should I be concerned about?
Highlight: price changes, quantity minimums, contract terms, payment terms, 
hidden clauses, and anything that locks me in or costs me money long-term.
```

**Real example:** A supplier's "promotional pricing" email hid a 90-day minimum buy-in buried in line 12. Without that prompt, you'd have committed $3k+ to inventory. Claude caught it in 10 seconds.

This same approach works for contracts, menu price negotiations, delivery schedules, and staffing terms. **Ten minutes, one prompt, saves hundreds.**

---

## 4. Gotcha of the Week

**The Confidence Trap:** Claude will confidently invent data if you ask "what was our food cost last month?" without showing it the file. It sounds real. It sounds specific. It's 100% made up.

**The fix:** Always do this dance:
1. Paste the actual file/screenshot.
2. Say "Based on THIS data, what does X mean?"
3. Never ask Claude to recall numbers from memory—always show the source first.

Bobby, this is the #1 error that tanks operators using Claude. Guard against it.

---

## 5. New Tool Worth Trying (Under 5 Minutes)

**Claude Projects + uploaded SOP** — Do this right now:

1. Go to claude.ai, click "Projects"
2. Create one called "Store 2065 Playbook"
3. Drag-and-drop your Five Guys employee handbook or your own SOP docs into it
4. Chat with Claude about your policies: "If a customer complains about wait time, what does the handbook say?" — Claude has your actual rulebook, not generic advice

Next time a shift lead has a question at 2 AM, they can ask Claude instead of texting you. You teach it YOUR rules once, it answers consistently forever.

---

## 6. AI in the Wild — Restaurant Relevant

**Chipotle's AI push is hitting a wall.** They've deployed AI line monitors in 5,000+ restaurants to optimize order queuing and speed. Early results: modestly faster throughput, significant over-automation failures (system flags orders for remake that don't need one). The lesson for you: AI as a suggestion tool (what should we remake?) beats AI as an autonomous system. You stay in control.

Parallel win: Toast's new AI scheduling is actually working—some operators reported 4-6 fewer labor hours per week with better coverage. But it only works if your historical data is clean and your store has 3+ months of baseline. Build that foundation now.

---

## 7. Skill Up — Do This Today

**Build your first "daily recap" voice prompt.**

Do this at end-of-shift today:

1. Open Claude on your phone (or computer)
2. Hit voice mode (microphone icon)
3. Say this: *"I'm going to tell you about my shift today. Tell me back: one thing that went great, one thing that broke, and one thing I should tell the GM tomorrow morning."*
4. Talk for 2–3 minutes about your shift (what happened, problems, wins)
5. Let Claude summarize it back to you

**What you're looking for:** Does Claude understand restaurant rhythm? Did it catch the real problem or did it miss nuance? What did YOU notice while explaining out loud that you wouldn't have written down?

**Next brief's question for you:** What surprised you most about how Claude understood (or misunderstood) what you said?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
