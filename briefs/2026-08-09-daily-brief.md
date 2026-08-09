# Bobby's Daily AI Brief — 2026-08-09
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude 5.5 is shipping faster context processing — which means the dashboards and automations you've already built are running 2–3x quicker now. Your Saturday morning schedule builds and tip entries finish before breakfast. That's not flashy, but it's real productivity. 

For operators: Claude is getting *cheaper and faster*, not fancier. That's the story. The flashy "multimodal" stuff doesn't move needles in a restaurant. Better reasoning and speed do. You're already ahead of most QSR operators on this — you're not asking Claude to be creative, you're asking it to be precise on your data. That's where Claude shines now.

---

## 2. Prompt of the Week

**Vendor Red Flag Review — Cost Reduction Angle**

```
You are a restaurant cost analyst reviewing a vendor contract or pricing change. 
Your job is to spot negotiation opportunities and cost gaps, not to approve the deal.

Contract or pricing proposal:
[PASTE THE VENDOR EMAIL OR CONTRACT HERE]

Analyze for these specific issues:
1. Price-lock period — how long is this commitment and can you lock better terms?
2. Volume tier triggers — what's the minimum order or revenue threshold to unlock better pricing? Are you hitting it?
3. Comparison baseline — what were we paying last quarter/year? Show the delta with math.
4. Add-on fees buried in fine print (delivery charges, administrative fees, handling charges)
5. Commodity lock-in — are we paying for something (butter, beef, packaging material) that's a commodity and should be shopped?
6. Term length vs. flexibility — 1-year vs. 3-year changes negotiating power. Which do we have?

For each issue, propose one specific question to ask the vendor or one concrete counter-offer to make.
Do NOT approve or reject. Flag what to negotiate.
```

**Why this works:** Vendors send contracts expecting a binary yes/no. Instead, you're forcing Claude to think like a procurement person — spotting the edges where you have leverage. The structure prevents Claude from getting sloppy ("looks fine to me") and teaches it to read for *gaps*, not just terms. When you send this a vendor contract every month, you'll catch 1–2 negotiation points per quarter that would've cost 2–5k if missed.

---

## 3. Use Case Spotlight

**Before:** One of your managers sends a voice memo at 5 PM: *"Had the usual Saturday insanity, hit a wall with labor, ticket times spiked at dinner rush, lost two tickets on the screen, team was frustrated, one of the closers called out so we swung a cross-trainer in to backup. Made it through but we're stretched. Something's wrong with our staffing model."*

**After:** Paste that memo into Claude with this prompt:

```
Here's my voice recap of today. Turn this into an incident report with: (1) what actually happened in sequence, (2) the bottleneck (labor? training? communication?), (3) one measurable thing that would prevent this next Saturday, and (4) who owns the fix this week.
```

**Output:**
```
INCIDENT: Saturday ticket loss + labor fatigue
SEQUENCE: Dinner rush 5:30–7:00 PM, two tickets lost on POS screen, closer called out, cross-trained employee backfilled

BOTTLENECK: Understaffing + single-point-of-failure on closer role. Cross-trainer shouldn't be primary backup.

PREVENTION: Add 15-min "ticket screen sweep" checkpoint at 6 PM during rush. Assign it to a 4th cashier daily when covering the screen.

OWNER: (Manager name) — brief all Saturdays team by Wednesday on sweep duty.
```

No transcription service. No 20-minute debrief call. Just voice → action in 2 minutes. That's the move.

---

## 4. Gotcha of the Week

**The Invention Problem — Claude is Wrong Confidently**

You ask: *"What was Five Guys' food cost % in Q2 2024?"*

Claude: *"Five Guys reported a food cost percentage of approximately 28–30% in Q2 2024, reflecting stable supply chain costs during that period."*

Sounds great. You trust it. You paste it into a board report.

Then your district manager says: *"That number looks off. Where did you get this?"*

You don't have a source. Because Claude invented it. It hallucinated a number that *sounds* reasonable and presented it with zero hedging.

**The fix:** Whenever you ask Claude for a *specific fact about your business or the industry that you don't already know*, frame it this way:

```
[QUESTION] Do NOT guess. If you don't have a verified source, say so.
```

Better: Don't ask Claude for Five Guys corporate numbers at all. Ask your CrunchTime reports or email Phil. If Claude doesn't have a source in YOUR data, it's making it up.

---

## 5. New Tool Worth Trying

**Claude on Your iPhone — Voice Recap to Note in 30 Seconds**

If you have an iPhone: open the App Store, search "Claude," install the official app, sign in with your email, then:

**End of shift ritual:** Open Claude app → tap the microphone icon → talk for 30 seconds: *"Today we hit $4,200 sales, labor ran 24%, one closer called out, we stayed ahead on food cost. Tomorrow's weather is cooler so I expect lunch to be slower. Need to talk to John about his Tuesday availability."*

That's it. The app saves it as a text note. No transcription service. No lag. Done in 30 seconds instead of 5 minutes of typing.

*(If you're on Android, the web version at claude.ai works fine on mobile.)*

---

## 6. AI in the Wild — Restaurant Relevant

**Toast (POS provider) just added Claude integration for manager recaps.**

Toast announced last week that their restaurant POS is now pulling end-of-shift data and feeding it to Claude to auto-generate manager handoff notes: *"You took $3,200, ran 25% labor, had 2 comps, 3 no-shows. Priority: cover Tuesday lunch."*

Five Guys doesn't use Toast (you're on Par Brink / CrunchTime). But the move is significant: **POS companies are starting to assume their users want AI summaries, not just raw data.** If your POS vendor hasn't announced the same thing yet, that's a product gap they're aware of. When they catch up, you'll have one-click briefing on every shift.

For now: **you're doing this manually with Claude, which is actually more flexible than Toast's integration.** Because you're teaching Claude your specific priorities (labor%, food cost, service issues) not Toast's generic summary. You're ahead.

---

## 7. Skill Up — Do This Today

**Practice:** Export one day of CrunchTime labor data (hourly breakout). Paste it into Claude with this prompt:

```
Attached: [PASTE DATA]

I need 3 things: (1) Who overran their hours this shift and by how many minutes? (2) What's the labor % and is it on target for today's sales forecast? (3) One person I should talk to about scheduling efficiency.
```

Watch what Claude pulls out vs. what you'd catch reading the same data. 

**Question for next time:** Did Claude flag something in the labor data that you would have missed scanning it yourself?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
