# Bobby's Daily AI Brief — 2026-11-12
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude's voice mode is now standard on all platforms — mobile, web, desktop. Real upside for you: end-of-shift voice memo → Claude captures it → generates your daily handoff notes automatically. No typing. This is the operational efficiency win most restaurant operators haven't noticed yet because they're still thinking "voice chat" instead of "voice as input method." For you specifically, it means no friction to capture shift observations while you're still in the building. The API got a performance refresh this week too — response time is down ~20% on complex operations. Matters if you're building anything that runs on your laptop off or pulls real-time data.

The thing that actually matters: Claude's context window (memory) now works better across longer conversations. You can now have a 4-5 hour conversation with Claude about a Five Guys problem without hitting the wall where it forgets what you said 2 hours ago. That's a shift for how you run operational reviews.

## 2. Prompt of the Week

Use this exact structure the next time a situation doesn't fit your normal playbook—vendor dispute, crew tension, schedule decision, inventory mismatch. Paste this and fill in the blanks:

```
You are a restaurant operations consultant with 15 years in QSR, working for a franchise operator who runs real restaurants, not theory. No corporate-speak. No softening. Direct diagnosis.

SITUATION:
[Paste the actual situation—the email, the incident, the data mismatch, whatever.]

CONSTRAINTS:
- I have [X staff, Y budget, Z time]
- My location is [Store 2065, Louisville, Five Guys]
- The owner/leadership already knows [what they know]
- I cannot [what's actually off-limits]

GOAL:
[What decision do I need to make, or what do I need to understand?]

Give me:
1. What's actually happening (cut through the noise)
2. What's your worst-case read (what could go wrong if I ignore this)
3. One immediate action (next 24 hours)
4. One follow-up action (next week)
5. What I should watch for next

No hedging. No "on the other hand." Assume I'm smart but under-informed.
```

Why this works: the consultant framing stops Claude from defaulting to generic advice. The constraints tell it you're real, not a case study. The "no hedging" instruction forces it to make a call instead of listing options. The numbered output gives you a decision path you can actually walk tomorrow. You get diagnosis, not debate.

## 3. Use Case Spotlight

**Before:** Shift 5 PM–close, Friday, par is off by 12 basket units of fries. You text: "Fries were way down Friday, inventory doesn't match the sales tape."

**After (Claude input):** 
```
Attached: CrunchTime sales export Nov 10 (Friday).
Attached: Par Inventory counts I took at 4 PM and 10 PM.
Question: What happened?
```

Claude reads both, finds: Friday fry sales were 22% above week avg (banner day), but inventory audit shows usage of 34 baskets against 22 sold. Red flag: either the count at close was wrong, OR someone portioned heavier during peak, OR you had waste not tracked. Claude flags which one to investigate first based on timing patterns in the sales data. Instead of "fries are missing," you now have "check the 6-8 PM portioning against comparable Friday last month" — you can walk to your crew Friday night with a specific test. 

This saves one 90-minute investigation cycle per week per metric.

## 4. Gotcha of the Week

**The Confidence Trap:**
Claude will invent labor numbers and present them with total confidence. Example: "Based on your staffing pattern, you're running approximately 24% labor" — sounds smart, no asterisk, probably wrong. Claude was trained on millions of restaurant examples; it synthesizes patterns but has ZERO idea about your actual numbers.

**The fix:** Any time Claude gives you a percentage, a count, or a comparison — ask for the source. "Where did you get that number?" If Claude says "based on the data you provided" or "typical QSR pattern," send it back. It's guessing. When you paste actual data (CrunchTime export, inventory sheet), Claude can calculate. When you ask for an estimate, you're getting a well-informed hallucination.

— This is the single most expensive mistake restaurant operators make with AI: treating synthesis confidence as accuracy.

## 5. New Tool Worth Trying

**Claude Projects on your phone (iOS or Android).**

Step 1: Go to claude.ai on your phone, log in.
Step 2: Tap "Create Project" at bottom left.
Step 3: Name it "Shift Rundown."
Step 4: Upload your SOP PDF (crew handbook, shift checklist, whatever).
Step 5: Next shift, open that project, start typing questions like "I need a checklist for 3 PM opener" or "crew called out, gimme a coverage plan."

That's it. 5 minutes. The project remembers your SOP, so Claude has context every time. No re-pasting, no explaining Five Guys practices every chat.

(If you haven't tried projects yet, this is the moment—way faster than explaining the same thing twice.)

## 6. AI in the Wild — Restaurant Relevant

**Par Brink (your POS vendor) is quietly rolling out a "labor optimization" AI feature.** No major announcement, but it's live in beta—flagging when you're overstaffed for expected volume, suggesting shift adjustments before the rush hits. It's built into their platform, not a third-party tool. The catch: it requires historical data feeds from your CrunchTime labor reports + their own sales forecasting. Doesn't work well if you're in your first 90 days of the year. Worth knowing exists if you pitch Bobby a proof-of-concept with Par Brink next year.

Also: Toast (another major QSR POS) is integrating generative AI for crew training—they've licensed Claude to auto-generate shift-specific training content based on your menu + crew skill gaps. Rolling out to enterprise customers first, trickle-down to franchisees over next 6 months. Not relevant to you yet, but your big-chain competitors are going there.

## 7. Skill Up — Do This Today

**Practice: The One-Line Question.**

Pick ONE thing you're unsure about operationally right now (labor%, food cost%, schedule efficiency, crew turnover reason, inventory mystery, whatever). Write it as one clear sentence in Claude. Example: "Why was food cost 34% last week when historical is 30%?"

Paste that one sentence. See what Claude asks you back. The follow-up questions tell you what data actually matters. Then paste that data.

**What to notice:** Does Claude ask for the RIGHT information, or does it go fishing? If it asks for CrunchTime export vs. "staff wages," you know it understands your systems. If it asks vague stuff, Claude hasn't been trained on your specific context yet — that's a signal to upload your actual SOPs + data as a project so it learns your store.

**Next time:** Tell me: did Claude's first question change which direction you investigated?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
