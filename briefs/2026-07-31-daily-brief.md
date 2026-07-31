# Bobby's Daily AI Brief — 2026-07-31
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

**The thing you should care about:** Claude Projects now supports real-time data connectors. This means your Claude chat can pull live data from connected sources—CrunchTime feeds, your safe drawer log, schedule updates—without manually pasting. The piece you need: if you wire a JSON feed from your dashboard repo into a Project, Claude sees fresh data every conversation. No copy-paste, no stale exports.

**Why it matters for you:** Your dashboard is read-only. But a Claude Project + live feed means you can ask questions against *today's* data in plain language. "Show me who punched in late this week" doesn't require you to open CrunchTime or parse a spreadsheet anymore. The bot becomes a live advisor, not a report generator.

**Reality check:** It's still early. The connector setup takes 20 minutes. But this is the bridge between "Claude reads my data" and "Claude advises on my data."

---

## 2. Prompt of the Week

**Coaching Conversation Prep — Paste this directly:**

```
You are a restaurant operations coach. I'm about to have a 1-on-1 conversation with [EMPLOYEE NAME], our [ROLE], who [SPECIFIC SITUATION: e.g., "has been late 3x this month" or "just started and is still ramping" or "scored low on the last inventory"].

Context:
- Their history: [2-3 sentences about what you know about them]
- What I want to accomplish: [the actual goal—don't be vague]
- What I don't want to do: [what NOT to do in this conversation—often more important]

Generate a 5-minute conversation outline. Format it as:
1. Opening (don't jump to the issue—build context)
2. Listen first (the actual question to ask them)
3. If they say X... (anticipate one objection/response and your move)
4. The ask (what you want them to do differently)
5. Close (how to end on their commitment, not your frustration)

Make it sound like me. No corporate HR language. Make it coachable, not punitive.
```

**Why this works:** Most coaching conversations fail because managers jump to the problem statement. This prompt forces you to open with curiosity, not accusation. The "If they say X" section preps you for pushback—so you're not caught flat-footed. And that close matters: people follow through on *their* commitments, not your orders. This prompt structure teaches you to end on theirs.

---

## 3. Use Case Spotlight

**Email Drafting for Vendor Negotiations**

**The problem:** You get an email from your Par Brink rep asking about switching you to their new cloud-based reporting. You're skeptical. The email is friendly but salesy. You want to ask smart questions without being rude or sounding lost.

**Raw input to Claude:**
```
I got this email [paste vendor email]. We're not ready to switch systems. 
What questions should I ask them that sound smart but actually buy us time 
and smoke out whether this is a real upgrade or just a migration tax?
```

**What Claude returns:**
- 4-5 specific, technical-sounding questions about their data retention policy, audit trails, API stability, and rollback plan
- Each question has a one-liner on WHY you're asking it (the subtext)
- A response template that says "thanks for the context, we're evaluating in Q4" (buys you actual runway)

**Why it works:** Vendors respect operators who ask questions. And these aren't adversarial—they're the questions any smart buyer asks. Claude helps you sound sharper than you feel in the moment. Five Guys' corporate is always shipping new tools. This prompt pattern scales to every vendor pitch.

---

## 4. Gotcha of the Week

**The Confident Hallucination**

You ask Claude: "What's the average food cost percentage for a Five Guys across the US?"

Claude answers: "5-year industry average is 28-31% for QSR chains, Five Guys typically sits 29-30%."

It sounds right. It's cited. You copy it into a plan.

**The trap:** Claude invented those numbers. It didn't look them up. It generated plausible-sounding data because your question asked for a number and numbers are what confident assistants provide.

**The fix:** Any time Claude gives you a specific number about your industry (labor %, food cost %, turnover rate, industry benchmark)—stop and ask: "Where did you get that number? Can you show me the source?" If Claude can't cite a specific report or data source you can verify, it's a guess wearing a suit.

**For you specifically:** Never use Claude numbers to justify a business decision to your DM or to Bobby Davis. Pull actual numbers from CrunchTime, from Five Guys corporate reports, or from public sources you can name. Claude is a thinking partner, not a data source.

---

## 5. New Tool Worth Trying

**Claude on iPhone (voice mode)**

**What it is:** You can now voice-chat with Claude on your phone like you'd text a colleague. No typing.

**Why this matters for you:** End-of-shift recap. You're tired. You walk out at close. You tap the mic and say: "Rough night. We had a walkout on the line, the delivery order system went down twice, and labor went over budget. Give me three things I should email to Bobby Davis first thing tomorrow."

Claude handles it. You drive home. Tomorrow you send the email.

**How to try it (legit 5 minutes):**
1. Open Claude app on your iPhone (or go to claude.ai if you use web)
2. Tap the mic icon (bottom-right, looks like a microphone)
3. Say: "I want to test voice mode. Just reply back what you heard."
4. Listen. It works.
5. On your next session, try a real task: "Draft a schedule change request for [person]."

**The gotcha:** Voice mode works best when you're specific. "Fix my schedule" gets a vague answer. "I need to move Dakayla from Wednesday night to Thursday lunch because she's covering a different store" gets a real email draft.

---

## 6. AI in the Wild — Restaurant Relevant

**Toast's new AI order routing is eating market share from competitors.** 

Toast announced in June that their platform now auto-routes incoming orders (DoorDash, Uber, in-house) to the fastest available station based on real-time prep times and kitchen load. Five Guys corporate hasn't announced anything similar, but your POS (Par Brink) is watching.

**What this means for you:** Your job as manager is about to shift from "direct labor to each station" to "did the system route the order correctly?" The AI does the directing. You audit the AI.

**Why you care:** If Five Guys rolls out order-intelligent routing in the next 12–18 months, your labor model changes. You can't hire slower prep people anymore—the AI exposes inefficiency. But you CAN run leaner. This is the actual future Bobby Davis is probably watching.

**Action:** Next time you talk to the DM or Bobby, ask: "Has Five Guys corporate said anything about AI order routing?" Not because you're worried. Because you want credit for thinking ahead.

---

## 7. Skill Up — Do This Today

**Create a shift recap template in Claude Projects.**

**Exact task:**
1. Open Claude (claude.ai or app)
2. Click "Create a Project"
3. Name it: "Daily Shift Recap — 2065"
4. In the instructions, paste this:

```
I'm Bobby, store manager at Five Guys location 2065 in Louisville. Every night, 
I'm going to recap the shift. You're going to organize it into a 3-minute read 
that the DM can scan first thing in the morning.

Format my recap as:
- HEADLINE (one sentence summary: "Solid night, labor tight, one equipment flag")
- METRICS (what happened: labor%, food cost%, sales vs forecast, transactions)
- PEOPLE (staffing, training flags, discipline items)
- OPERATIONAL (what broke, what worked, inventory notes)
- TOMORROW (one thing to watch for tomorrow)

Ask me questions to fill gaps. Be concise.
```

5. Save it.
6. Tomorrow at close, open that Project and say: "Recap today."

**The question to answer:** What surprised you most when Claude organized your recap differently than you would have?

*(Note: This gets you thinking about how Claude structures information. That skill—clarity through structure—is what separates a good operator from a great one.)*

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---
