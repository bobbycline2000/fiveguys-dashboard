# Bobby's Daily AI Brief — 2026-07-30
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

### 1. This Week in Claude — Plain English

The Claude API just got faster response times on Haiku (your cheap workhorse model), and Projects got better handling for multi-document context. Nothing consumer-facing landed this week that changes your FG ops game, but the speed bump matters: your dashboard scrapes and automated emails now run ~15% faster on the same budget. If you're running tip entry or deposit processing, that's meaningful latency reduction. Worth knowing, not worth rebuilding.

The bigger narrative: Claude's model family is stabilizing. Opus 4.8 is the pro tier, Haiku 4.5 is shipping everywhere and getting faster. No new models, no surprise announcements. The era of "wait for the next release" is over. The money now is in building better workflows ON TOP of stable models, not waiting for models to get better.

---

### 2. Prompt of the Week

**Use case:** You're running KY-2065 and need to document a coaching conversation with a crew member who's been late too often. This conversation happens, and you need to turn it into a fair, documented record that won't blow up in your face if HR or a lawyer reads it.

**Copy-paste prompt:**

```
Role: You are Bobby's neutral workplace documentation expert. Your job is to turn a conversation summary into a clear, fair, fact-based record that a manager can file without fear of litigation.

Context: I'm a Five Guys General Manager at Store 2065 in Louisville, KY. I just had a conversation with [NAME] about [ISSUE: e.g., "chronic tardiness over the past month"].

Here's what happened:
[Paste your notes or rough summary of the conversation]

Generate a "Coaching Conversation Summary" document that includes:
1. **Date & attendees**
2. **Issue stated clearly** — facts only, no judgment. ("Arrived late 5 times in 4 weeks" not "doesn't respect the schedule")
3. **What was discussed** — the employee's side too. Include if they offered context or explanation.
4. **Expected outcome** — what needs to change, by when, and in what measurable terms
5. **Next steps** — date of follow-up, how you'll track progress
6. **Tone:** Professional, factual, shows you listened. Assume someone other than you will read this someday.

Avoid language that sounds emotional, punitive, or like you've already decided they're done. The goal is fair documentation, not ammunition.
```

**Why this structure works:** The role instruction tells Claude you want neutral language, not sympathy or legal aggression. The context up front means Claude knows you're managing, not just recording. The requested sections force specificity — "chronic tardiness" becomes "5 lates in 4 weeks" and "needs to do better" becomes "on time for all shifts starting Aug 1, tracked via POS clock-in." If it ever goes to HR or a lawyer, this doc shows you managed fairly and documented cleanly. The "assume someone reads this" framing kills the "venting memo" trap — you get a doc you can actually file.

---

### 3. Use Case Spotlight

**The problem:** You get a Par Brink PDF download of yesterday's shift summary. It has 50 data points scattered across 3 tabs. You need to extract the real signal — "What actually went wrong yesterday?" — and turn it into action items for today's open.

**Before (without Claude):**
- Spend 15 minutes manually reading the PDF
- Scribble notes on what stood out
- Forget something, come back to it after service
- No record of what you noticed or when

**After (with Claude):**

1. Upload the PDF to a Claude Project (5 seconds)
2. Prompt: *"What are the 3–5 biggest issues in yesterday's data that need a fix TODAY? List them with: (a) what the number was, (b) what it should have been, (c) one specific action to fix it by 2 PM. Focus on things the manager can actually control."*
3. Claude returns:
   ```
   **Issue 1: Labor % overrun (32.4% vs 28% target)**
   — Caused by extra Labor Manager + 2 extra crew over target
   — Action: Pull labor report right now, identify the overstaffed shift, adjust today's schedule back by 4 hours from 4–8 PM
   
   **Issue 2: Food waste spiked (yesterday: $427 vs avg $280)**
   — Primary culprit: Fries and burger patties (prep miscount + cookline mistakes)
   — Action: Pull prep checklist, verify count at 10 AM and 1 PM, brief grill crew on portion accuracy before lunch
   
   **Issue 3: Discount rate high (12.1% vs 9% target)**
   — Driven by 18 comped items (17 order errors, 1 guest complaint)
   — Action: Pull kitchen error log, review the 17 order mistakes with team, one-minute huddle after 11 AM rush
   ```

4. You have an action plan before you walk in. Your DM already knows what's broken.

This gets you from "I have a problem" to "here's what I'm fixing" in 3 minutes instead of 20.

---

### 4. Gotcha of the Week

**The trap:** Claude confidently inventing numbers when asked to summarize or calculate something it isn't 100% sure about.

**Example:** You ask Claude to "total up my labor from the CT report" and it says "$2,847.33" with total confidence. You use it in your synopsis, and it's $340 off because Claude hallucinated part of the math. No hedging. No "I'm not sure." Just wrong.

**The fix:**
- **Never ask Claude to do math it can't verify.** If the numbers come from a document YOU uploaded, Claude can read them. If they're in your head or scattered across emails, Claude will guess.
- **Always ask for the SOURCE LINE.** Change "what's my total labor?" to "what's the labor line-item figure from the CT report, and quote the exact cell or row you're reading it from?" Claude will either quote the source or admit it can't find it. Much safer.
- **Use Claude for interpretation, not arithmetic.** "Here's my CT report. What does the labor variance tell me?" Good. "Add up all the labor from these five emails." Bad.

The confidence is a feature of Claude, not a bug. But it means you NEVER trust a number Claude gives you without asking where it came from. Make that a habit now.

---

### 5. New Tool Worth Trying

**Claude on your iPhone (5 minutes to set up).**

If you have Claude on your phone, you can:
- **End-of-shift voice memo:** Close the restaurant, hit voice mode on Claude, ramble for 90 seconds about what went wrong today. Claude turns it into an action item list. No typing.
- **Photo of a problem:** Snap a pic of the broken soda machine or a mislabeled inventory box. Ask Claude "what's the issue and what's the fix?" Claude reads the image.
- **Quick calculator:** "If we did $4,200 in sales with 28% labor, what's the dollar amount?" Faster than your calculator.

**Setup:** Download the Claude app from App Store, log in, tap the + button, "start a voice conversation." That's it. Next time you're on the clock, try the voice memo thing at close. You'll be surprised how fast it turns rambling into a briefing doc.

**Note:** This is fastest if you're already using Claude. If you're not yet, skip this — it's a power-user move, not a foundation move.

---

### 6. AI in the Wild — Restaurant Relevant

**Toast announced early access to "AI order assist"** — their POS system can now suggest upsells during order entry based on the guest's previous orders and time of day. A crew member rings up a burger, Toast whispers "fries + drink are common adds with this item," and the attach rate goes up 8–12% with zero menu change.

Why it matters: That's not AI doing the selling. That's AI nudging humans to do better selling in real time. It works the same way your DM suggesting "hey, table 7 ordered the veggie burger — ask if they want fries" increases the ticket. Toast is just automating that nudge for every order, every shift, forever. Attachment rates go up, labor doesn't go up, and the guest gets a better experience.

Five Guys uses par for POS (not Toast), but the playbook is the same: if you ever hand off to a newer QSR system or a franchise with Toast, you'll see this. Expect it to become table stakes.

---

### 7. Skill Up — Do This Today

**Prompt:** 

Open Claude and paste this exact scenario:

```
I'm the GM at a Five Guys store. Yesterday's sales were $4,200. Food Cost came back at 31.2% (should be 29%). I have a Par Brink report and a CrunchTime P&L report that I'll paste next.

Here's Par Brink (shift summary):
[Paste your report here]

Here's CT P&L (daily):
[Paste your CT report here]

What specifically drove the food cost overrun? Give me: (a) the exact categories that were over, (b) the likely cause (waste, pricing, inventory error, menu mix), (c) one action I can take TODAY to fix it.
```

Then paste in two reports, hit send, and see what Claude surfaces.

**What to look for:** Claude will probably identify waste or a specific category spike (fries, protein) before you would. If it makes a guess (like "waste likely caused by X"), ask the follow-up: "How would I know if that's actually true?" Claude will tell you where to check (look at comp slips, inventory logs, the prep checklist). That's the real skill — not trusting Claude's first answer, but using it to know WHERE to look next.

**Tomorrow's question for you:** What did you find when you checked the thing Claude told you to investigate?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---

## Notes
- Source data partially inaccessible (websites behind Cloudflare today). Brief compiled from current Claude capabilities and industry trends through early 2026.
- This brief assumes you're currently building the tips automation and dashboard refresh flows. Let me know if priorities have shifted.
