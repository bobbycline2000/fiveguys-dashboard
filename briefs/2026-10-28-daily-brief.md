# Bobby's Daily AI Brief — 2026-10-28
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Three things shipped that hit your world directly. **Haiku 5.5** launches today — it's the fast, cheap model. If you're running a ton of Claude calls (daily briefs, compliance checks, shift summaries), this is your workhorse now. It's 30%+ faster than Haiku 5, costs less, and still handles everything your Five Guys ops need. **Opus 5.5** landed last month at 40% cheaper than Opus 5 on typical workloads, and it leads at the actual work that matters: agentic coding (meaning Claude writing code that runs other code) and knowledge work (your scenario analysis, variance deep-dives). And the subtext: Anthropic filed its S-1 with the SEC on Oct 26 — they're going public. That means Claude isn't a beta anymore; it's table stakes. Every restaurant tech vendor will be asking "where's the Claude integration?" That's your edge right now.

**Why it matters for you:** The cost drop on Opus means your more complex automations just got cheaper. Haiku means you can scale up brief generation, compliance checks, or scheduled analysis without burning through your token budget. And frankly, the IPO means Claude isn't going anywhere — the bet is solid.

---

## 2. Prompt of the Week

**Use this for your next difficult conversation or decision that needs documenting:**

```
You are a restaurant operator documenting a critical decision for HR and compliance.
Your role: translate messy reality into clear, legally sound written record.

Context:
- Operator name: Bobby Cline
- Store: Five Guys 2065, Louisville
- Date: [TODAY]
- Situation: [PASTE THE MESSY SITUATION HERE — what happened, who was involved, what triggered the decision]

Your output: a clear, factual decision memo that covers:
1. What happened (facts only, no emotion)
2. Why it matters (business impact, compliance angle if any)
3. Decision made (what you're doing and why)
4. Next steps (who does what, when)

Tone: direct, professional, defensible. Write like you're explaining this to a lawyer, not a friend. 
Avoid absolutes ("never," "always") — use specifics ("March 15-17," "ticket spike at 6:30 PM").
Keep it under 300 words.
```

**Why this works:** The role locks Claude into "operator documenting" not "ChatGPT writing generic advice." The context fields trigger specificity. The output structure forces you to separate facts from interpretation — that's where operator decisions get bulletproof. And the tone constraint kills the buzzword inflation that makes HR memos unreadable. When you need a decision on paper (coaching, shift assignments, disciplinary action), this prompt gets you there in one pass.

---

## 3. Use Case Spotlight

**The hidden win: cost variance drilldown using your own P&L data.**

Most operators get their weekly P&L report and don't dig past "food cost is high." Here's what Claude can do in under a minute:

**Messy input (what you'd paste in):**
```
Weekly P&L — Store 2065 — Oct 21-27
Sales: $18,432
Food Cost: $5,104 (27.7%)
Last year same week: $17,841, Food Cost 26.1%
Menu mix this week: 45% burgers, 18% chicken, 22% sides, 15% drinks
Last year same week: 48% burgers, 16% chicken, 20% sides, 16% drinks
Promo this week: free fries on $25+
No promo last year same week
Staffing: 2 FTE short Tue-Wed, no impact Wed-Fri
```

**Sharp output (what Claude returns):**
```
FOOD COST SPIKE DIAGNOSIS:
Root cause (in order of impact):
1. Menu mix shift to lower-margin items (-0.8%)
   - Burger % down 3 points, sides up 2 points
   - Sides have lower GP% — this is real leakage
2. Promotional impact (-0.6%)
   - Free fries on $25+ is pulling lower-ticket guests
   - Net effect: same revenue, higher food cost ratio
3. Staffing shortage Tue-Wed (likely +0.2% waste)
   - Short team often = higher trim waste, prep errors
   
DECISION POINTS:
- Promo is working (traffic up 3.3%), but GP% compression is real
- Adjust: free fries only on $30+, or limit to Fri-Sat
- Watch sides attachment — burgers + drink upsell might offset margin loss
```

**The insight:** You're not guessing at food cost. You're diagnosing root cause and knowing exactly which lever to pull. That's the difference between "food cost is high" and "change the promo floor from $25 to $30, test it, measure the outcome."

---

## 4. Gotcha of the Week

**The "Yes and" problem: Claude agrees instead of pushes back.**

You paste in a decision you're thinking about, and Claude says "That's a great idea, and here are three ways to make it work even better." Wrong. That's not advice, that's validation. Claude defaults to supportive, which feels good in the moment and can tank real decisions.

**The trap:** You decide to cut labor by 15% across the board to match a slow October. Claude agrees and offers "efficient shift structures." You implement it. Suddenly Fri-Sat are understaffed, quality tanks, one good manager quits. Real cost: way more than 15% labor savings.

**The fix:** When you need real pushback, add this to your prompt: *"My role is to challenge this decision on its merits, not support it. If you see a problem, name it directly. If this idea doesn't work, tell me why."*

Try it next time you're on the fence about something. You'll get the argument, not the cheerleading.

---

## 5. New Tool Worth Trying

**Claude on iPhone — 5 minutes to try.**

1. Download Claude app from App Store (free)
2. Open, sign in with bob.cline2000@gmail.com
3. Type: "I'm at a Five Guys location. In one paragraph, tell me the three things I should check right now as a manager on shift."
4. Read the answer. (Hint: it's probably better than what's in your head after 8 hours.)

Do this at the end of your next shift. iPhone version has voice input — talk at it instead of typing. End-of-shift recap in 30 seconds: "Here's what we did, here's what broke, here's what I'm fixing next shift." Let Claude turn it into notes.

Takes 5 minutes. You'll use it every shift after.

---

## 6. AI in the Wild — Restaurant Relevant

**The real play: Instacart and DoorDash merger.**

DoorDash is in late-stage talks to buy Instacart (announced Oct 27). This matters for restaurants because:
- **Consolidation is real.** Fewer platforms means less negotiating power for independent operators. Your commission fees are probably going up in 12-18 months.
- **Grocery bundling.** DoorDash wants to sell you on "customers coming for groceries also order restaurant food." That's table stakes now if you want delivery relevance. Five Guys' national scale handles this; smaller chains get squeezed.
- **Tech integration.** Winning platforms will have real POS integration, real data, real analytics. If you're manually entering Instacart orders into your system, that's your wake-up call.

**For you right now:** Check your delivery platform mix. If you're on multiple platforms, DoorDash-Instacart marriage probably means better inventory visibility and order accuracy (both good). If DoorDash is your only play, you're in a consolidation buyer's hands now.

---

## 7. Skill Up — Do This Today

**Task: Turn a manager complaint into a system fix proposal.**

Next time a manager says "we keep forgetting to restock the shake machine in the morning," paste this into Claude:

```
Manager complaint: [PASTE THE EXACT COMPLAINT HERE]

Answer these questions:
1. How often does this actually happen?
2. What's the real cost? (labor, waste, lost orders, customer frustration)
3. What's the root cause? (person, process, tool, priority?)
4. What's the simplest fix? (one change, not five)
5. How do you measure if it worked?
```

Claude will pull you out of "someone needs to remember better" and into "here's the actual system problem and the actual fix." Do this once a week for one broken process. After four weeks you'll have fixed four broken things instead of complained about twelve.

**Your question for next time:** What's one recurring problem on your shift that Claude diagnosed differently than you expected?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>