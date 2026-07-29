# Bobby's Daily AI Brief — July 29, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

**Voice mode is now live on mobile and desktop.** If you've been narrating shift problems into your phone and wishing Claude could just listen, this is it. Talk to Claude like you're texting a friend. No typing. No interface. Just dump the problem — "we're bleeding on food cost this week, labor is up 2 points, tell me what to cut" — and Claude talks back. Works offline on devices; syncs to your projects when you reconnect.

Why it matters: You don't have time to sit down and type. Your brain is in operator-mode 60 hours a week. Voice mode closes the gap between "I should ask Claude about this" and "Claude is actually listening." The real constraint for most operators isn't what Claude can do — it's friction. This removes friction.

**Claude Projects now support custom instructions at the project level.** This is the sleeper feature. You can set up a Five Guys Finance Project that auto-applies your store's cost structure, your P&L layout, your KPIs every single time you ask a question. No copy-pasting "our food cost is typically 28–32%." Claude just knows. Set it once, ask a thousand questions from the same baseline.

---

## 2. Prompt of the Week

**Disciplinary Conversation Prep** — Use this before any hard conversation with a crew member.

```
You are a Five Guys general manager preparing for a performance conversation with a crew member named [NAME]. 

Your goal: Document the issue clearly, deliver feedback that lands, and keep the relationship intact.

The situation: [DESCRIBE THE ISSUE — be specific: what happened, when, impact]
Previous conversations: [WHAT YOU'VE ALREADY TOLD THEM, IF ANYTHING]
Context you want considered: [ANY MITIGATING CIRCUMSTANCES YOU KNOW ABOUT]

Generate:
1. A one-sentence summary of the core issue (what you're really addressing)
2. Two concrete examples of when this behavior showed up (dates/times/impact)
3. What you need from them going forward (specific, measurable)
4. Three things NOT to say (traps that blow up the conversation)
5. Your opening line — the first 30 seconds (plain English, direct, respectful)
6. How to end it (what should they leave knowing)
```

**Why this works:** The structure forces you to separate the emotion from the facts. Most hard conversations fail because the manager is still angry or defensive — you lead with frustration instead of clarity. This prompt makes Claude the third voice in the room: neutral, logical, grounded in examples. You get the conversation script BEFORE you're heated. You can read it, adjust it, own it. Then you walk in calm. That's the difference between a conversation that sticks and a conversation the crew member forgets by Thursday.

---

## 3. Use Case Spotlight

**Turning a CrunchTime P&L export into a one-page action plan.**

**The messy input:** You download last week's P&L from CrunchTime. It's 40 rows. Sales are down 3%. COGS is up 1.5 points. Labor is flat but food cost is creeping. You stare at it. You know something's wrong but you don't know what to *do*.

**What Claude does:** Upload the PDF or paste the export. Ask: *"Rank these variances by what I can actually fix this week. Tell me: (1) the one thing that if I fix it moves the needle, (2) three tactical moves in the next 72 hours, (3) what to watch for."*

Claude reads the numbers, knows your baseline (if you've told it), and gives you a prioritized play. Not "food cost is high" — that's obvious. But *"your entree yield is 2% below standard; if you tighten portion control on 1/4-pounders and 1/3-pounders for three days you recover $200 of the week."*

Then you walk that into your crew with a one-liner: *"We're gonna dial in portions on the premium burgers — here's why, here's how for three days, thanks."* Crew sees you read the numbers. Crew knows what to do. Problem tightens.

**Real output:** From a fuzzy "something's off" to a named problem and a 72-hour fix in under 2 minutes.

---

## 4. Gotcha of the Week

**Claude invents numbers and delivers them with confidence.**

This happened to another operator last week. He asked Claude for "typical QSR labor % for a location like mine." Claude said "most quick-service franchises run 24–26% labor." Sounded reasonable. He used it to set targets. Found out later it's actually 28–32% for Five Guys, and his targets were killing his team.

**The trap:** Claude doesn't know your business. It reads patterns from its training data and fills in gaps. When you ask it to estimate, it estimates well-presented. It doesn't tell you it's guessing.

**The fix:** Every number that matters — cost basis, labor targets, sales benchmarks, food cost — must come from YOUR data or Five Guys published benchmarks. When Claude gives you a number, assume it's informed intuition, not fact. Verify before you act on it.

---

## 5. New Tool Worth Trying

**Upload a Photo of Your Menu to Claude and Ask It Questions.**

You've probably got a printed menu sitting on your desk right now. Take a photo with your phone. Open Claude on your phone (it's free). Hit the paperclip. Upload the photo. Ask: *"If I wanted to test a price increase on the cheese burger, what would be the best framing and what price point makes sense?"*

Claude sees your menu, reads the current pricing structure, and gives you an answer rooted in what you actually offer — not generic menu-pricing theory.

**Time to try:** Two minutes. Literally take a photo, upload, ask. That's it.

---

## 6. AI in the Wild — Restaurant Relevant

**Olo announced integration with ordering platforms for AI-assisted upsells.** The real story: Toast, Square, and R365 are all racing to bolt AI onto their POS systems so the system suggests — not you — what a customer might want when they order. "You ordered a burger, fries, drink — add a shake for $4?" The AI learns what works at your location.

Why you should notice: This is the next battleground. If another Five Guys in Louisville starts using this and lifts ticket average 8–12%, the franchisor notices. You don't have to implement it tomorrow, but if you're running a location competing on velocity and margin, watching how other operators use AI at the point of order is smart. It's coming to POS systems everywhere in the next year.

---

## 7. Skill Up — Do This Today

**Capture a voice memo of your end-of-shift thoughts and turn it into a written action item list.**

Here's the exercise:

1. Open Claude on your phone. Hit the voice button.
2. Spend 90 seconds talking about the shift: *"Lunch was slammed, drive was down, we had two call-outs, kitchen was lagging on burgers by 4 minutes, inventory showed we're low on brioche, couple of crew were dragging by 4 PM, one customer complaint about cold fries."*
3. Stop. Ask Claude: *"Turn that into a bulleted action list for tomorrow — what needs to happen, who should own it, what I need to address."*

Look at what Claude gives you. Notice how it extracted the signal from the ramble. Tomorrow, when you're standing in front of the crew, you've already organized the shift debrief in your head.

**What to notice:** Did Claude surface something you glossed over? Did it reframe an issue in a useful way? That's the real skill — teaching Claude to listen like a GM who's been in the business 20 years.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
