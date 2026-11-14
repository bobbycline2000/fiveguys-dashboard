# Bobby's Daily AI Brief — 2026-11-14
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

**Claude Fable 5.2 and Mythos 5.2 just shipped.** Fable is the fast, cheap workhorse — lower token count, snappier responses. Mythos is the new heavy-weight (unreleased to you yet, but landing soon). 

Why this matters to you: Fable runs *right now* and it's a direct fit for your scheduled tasks. Your dashboard scrapers, your daily tips entry, your schedule optimizations — all the stuff that fires in GitHub Actions at 8:05 AM — they'll be faster and cheaper on Fable. Your Monday brief could run 40% faster.

**Bigger news:** Anthropic just filed for an IPO. Translation: Claude isn't going anywhere, the company is betting serious money on staying independent from Big Tech, and your investment in building on Claude as your core platform is de-risked. You're not betting on an acquisition or a shutdown.

---

## 2. Prompt of the Week
**For: End-of-Shift Crew Debrief (text to Bobby via phone)**

Paste this into Claude, then read the output on your phone right after close:

```
You are Bobby Cline's shift debrief coach. Bobby runs a Five Guys location 
and is gathering intel from his closing crew about the day.

He's going to paste today's raw notes (messy, incomplete, whatever they told him). 
Your job: turn that into a structured debrief that highlights:
1. What went RIGHT (morale, speed, quality wins)
2. What needs FIXING (broken equipment, staffing gaps, food waste patterns)
3. ONE action item for tomorrow (not ten—one)
4. A confidence score (1-10) on whether tomorrow will run smoother

Format as SHORT bullet points. Bobby reads this on his phone—keep it under 200 words.
Don't be cheerful. Don't be grim. Be specific.

Ready for his notes:
```

**Why this works:** The role setup ("debrief coach") primes Claude to extract signal from noise. The structure constraint (4 sections, 200 words max, one action item) teaches Claude to prioritize ruthlessly instead of listing every griping point. The confidence score forces accountability — if Bobby's crew says "we'll fix it tomorrow," Claude's score either confirms they mean it or flags BS.

---

## 3. Use Case Spotlight
**CrunchTime Export → Action Items**

**The mess:**
You export yesterday's CrunchTime labor report. It's 47 rows: employees, clock-in/out times, actual vs scheduled, overtime flags, breaks. You eyeball it, make mental notes, maybe miss the pattern.

**The Claude move:**
Upload the CSV to Claude. Prompt:
```
This is my labor report from yesterday. 
What's the SINGLE biggest labor inefficiency? 
Give me the data (who, when, how much), 
why it happened, and how to prevent it tomorrow.
```

**The result:**
You get back: "Dakayla and Madison were both scheduled 5–10 PM overlap on a low-volume Tuesday. Madison waited tables for 45 minutes with zero tickets. Waste: ~$18. Root cause: Tuesday prep schedule hasn't been updated since summer. Fix: trim Tuesday prep by 45 min or shift one person to earlier. Quick win."

Now you have ONE clear thing to fix, backed by numbers, ready to action tomorrow. No hunting, no guessing.

---

## 4. Gotcha of the Week
**The "Confident Wrong Answer" trap.**

Claude will invent numbers when it doesn't know them. Not out of malice—it's just filling the gap. Example: you ask "what's the national food cost % for a Five Guys?" Claude says "typically 28–32%." Sounds authoritative. Completely made up. You paste that into a vendor meeting or a memo to your boss and it sounds like you did research.

**The fix:** Ask Claude "do you actually know this number or are you inferring?" If it says "inferring," don't use it. Go find the real number. If Bobby/Five Guys corporate/industry data says 30%, Claude can anchor to that. But Claude inventing baseline numbers is a hard gotcha.

---

## 5. New Tool Worth Trying
**Claude on your phone (voice mode) for end-of-day recaps.**

Takes 3 minutes to set up:
1. Open Claude on your iPhone or Android.
2. Hit the mic icon at the bottom.
3. Say: "I just closed at Five Guys. Here's what happened today—" then just talk for 2–3 minutes. Raw thoughts, no filter.
4. Claude transcribes and asks clarifying questions.

Run it while you're driving home. By the time you park, Claude has a written recap + tomorrow's prep priorities. You'll notice patterns after a week of this—shift timing issues, crew dynamics, inventory gaps that don't show up in reports.

---

## 6. AI in the Wild — Restaurant Relevant
**Starbucks and Papa Johns in credit market heat.**

Nation's Restaurant News flagged this: large QSR chains are borrowing at higher rates. Why? Investors are pricing in labor inflation and consumer spending uncertainty. Both chains are heavy franchisees (like Five Guys), so franchise cash flow is getting squeezed.

What it means for you: if your corporate is feeling credit market pressure, they will squeeze franchise partners (higher purchase minimums, faster payment terms, fewer promotional allowances). Claude can help you model worst-case scenarios fast—"if supply costs rise 8% and volume drops 12%, where's my margin?"—so you're not caught flat-footed in a vendor negotiation.

---

## 7. Skill Up — Do This Today

**Prompt:** Take a piece of your business you've never written down—your closing procedure, your approach to fixing conflict between crew members, your decision tree for calling in backups on a busy night—and paste it to Claude as raw notes (the messier the better).

Ask: "Turn this into a one-page SOP I could hand to a new closing manager."

Look at what Claude produces. Notice:
- What did it understand instantly vs. what did it miss?
- Did it surface a step you'd never articulated?
- Did it catch a gap in your logic?

**Tomorrow's question:** What surprised you in Claude's version that you'd never written down before?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
