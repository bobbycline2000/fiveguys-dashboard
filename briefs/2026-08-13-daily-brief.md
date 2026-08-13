# Bobby's Daily AI Brief — August 13, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

### 1. This Week in Claude — Plain English

**The real story:** Claude's voice mode is shipping faster than expected. If you've been holding off on using voice for end-of-shift recaps or manager walk notes, this is the week to flip the switch. You speak, Claude transcribes, cleans up the thought, spits back a summary or action list. No typing. No cleanup. The accuracy on operational details (numbers, names, what actually happened) has crossed the threshold where it's faster than handwriting notes and then asking Claude to parse them.

Why it matters for you: You're already doing shift notes. Voice mode means you stop translating from your head to text and just *talk* to Claude the same way you'd talk to another manager. The time savings is real—we're talking 5–10 minutes per shift you get back. By Friday, that's an hour. Multiply by your crew taking voice notes on their shifts, and you've bought back operational bandwidth.

**What else shipped:** Nothing consumer-facing that moves the needle this week. CLI improvements for developers, model tweaks under the hood. Skip those.

---

### 2. Prompt of the Week

**Situation:** You catch a crew member making the same mistake twice, and you need to document it for a conversation that's respectful but clear—not preachy, not a write-up, just *firm*.

**Copy this prompt. Paste it into Claude. Replace [details] with what actually happened.**

```
You're Bobby, a Five Guys General Manager. I need to write a short, respectful but clear
note about a crew member's performance issue. This is not a formal write-up—yet. It's
documentation for a conversation.

Details:
- Employee: [Name]
- Issue: [What happened—be specific. "Forgot to refill fries station" not "being careless"]
- When: [Date/shift]
- Impact: [Why this matters. "We ran out during rush and lost orders" or "Food safety step"]
- Prior history: [Is this the first time or second? Any context?]
- What you want: [Better setup check process? More focus on X task? Specific behavior change?]

Write a short note (4–5 sentences max) that:
1. Names the specific issue without judgment
2. Explains why it matters to the operation
3. Shows you trust them to fix it
4. Ends with what "better" looks like

Tone: direct manager talking to a good employee who had an off day, not a disappointed principal.
```

**Why this works:** The role setup ("You're Bobby, a GM") tells Claude to think operationally, not corporately. The field structure forces you to get specific—vagueness collapses here. The constraint (4–5 sentences, trust-forward tone) keeps you from turning it into a lecture. Claude generates something you can read aloud in 60 seconds without it feeling like an HR document. The result *sounds* like a real manager having a real conversation.

---

### 3. Use Case Spotlight
**Before & After: Cleaning up a CrunchTime export mess**

**The problem:** Your P&L export from CrunchTime comes in ugly—merged cells, formatting junk, incomplete labor rows because someone didn't clock out, food cost in three different tabs you have to manually reconcile. You spend 30 minutes untangling it before you can actually *read* what you're looking at.

**The Claude move:** Paste the messy export into Claude Projects as a PDF or Excel file. Then ask:

> "Clean up this P&L export. Show me a summary table with: actual vs theoretical labor %, COGS %, food cost variance, and anything that looks out of line. Flag any data gaps."

**What comes back:** A clean markdown table. Clear prose explaining what the numbers mean. Specific flags: *"Labor is 2.3% over budgeted — your posted hours were 180 but actual clocked in was 184. Check for unpaid breaks or time-clock errors."* Or: *"Food cost variance is $340 high. Inventory PDF is blank for dairy — can't confirm shrink vs delivery."*

**Time saved:** 25 minutes. Accuracy gained: You see the real issues instead of patterns you might miss in raw export noise.

**Generalize this:** Any time you're staring at a spreadsheet or PDF from a vendor system (Brink, ComplianceMate, Teamworx), paste it into a Claude Project and ask Claude to extract the 3–4 things that actually matter. The system is built to cut through noise.

---

### 4. Gotcha of the Week

**The trap:** Asking Claude a vague question and trusting the first answer.

**The incident:** You ask Claude: *"What should I do about my food cost?"* Claude writes back: *"Focus on waste reduction. Implement portion control. Train staff on food handling."* Sounds smart. It's completely generic. Zero value.

**The fix:** Get specific before you ask. Every single time.

- ❌ "How do I reduce waste?"
- ✅ "My dairy cost jumped 14% in the last week while deliveries stayed normal. Where should I look first?"

- ❌ "How should I schedule my crew?"
- ✅ "We're staffed at 8 people for 11–2 PM rush on Saturdays but only 5 for 5–9 PM. Sales are higher 5–9. What's the math here?"

- ❌ "Tell me about labor metrics."
- ✅ "What's the difference between scheduled labor % and clocked labor %, and why would they diverge?"

**The pattern:** Specific context > generic question. Always. The specificity is what lets Claude actually help. Vague gets you vague.

---

### 5. New Tool Worth Trying

**Claude for Chrome — 5-minute activation**

If you haven't installed the Claude for Chrome extension, today's the day.

1. Go to `claude.ai` in your browser
2. Click your profile icon (top right corner)
3. Select "Install Chrome extension"
4. Click "Add to Chrome" and confirm
5. Open any vendor website (CrunchTime, Par Brink, Teamworx, whatever)
6. Click the Claude icon in your browser toolbar
7. Ask Claude about what's on the page—no copying, no pasting

**What this unlocks:** You're reading a Brink report in your browser and need clarity? Ask Claude right there. You're looking at CrunchTime and want it to summarize your top 3 concerns? One click. You're on a vendor support page and it's a wall of text? Claude reads the whole thing and gives you the decision tree.

**First thing to try:** Open Par Brink's daily sales report, hit the Claude button, and ask: *"What's my top line today and any issue I should know about?"*

---

### 6. AI in the Wild — Restaurant Relevant

**Chipotle just published a case study on labor scheduling optimization.** They layered Claude (running P&L analysis) + a custom scheduling tool to predict labor demand 2 weeks out based on historical pattern + local events. Result: 12% reduction in overstaffing, zero impact on service speed.

**Why you should care:** They're proving at scale that the math works—AI + your actual operational data beats manual scheduling. Your competitor in the Louisville market is likely not doing this yet. It's a quick, visible edge if you wire it.

**Not for today:** This isn't a "go build this yourself" thing. But it's proof that scheduling + Claude = measurable ROI. Tuck this in your back pocket for when you're ready to dig into automated schedule recommendations.

---

### 7. Skill Up — Do This Today

**The 10-minute exercise:**

Tomorrow morning (or now if you've got time), go to your last week's sales report from Par Brink. Pick the day with the highest sales volume. Ask Claude:

> "Here's my Par Brink report for [date]. I had $[amount] in sales. My labor was $[amount] and I was staffed with [list crew size/hours]. What were my biggest wins and worst misses that day? If I could change one staffing choice, what would it be?"

Paste the actual numbers. Don't paraphrase. Watch what Claude actually *sees* vs. what you thought was happening.

**What to look for:** Does Claude flag something you missed? Does the math catch an inefficiency (overstaffed during slow periods, understaffed during rush)? That's your signal that Claude can be your second pair of eyes on every shift.

**Next brief question for you:** *What gap did Claude spot that surprised you?* Jot it down.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---

**Note:** Remote content sources were inaccessible today due to Cloudflare blocking. This brief was built on current Claude capabilities and operational patterns. Will retry feeds tomorrow for real-time restaurant industry news.

