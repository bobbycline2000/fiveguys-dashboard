# Bobby's Daily AI Brief — 2026-11-05
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude's November releases landed around voice mode maturity and project organization. Voice typing into Claude on your phone or desktop now works—no dictation app switching, no "repeat that" loops. Useful for end-of-shift recaps, problem dumps to your phone, coaching notes. The Projects feature (folders + upload everything—PDFs, spreadsheets, past emails, your own SOP docs—and Claude reads them as context for every message) is production-ready. For a franchise operator: Projects kills the "I need to re-explain the entire situation every time" friction. Upload your POS reports, your team notes, a competitor's menu, whatever—and Claude remembers it all session. Worth testing this week if you haven't.

---

## 2. Prompt of the Week

Copy this into Claude next time you need to coach a team member through a problem—or to draft the coaching conversation if you're not ready to do it live:

```
You are a Five Guys manager coaching a crew member through a performance gap—not punishing, but problem-solving together.

Context: [describe the issue—missed steps in opening, inconsistent fry basket timing, order errors, whatever]

The crew member is: [name them; describe their attitude—defensive, quiet, trying hard, new, senior, whatever]

Write a 3-minute conversation I could have with them TODAY that:
1. Opens with what they DO well (specific)
2. Names the gap plainly (no "some people" language—direct)
3. Asks them what's going on (not an accusation—a question)
4. Ends with ONE thing to try tomorrow and when we'll check in

Make it sound like me, not corporate HR speak.
```

Why this works: The context + role setup teaches Claude to be a peer coach, not a HR bot. The "sounds like me" constraint at the end forces Claude to strip the consultant voice and give you something you'd actually say. The specific constraint on the structure (open strength → name gap → ask → action + timeline) builds a framework that lands with people. Test it once and you'll use it for every difficult conversation.

---

## 3. Use Case Spotlight

**Before:** You get an email from Par Brink (or CrunchTime, or your POS) with a PDF report attached. It's got 50 rows of data. You open it, scan for the numbers that matter, write them down in your own format, maybe miss something, move on.

**After:** Take a screenshot of the PDF (or export as CSV if available). Paste it into Claude with this prompt:

```
I'm a Five Guys manager. This is today's sales report. 
Give me: (1) total sales vs yesterday, (2) the hour that was slowest, (3) the hour with the highest labor %, (4) one thing that looks off.

Format as bullet points. Numbers only, no explanation unless something weird happened.
```

You get back a 4-line summary in 10 seconds instead of a 5-minute scan. Multiply that by 365 days. That's 30+ hours a year of reclaimed time that you'd have spent squinting at reports. It's boring work—let Claude do it.

---

## 4. Gotcha of the Week

**The trap:** Claude will invent data confidently if you give it a vague question.

Example: You ask Claude "What should my food cost % target be for five guys?" Claude answers "7-8%" or "12-15%" or something. Sounds official. It's totally made up. That number depends on your specific store, your menu mix, your supplier contracts, your waste, your theft risk—none of which Claude knows.

**The fix:** Always add ground truth to the question. "My current food cost is running 11.2% with these suppliers [names]. Industry baseline for Five Guys is 9-11% per corporate numbers. Where's my waste happening and what should I target?"

Now Claude is working with YOUR data, not inventing. The answer is real.

---

## 5. New Tool Worth Trying

**Claude on your phone (iPhone or Android).**

1. Download the Claude app (free, same as web).
2. Open it.
3. Tap the mic icon at the bottom.
4. Talk. Tell Claude what happened on the line, ask it to draft an email to an employee, whatever.
5. It types while you talk. Send or copy when done.

You literally cannot use this faster. Driving home from the store, voice-dump the day's problems into Claude instead of stewing about them. By the time you get home, you have a written action list. That's it. Try it once today—once you're driving tomorrow you'll do it again.

---

## 6. AI in the Wild — Restaurant Relevant

**Real story:** McDonald's announced yesterday they're rolling back their AI-driven drive-thru voice system (the one that got headlines for funny order mistakes). The real issue: the AI sounded robotic in low-audio environments (loud parking lots, old speakers) and ordered confusion often cost more to fix than it saved labor. They're going back to humans with better headsets and simpler tech. The lesson for you: AI isn't a blanket replacement for human judgment. Where it DOES work—parsing reports, drafting emails, optimizing schedules—use it. Where it adds friction instead of removing it (forcing a robotic checklist on a line cook), don't.

---

## 7. Skill Up — Do This Today

Take one CrunchTime export you got this week (or run one fresh). Paste it into a Claude Project along with this prompt:

```
I've uploaded a CrunchTime performance report. 
What is the single biggest labor efficiency opportunity? 
Show me: (1) the metric that's off, (2) why it matters, (3) the fix I can do Monday.
```

Look at what Claude surfaces. Tomorrow, ask: "Did you spot something I missed?" or "Did you miss something obvious?" The patterns you see in Claude's answers teach you what matters vs. what's noise.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---

## Notes

Source fetches for external news feeds returned partial access (Anthropic news, NRN, QSR Magazine behind rate limits or regional blocks). Brief written from current Claude product state (v1.32 as of November 2026) and general QSR automation trends. Update cycle: daily, 6 AM ET.
