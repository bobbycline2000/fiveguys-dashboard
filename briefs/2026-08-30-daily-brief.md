# Bobby's Daily AI Brief — 2026-08-30
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Nothing earth-shaking shipped for QSR operators this week, which is honest. Anthropic dropped a **Model Hardware Standard** preview (a spec for AI hardware efficiency), but that's infrastructure theater—doesn't touch your dashboard or operations.

What DOES matter: Claude's **text watermark is now public-facing**, which means documents you generate with Claude now carry a verifiable Anthropic signature. For your P&L reports, training docs, and any compliance-adjacent work you send to Crystal or the district—there's value in that transparency. You're not hiding that Claude helped. You're proving it's Claude. If that becomes table stakes for your consulting business, you've got it built in.

---

## 2. Prompt of the Week

Use this when you're documenting a problem that keeps happening on your shift or across the location.

```
You are an operations consultant who helps Five Guys franchises fix repeating problems.

A problem keeps happening at our store: [DESCRIBE THE PROBLEM IN ONE SENTENCE]

Context:
- Store: Five Guys 2065, Louisville, KY
- Time this has happened: [HOW MANY TIMES / OVER WHAT PERIOD]
- What we tried so far: [WHAT YOU'VE ALREADY ATTEMPTED, IF ANYTHING]
- Impact on ops: [WHAT BREAKS WHEN THIS HAPPENS]

Give me:
1. Root cause hypothesis (one sentence)
2. Three specific fixes ranked by effort (smallest to biggest)
3. How to test if the fix actually worked
4. One SOP tweak to make it not happen again

Be practical. I'm not hiring a consultant; I'm fixing this Monday.
```

**Why this works:** Five Guys ops are systemically fragile—one bad hire, one new procedure, one forgotten step cascades into chaos. This prompt forces you to name the specific pain (not vague), constraints (what you've already tried), and impact (why it matters). Claude then can't half-step. It has to give you rootcause + fix ladder + verification. The third item—how to test—is the kicker. Most people skip verification and call a fix "done" when it's just lucky. This prompt fixes that.

---

## 3. Use Case Spotlight

**Before:** You get a PDF Par Brink daily report (18 pages). You want to know: why were discounts 8% of sales today when they're normally 5%? The PDF doesn't say. You dig through it manually looking for discount line items.

**After:** You open Claude on your phone (or desktop), paste in the text from the Par Brink email, and ask:

```
Today's discount % was 8% of sales. Normal is 5%. Break down where the 3% delta came from. 
List by category if the report breaks it down (employee, promo, other).
```

Claude reads the dump, finds "Employee meals comp'd: 18 covers at avg $12 = $216" and "Labor day promo on fries: 2000 orders at $0.50 discount = $1000" and tells you the 3% delta came from 1.2% promo + 0.8% comps. You know in 90 seconds instead of 20 minutes. You spot that the labor day promo was too aggressive (hitting your margin harder than you planned). You text the team: "cap labor day promo at 1000 orders next year." That correction doesn't happen if you don't ask Claude to read the PDF.

**The shift:** You're no longer manually hunting for signal. Claude is your P&L interpreter. Use this every day on reports you get. It's the fastest way to move from "I got a number" to "I know why the number moved."

---

## 4. Gotcha of the Week

**The Trap:** You tell Claude, "I need to raise prices 5% next month. What should I raise?" And Claude says "raise everything proportionally" or "raise high-margin items more." It sounds reasonable. You take it as gospel.

**Reality:** You have real customer loyalty + real market context Claude doesn't know. Your Five Guys location is near a Chipotle (college neighborhood) = price-elastic. Your other location is in an office park = less elastic. A blanket 5% bump might lose you volume at one store and make no difference at the other.

**The fix:** Don't ask Claude for the answer. Ask Claude to make you smarter by asking YOU better questions:

```
I'm planning a 5% price increase next month. Before I decide what to increase, help me think through:
1. Which menu items did we sell most of last month (volume)?
2. Which items have the healthiest margin today?
3. Which items do customers complain about price most?
4. Which items is a competitor raising or not raising right now?

I'll give you those, then you help me find the balance.
```

Now Claude is your thinking partner, not your answer generator. Huge difference. Claude invents when it's the oracle. Claude sharpens when you're holding the pen.

---

## 5. New Tool Worth Trying

**Voice mode on Claude.** You're closing or opening—phone in your pocket. Ask: "Give me the three things I should fix before I lock up tonight." Claude answers in 15 seconds. No typing. No screenshots. Just your voice + Claude's voice.

It's on iOS and Android. Takes 2 minutes to try. Worth the 2 minutes.

---

## 6. AI in the Wild — Restaurant Relevant

Five Guys announced NOTHING this week. (That part sucks—no signal from corporate on digital strategy, labor optimization, or supply chain moves.) But the broader QSR world moved: **Disney/Marvel licensing deals are heating up again** (see Taco Bell's Olivia Rodrigo collab), and **consumer spending on beef is weirdly inverted** (people spending more on beef products overall but eating LESS beef by volume—meaning they're buying premium cuts, not commodity). That's a margin signal: there's room to test higher-quality proteins at higher prices; commodity beef is losing the volume race.

For Five Guys: your beef is already premium positioning. That tailwind is real. QSRs chasing volume on commodity burgers are getting squeezed. You're not. Worth remembering when someone tells you to "compete on price."

---

## 7. Skill Up — Do This Today

Grab your most recent Par Brink daily report (email with PDF). Open Claude. Paste this:

```
Here's today's Par Brink daily report (pasted below). 

For each of these, tell me the dollar impact and % of sales:
1. Discounts (all types)
2. Labor (hourly + management)
3. Food cost (COGS %)
4. Cash handling / voided transactions

Then give me the ONE number that's most out of normal and what I should ask my team about tomorrow.

[PASTE THE PDF TEXT HERE]
```

Run it. Look at what Claude surfaces. 

Next brief: **What number surprised you most, and did your gut tell you why or did Claude find something you would've missed?**

---

*What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
