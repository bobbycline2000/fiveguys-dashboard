# Bobby's Daily AI Brief — May 13, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude 4.7 (Opus tier) is now available with **extended thinking turned on by default** — Claude pauses to reason through complex problems before answering. For you: when you paste in a messy P&L variance, a labor scheduling jam, or a vendor contract red flag, Claude now spends a few seconds thinking it through instead of pattern-matching the first answer. Results are sharper. The thinking overhead is real (slower by 5–10 seconds), so use it when the problem is actually complicated, not for quick tasks. The bigger news is that **Sonnet 4.6 (the "fast" model) now supports file uploads and web search in Claude projects** — meaning you can finally build a persistent dashboard-monitoring agent that reads your weekly CrunchTime exports *and* searches for news about Five Guys corporate changes, labor law shifts, or your competitors' moves. That's a shipping feature for you, not a developer toy.

---

## 2. Prompt of the Week

**Use this for next Friday's weekly ops review with your DMs:**

```
You are a restaurant operations coach with 20 years in QSR franchise management. 
A general manager is reviewing this week's numbers with you. Your job: surface the 
three things that matter, ignore the noise, and give honest feedback on what to fix.

Frame your response like you're sitting across from them:
- Start with what went WELL (one thing, max one sentence)
- Then the PROBLEM AREA that costs them most money or stress
- Then ONE specific action they can take this week to move the needle
- Close with the question that will make them think

Here's their data:
[PASTE IN: sales, labor %, food cost %, one paragraph about the week's chaos]

Remember: franchise operators are tired. They don't want a report. They want to know 
what to do Monday morning.
```

**Why this works:** The "coach" role makes Claude cut through the jargon and focus on *impact*. The constraint ("one thing went well") stops Claude from fluffing with generic praise. The closing question forces Claude to hand back agency to *you* — it's not a lecture, it's a conversation. This structure mirrors what a real franchise consultant would do, which is why it produces better outputs than a generic "analyze this data" ask.

---

## 3. Use Case Spotlight

**Converting a rambling voice memo into a actionable follow-up email.**

**Before (what you'd normally do):**
Record a voice memo at 10 PM after a rough shift: "So we had this thing with the order system going down at lunch and nobody knew what to do because the backup process is just, I don't know, nobody trained them on it? And then Bri had to step in but she was on register so that was a mess. Also noticed the walk-in cooler temperature was reading high again, probably just the sensor but we should check that. Oh, and do we have enough small cups for the weekend? I should probably send someone to check inventory..."

**After (3 minutes of Claude work):**
Paste the memo into Claude, ask: "Turn this into a task list for my DM Bri — what's urgent, what's a training gap, what's maintenance." Claude outputs:

```
URGENT (handle today):
- Check walk-in cooler sensor — if reading high, it's either sensor calibration or unit failure. 
  Don't wait on this.
- Verify small cups inventory for weekend. (1 hour check)

TRAINING GAP (next week):
- Backup order process during system down. Bri should train the crew on the manual order 
  entry procedure so nobody freezes next time. This is a 30-minute Saturday train-up.

OWNERSHIP:
- Ask Bri to send you a photo of the walk-in temp display tomorrow morning so you know it's 
  checked.
```

You copy this into an email to Bri, send it, and now she knows what to do instead of getting a phone call at 6 AM asking her to "figure out the cooler thing." Real money and stress saved.

---

## 4. Gotcha of the Week

**Claude invents numbers when it doesn't know, and presents them confidently.**

You ask Claude: *"What's the typical food cost percentage for a fast-casual burger operation like Five Guys?"* Claude says: *"Fast-casual burger chains typically operate at 28–32% food cost, with premium operations like Five Guys trending toward 30%."* This sounds reasonable, right? It's also sometimes *completely wrong* depending on your sourcing, location, and current commodity prices.

**The trap:** Claude sounds authoritative, so you write it into a vendor pitch or a budget. Then reality hits and your numbers are off by 5 percentage points.

**The fix:** Anytime Claude gives you a benchmark, market rate, or industry number — ask: *"Where did you get that number, and how old is the data?"* Claude will tell you it's synthesized from training data, which is honest. Then do a *three-source spot check* yourself: ask three people in your network, one Five Guys peer, one industry forum post from this year. Use Claude's number as a starting point, not a fact.

---

## 5. New Tool Worth Trying

**Voice Mode on Claude.com — try it with your end-of-shift rundown.**

Go to Claude.com on your phone, tap the microphone icon in the chat box, and hit record. Talk for 30 seconds about your day: *"We had a crazy lunch rush, register went down for 20 minutes, food got backed up, staff handled it okay but it was messy. Labor was a bit high today. Also the ice maker is making that noise again."*

Stop recording. Claude transcribes and responds out loud with a summary and next steps. Takes 90 seconds total. The feature lives in Claude.com today, no subscription required, works offline after the first load.

**Why try it:** At the end of a 12-hour shift, typing is friction. Voice is how you actually think. Doing a quick debrief with Claude via voice takes the same brain space as thinking out loud to yourself — which you're already doing — but you get a structured output you can send to your team.

---

## 6. AI in the Wild — Restaurant Relevant

**Chipotle is rolling out ordering kiosks with AI-powered menu optimization.** The kiosks watch what customers order, what gets wasted, and what combinations are slow to prepare — then the algorithm surfaces different combos and portion sizes to each region. No servers pushing items. Just: *"Customers in Denver are ordering extra guac but skipping queso. Suggest queso combo on this kiosk for the next 3 weeks."* This is not gimmick AI. It's margin AI. A 2–3% uptick in per-ticket average if the algorithm is right. Five Guys isn't doing this yet (as far as public reporting goes), but it's a signal that automation is moving past "food prep" into "what we sell and how we present it."

---

## 7. Skill Up — Do This Today

**Prompt:** Paste this into Claude right now and do it once:

```
I'm going to give you a vendor email. Read it like a contract lawyer would, not like 
a tired GM would. Flag:
- What commitment am I making?
- What's the price and when does it change?
- What happens if I want to cancel?
- Is there anything hidden in the legal boilerplate that surprised you?

Then tell me in one paragraph: should I sign this, or negotiate first?

[PASTE A RECENT VENDOR EMAIL HERE]
```

**What to notice:** Watch how Claude's tone shifts when you ask it to read like a lawyer instead of like a general. It catches things you'd miss in a tired 6 PM scan of your inbox. The "should I sign or negotiate" question at the end forces a decision, not a summary.

**Your question for next time:** After Claude flags the red flags in a vendor contract, which one surprised you most? (This trains you to spot that pattern yourself next time.)

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
