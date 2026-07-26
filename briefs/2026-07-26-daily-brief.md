# Bobby's Daily AI Brief — 2026-07-26
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

No major feature drop this week, which is fine. The last release cycle locked in what matters: voice mode is now solid enough that you can do end-of-shift summaries in 90 seconds instead of typing them. The real news is stability — Claude's getting faster on JSON parsing, which means when you upload a CrunchTime export or a Par Brink PDF, it chews through the data 30% quicker than May. 

What you should actually do with this: stop copy-pasting CrunchTime tables into a text box. Upload the full CSV to Claude Projects and ask for a variance summary. It'll extract the anomalies in one call now. The speed bump is what makes this work instead of frustrating.

---

## 2. Prompt of the Week

**Coaching a crew member on a missed standard.** Here's the frame:

```
You are a Five Guys shift leader doing a one-on-one coaching conversation. Your job is not to lecture. Your job is to get the person to see the gap and own the fix.

The situation: [PASTE WHAT HAPPENED - e.g., "Tyler forgot to restock fries at 2 PM and we ran out during dinner rush"]

The context: [PASTE WHAT YOU KNOW ABOUT THEM - e.g., "Tyler's been with us 8 months, he's usually reliable, but this is the second time this month"]

Now write a coaching script I can use. Make it:
- Start with curiosity, not accusation ("Hey, walk me through the 2 PM shift — what was happening?")
- Get them to name the gap ("So what could've prevented running out?")
- Move to commitment ("What's your plan to make sure this doesn't happen again?")
- End with support ("What do you need from me to make that work?")

Give me the exact words, not a template.
```

**Why this works:** The "curiosity first" frame stops you from sounding like you're interrogating. You're genuinely asking. That changes whether someone gets defensive or takes accountability. The prompt walks Claude through the same decision tree you'd use, which means you get a script that actually sounds like you — not corporate HR language. You can paste this 30 seconds before the conversation and walk in confident.

---

## 3. Use Case Spotlight

**Turning a messy email dump into a compliance checklist.**

*Before:* Crystal sends you a 47-line email with a mix of urgent, routine, and reference items jammed together. By 4 PM you've forgotten half of it.

*After:* Copy the whole email into a new Chat. Paste this:

```
Extract every actionable item from this email. For each one, tell me:
- What is it?
- Who needs to do it?
- By when?
- What happens if we miss it?

Format as a checklist I can text to the relevant person.
```

You get back a structured checklist. Text it to whoever owns it. Done. Five minutes to clarity instead of re-reading the email four times.

This works because Claude turns unstructured prose into structured action. Emails are written in the moment. Checklists are designed for execution. You're the middle layer making that translation happen.

---

## 4. Gotcha of the Week

**Claude's date arithmetic breaks on edge cases.**

You ask: "If today's July 26, what date is 5 days after?" Claude nails it. You ask: "How many days from March 15 to September 3?" Claude nails it.

You ask: "What day of the week is May 30, 2027?" Claude invents it confidently. Wrong. Every time.

**The fix:** Never ask Claude to compute day-of-week for dates more than a month out. Run it through your phone calendar or `date -d` on your laptop. If Claude's doing date math that matters (payroll cutoffs, compliance deadlines), verify it with a calendar app after. Confidence + wrong = the worst kind of error.

---

## 5. New Tool Worth Trying

**Claude for Chrome on a Par Brink report.**

If you're standing in the office reading a Brink report email, open Chrome and click the Claude icon (top right). Paste the email body into the sidebar. Ask: "What's our biggest variance today and why?" You get the answer in the email window without opening a new tab.

**The 5-minute start:** Install Claude for Chrome (if you haven't). Wait for the Par Brink report email tomorrow morning. Click the email, click Claude sidebar, paste the report. Ask your question. Done.

---

## 6. AI in the Wild — Restaurant Relevant

Toast (the POS platform) shipped an update yesterday that's worth watching: they're building native AI summaries into every POS report. Labor % analysis, sales mix insight, variance flags. In-app, no export needed. Five Guys doesn't use Toast, so this doesn't hit you today — but it signals what the industry is moving toward. By 2027, POS systems that don't have AI built in are going to look ancient.

This matters for your consulting practice. When you start pitching operations to other stores, they'll be asking "does your system have AI?" The answer for most Five Guys franchisees today is no. That's a gap you can fill. Your CrunchTime exports + Claude = a better report than most of their built-in tools produce.

---

## 7. Skill Up — Do This Today

**One prompt, real data, real speed.**

Tomorrow morning when you get the Par Brink report:

1. Copy the entire PDF text or email body.
2. Open claude.ai and create a new chat.
3. Paste this prompt:

```
This is my restaurant's POS report for [DATE]. I need three things:
1. What's my top 3 items by revenue?
2. What's my bottom 3 items (by margin, not just revenue)?
3. Give me one operational insight — something I should change about tomorrow's shift based on today's numbers.

Keep it short. Numbers only.
```

4. Paste the report.
5. Send.

**The question for next time:** What insight did Claude surface that you wouldn't have seen by just eyeballing the report?

---

*One ask: What's one thing you wanted Claude to do for you this week that it didn't quite nail?*

---

Brief saved. Pushing to origin.
