# Bobby's Daily AI Brief — July 2, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude Sonnet 5 shipped yesterday (June 30), and it's the model that actually matters for you right now. This is the one that handles coding, agents, and the heavy lifting your dashboard and automations run on. Faster, more reliable at complex reasoning. The upgrade is already live — if you're using Claude it's probably running on Sonnet 5 without any action from you.

Fable 5 (the fast model) comes back online July 1 after being suspended for safety review. This one's your lightweight option when you just need quick answers and don't need the heavier reasoning. Use it for Slack replies, quick questions, things that don't need 3-minute thinking time.

Bottom line: Your existing flows get better with Sonnet 5. No changes needed, just faster and more reliable. Fable 5 back as a speed option for lightweight tasks.

---

## 2. Prompt of the Week

**End-of-Shift Labor Recap — Turn chaos into data**

Use this exact prompt in Claude when you're wrapping the day:

```
You are a Five Guys operations analyst. I'm going to paste my notes from closing today. 
Your job: (1) Extract the staffing issues — who was short, late, or left early, (2) Flag 
any wage/labor compliance concerns (off-the-clock work, shifts too long, break violations), 
(3) Summarize the actual labor cost vs expected, (4) Give me 2-3 one-liners for the team 
to address this tomorrow, (5) Spot any trends if I give you 3+ days of notes.

Only use what I explicitly state. Don't invent details. Flag anything unclear as [UNCLEAR].
```

Then paste your closing notes — messy text, bullet points, whatever form they're in. 

This works because it gives Claude a real role (analyst, not chatbot), hard constraints (use only what's stated, flag unknowns), and specific outputs (5 things to deliver, in order). You get data you can act on instead of commentary. When you paste 3 consecutive days of these, Claude can spot the pattern you're living in but might not notice.

---

## 3. Use Case Spotlight

**Problem:** You close at 11 PM, write down labor notes in fragments — "Sarah didn't show til 4, we ran short dinner," "gave Jordan extra break," "Marcus went home at 9" — and by Monday morning it's gone. You don't remember whether that was a one-off or a pattern. By Friday you look at payroll and see overspend but can't trace why.

**Solution:** Paste that messy closing note into Claude with the prompt above. You get back:

```
STAFFING ISSUES:
- Sarah: 2-hour late arrival (gaps dinner rush)
- Marcus: Left 2 hours early (didn't finish closing)

WAGE CONCERNS:
- Extra break given to Jordan (clarify — paid or unpaid?)
- Missing info on whether closing shift was stretched

LABOR COST IMPACT:
- Expected 4 staff, ran 3 from 5–6 PM (estimated $45 delta)

TOMORROW'S ACTIONS:
- Confirm Sarah's availability Wed before 2 PM
- Review Jordan break policy with team
- Tighten closing-shift handoff procedures

TREND WATCH: Need 3 more days to spot pattern.
```

Now instead of "payroll looks high but I'm not sure why," you have a dated record you can reference. Three weeks of these and you see: "Sarah's consistently 1–2 hours late on Tuesday–Wednesday. It's costing us $300/month in gap coverage."

Then you solve it (talk to Sarah, adjust scheduling, hire another closer).

---

## 4. Gotcha of the Week

**The Invisible Trade-off**

Claude is excellent at reasoning inside a system (analyzing your P&L, drafting an SOP, summarizing your schedule challenges). Claude is confident but unreliable at *facts outside your system* (what the competitor down the street charges, what Five Guys corporate policy technically says, how much insurance costs in Kentucky).

The trap: You ask Claude "what should I charge for a bacon cheeseburger?" and it gives you a answer that sounds reasonable. But it's hallucinating based on averages, not the actual Five Guys pricing your franchisee agreement locks you into. You make decisions on invented facts.

**The fix:** Any time Claude is answering a factual question about something outside your direct control (policy, pricing, regulations, competitor moves), follow up with "where did that number come from?" If Claude says "based on industry averages" or "typical pricing," that's a hallucination flag. Go verify with your source (your franchisee agreement, the Five Guys Operator Handbook, Crystal at Estep).

For analysis inside your system (your labor numbers, your food cost, your schedule), Claude is trustworthy. For facts outside it, verify.

---

## 5. New Tool Worth Trying

**Claude on your phone — voice mode for end-of-shift dumping**

If you have Claude on your iPhone (free app), open it and tap the microphone icon. Talk to Claude like you're debriefing a friend: "We were short on the line today, Sarah didn't show until four, Marcus left early, and we ran out of bacon fries by nine." Claude transcribes it, then you paste the full conversation into the labor-recap prompt from section 2 above.

**Exact steps:**
1. Open Claude app on iPhone
2. Tap the waveform icon (bottom right of message box)
3. Speak naturally for 15–30 seconds — just vent the day
4. Tap stop
5. Copy the transcript (long-press the message, tap Copy)
6. Open Claude on desktop, paste, run the "end-of-shift labor recap" prompt

Total time: 3 minutes. You've now got dated, timestamped labor notes you can reference. Five days of these and you have a labor log that would take 30 minutes to write by hand.

---

## 6. AI in the Wild — Restaurant Relevant

**Luckin Coffee is opening kiosk-only locations in NYC subway stations.** No baristas. Customers order on the kiosk or app, coffee machine dispenses. Luckin is a Chinese chain that got aggressive with AI and automation early. They're expanding hard into the US. 

Why this matters: Luckin's model — minimal labor, high volume, low-touch transactions — is exactly what works for high-traffic urban locations. Five Guys is the opposite: high-touch, high-customization, higher labor cost. But *inside* your existing model, you can steal pieces: Are there repeatable orders that could be pre-built? Can a kiosk handle simple orders in peak times so your crew focuses on customization? Could you pre-bag fries during slow periods so you're not racing during dinner rush?

You're not going full Luckin. But watching how they handle the labor equation teaches you something about your own.

---

## 7. Skill Up — Do This Today

**Teach Claude your actual labor standards for a shift.**

Create a new Claude project right now (takes 30 seconds). Name it "2065 Labor Standards." Upload a document that answers these:
- What's the minimum staffing for each hour (Mon–Sun)?
- What are break policies? When? How long?
- When does labor typically exceed 30% of sales?
- What's your target wage per labor hour for the week?

Then paste a recent shift and ask Claude: "Does this shift fit our standards? What's off?"

Claude will remember your standards for the next week. You'll catch problems faster. "We ran short by 2 people Wed 5–7 PM" instead of "payroll is high, I'm not sure why."

**One question for next time:** Once you run this for a week, what surprised you? What pattern did you miss? Hit reply and tell me.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
