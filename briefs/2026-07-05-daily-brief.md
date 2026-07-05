# Bobby's Daily AI Brief — 2026-07-05
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude 4.6 (Sonnet) is shipping faster than ever, and the update that lands today is boring in the best way: it's now genuinely usable for back-office automation that previously required you to babysit it. Better understanding of spreadsheet formats (Excel `.xlsx` parsing without copy-paste), more reliable structured output (when you ask Claude to return a specific format, it actually does), and improved handling of PDF extracts from vendor reports. None of this is flashy. All of it saves you time.

The practical play for you: upload a Par Brink PDF, a CrunchTime report, or a supplier invoice into a Claude Project once, and Claude remembers the structure. Next time you paste similar data, it patterns-matches immediately. No re-explaining the format. This is the kind of small edge that compounds into real hours saved per week.

---

## 2. Prompt of the Week

**Vendor Negotiation Email — Copy/Paste Ready**

```
You are a seasoned restaurant ops manager for a Five Guys franchise. 
Direct, professional, no corporate fluff. You negotiate with vendors 
for better rates and terms. Treat this email like you're texting a 
peer — confidence, specificity, no threats, but no begging either.

Write an email to [VENDOR NAME] about [TOPIC: pricing, delivery frequency, 
payment terms, quality issue, product substitution, contract renewal].

Context:
- Our order volume: [amount/frequency, e.g., "2 deliveries/week, $3.5K/order"]
- Current contract terms: [key terms, e.g., "net 30, 2% markup on list"]
- My ask: [specific ask, e.g., "net 45 with volume discount, or move to competitor"]
- Relationship tone: [e.g., "long-standing, solid, but they're getting lazy"]

Keep it to one short paragraph. Lead with the ask, explain the business reason 
(briefly), close with what happens next. No hedging. No "I was hoping." 
Either it's reasonable or it isn't.
```

**Why this works:** The role setup teaches Claude you're a peer negotiator, not a supplicant. The constraint forces him away from corporate templates ("we value our partnership") into actual propositions. The context fields make his output specific instead of generic. You'll send this almost unchanged — which means it's saving you 20 minutes of drafting while sounding like you wrote it. That's the bar.

---

## 3. Use Case Spotlight

**From Chaos to Action: Turning a Voice Memo into a Shift Recap**

You end your shift, click your phone voice recorder, and dump five minutes of stream-of-consciousness: "Lunch was insane, call time was way off, fry station broke down twice, we threw out the second batch of fries, new guy Tyler missed half his shifts, sales were up but labor is killing us, check on why the discount codes aren't working, supplier said he'd call back Tuesday..."

**Before Claude:** You either type it all out (20 minutes) or you forget half of it by tomorrow and nobody knows why yesterday was rough.

**After Claude:** Paste that voice-memo transcript into Claude. Prompt: "Turn this into a shift recap. Pull out: what went wrong, who I need to follow up with, business impact (numbers if I mentioned them), and what I'm checking tomorrow. Format as a bullet list."

Claude returns:

```
SHIFT RECAP — [DATE]

WHAT BROKE
- Fry station: doubled equipment downtime (2x failure) → discarded second batch
- Call-in: Tyler missed ~50% of scheduled shifts
- Discount system: not activating (need to check settings)

BUSINESS IMPACT
- Sales: UP (numbers not specified — check POS)
- Labor: OVER (fry station solo + no Tyler = coverage gap)
- Food waste: 1x full batch fries (restock cost ~$120–180)

FOLLOW-UPS
- Tyler: address attendance pattern (three missed shifts in one week)
- Supplier: callback expected Tuesday re: [topic not specified]
- Tech: troubleshoot discount codes (possible POS config issue)
- Equipment: fry station—schedule service call, interim backup?

PATTERN TO WATCH
Pressure cooker days + new staff absences = quality hits + food waste.
```

You've got a real document to send to your relief manager. No ambiguity. No "I think something happened." This is what ops accountability actually looks like, and Claude can build it from your 5-minute rant.

---

## 4. Gotcha of the Week

**The Confidence Trap: Claude Making Up Numbers**

You ask: "How much should I budget for a new Deep Fryer?"

Claude confidently replies: "Based on industry standards, expect $2,500–$4,500 for a commercial-grade fryer."

Sounds reasonable. You're planning the capex, and it feels backed-up. **It isn't.** Claude guessed. He's never priced a specific model for a specific distributor. He invented a number that *sounds* right based on general patterns.

**The fix — make Claude cite or defer:**

Ask: "What are the three most common commercial Deep Fryer brands used in QSR, and where would I get a real price quote?"

Or better: "Upload this Five Guys equipment supplier contract. What are the fryer models in stock and their listed prices?"

Now Claude is working from reality, not vibes. The moment he's outputting numbers that matter to your P&L, he shouldn't be improvising. Force him to read the spec sheet, the vendor sheet, or the contract. If he doesn't have it, tell him to say so instead of inventing.

---

## 5. New Tool Worth Trying

**Claude Projects + Your CrunchTime Reports**

Here's a 5-minute setup:

1. Go to claude.ai and create a new Project (tap the folder icon, + New).
2. Name it: "2065 CrunchTime Reports"
3. Upload 2–3 of your most recent CrunchTime PDFs (today's, yesterday's, a typical slow day).
4. Write ONE instruction in the project description: "These are daily ops reports for Store 2065. When I paste new data, summarize the variance and flag anything over 10% from target."
5. From now on, paste a new report → Claude remembers the structure and baseline → instant summary.

No re-explaining every time. Takes 5 minutes. Saves 2 minutes per report, every report. That's 10 minutes/week if you're looking at one report per shift.

---

## 6. AI in the Wild — Restaurant Relevant

**Toast just acquired a labor-optimization vendor**, which means Toast's core product (POS + payroll integration) is about to get a scheduling layer that talks to your sales data in real-time. When your lunch rush prediction dips on Tuesday, Toast will recommend pulling a prep shift. This is live in beta with test kitchens now.

**Why Bobby cares:** Five Guys corporate isn't doing this yet. But your district competitor's POS is probably getting smarter while yours isn't. By year-end, most Toast/Square/Toast shops will have this. If you're not building your own version (and you're not — CrunchTime doesn't expose the API), you're at a disadvantage. *Note: Reverse-engineering CrunchTime's labor pull is still on the roadmap and would give you the same edge.*

---

## 7. Skill Up — Do This Today

**Practice: Diagnosis from Chaos**

Here's a real scenario (yours, probably):

1. Go grab any one of yesterday's shift notes — email recap, voice memo transcript, manager handoff, anything chaotic.
2. Paste it into Claude.
3. Type this prompt: "Pull out: (1) What actually happened vs what was supposed to happen, (2) who needs to know about this, (3) is this a one-time blip or a pattern, (4) what do I check tomorrow."
4. Claude returns a structured diagnosis.

Then ask yourself: **Did Claude ask me good questions, or did he assume?** If he invented details, where did he go wrong? If he nailed it, what made the input clear enough?

**Your question for next time:** When you did this exercise, did Claude ask for clarification, or did he guess his way through?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
