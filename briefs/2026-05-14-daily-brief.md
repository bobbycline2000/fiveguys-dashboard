# Bobby's Daily AI Brief — 2026-05-14
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

**Opus 4.7 shipped and it's a real upgrade.** Three times higher resolution on images (you paste in a screenshot or a menu photo and Claude sees the details you used to have to zoom in to catch), and the core reasoning got sharper — about 13 points better on engineering benchmarks, which translates to fewer "almost right" answers that waste your time debugging. **The actual news for you:** Claude Projects now let you upload your entire Five Guys playbook (SOPs, checklists, P&L templates) and reference it by name in chat instead of pasting it every time. That's labor saved. **Coming soon:** Managed Agents got a feature called "Dreaming" (early access) that lets Claude review past weeks and spot patterns in what worked and what didn't — think of it as an automated retrospective for your shift recaps.

---

## 2. Prompt of the Week

Copy this exactly and use it after a rough shift to turn observations into action items:

```
Role: You are a shift debrief analyst for a Five Guys location.

Input: [Paste the messy shift notes below — timestamps, issues, names, whatever order]

Tasks:
1. Extract the 3 biggest bottlenecks that slowed service
2. For each, identify the ROOT cause (not the symptom)
3. Propose ONE specific action to fix it by tomorrow
4. Flag any safety or compliance issues — immediate
5. Highlight ONE thing your team nailed

Output format:
- CRITICAL (must fix now): [list]
- THIS WEEK (next 7 days): [action] → responsible person → deadline
- WIN: [what went right]
```

**Why this works:** It forces you to separate "shift was hectic" from "the fry station ran out of oil at 6:30 and nobody refilled" (the actual problem). The three-layer structure (now/week/pattern) means you're not drowning in fixes — you're picking the ones that move the needle. Try it tomorrow after close.

---

## 3. Use Case Spotlight

**The Profit Leak Your P&L Report Won't Show**

Most operators see: "Food Cost: 28.5%, Labor: 32%, Waste: 1.2%" and think they understand the picture. They don't.

**Real case:** Store with a 28.5% food cost on paper but actually losing $8k/month to invisible waste — unsold sandwiches at close, oil changes that don't get logged, prep that goes bad because someone made too much.

**What Claude does:** Paste your inventory sheet + your sales report + your shrink number into Projects. Ask: "Walk me through where we're leaking money." Claude cross-references ingredient usage against menu sales and flags the mismatch. In one case: "You're buying 40 lb of ground beef weekly but your burger sales suggest you only use 28 lb. 30% waste, every week."

**The fix:** One conversation with Claude. Fifteen minutes to diagnose. One training shift on prep sizing. $30k/year back in your margin.

**This week:** Pull your last 4 weeks of inventory data and paste it into Claude Projects with your sales numbers. Ask it to find the waste.

---

## 4. Gotcha of the Week

**Claude will be helpful and wrong at the same time.**

You ask: "What's a good food cost for a burger shop?"

Claude says: "Industry standard is 28–32%." Confident. Sounds authoritative.

**The trap:** Five Guys is not "industry standard." Your beef sourcing, your fresh-never-frozen model, your customization waste — that's not the same as a chain that pre-portions and uses frozen. Claude just invented a number that's reasonable-sounding but not your reality.

**Fix:** Always compare Claude's answers against YOUR actual numbers first. Ask a follow-up: "What's MY food cost trending?" Pull your last quarter. See if the "standard" makes sense for your store. If it doesn't, tell Claude the mismatch — that's the actual signal.

---

## 5. New Tool Worth Trying — 5 Minutes

**Claude Projects (upload once, reference forever).**

Steps:
1. Go to claude.ai/projects
2. Click "New Project"
3. Name it "Five Guys SOP Library"
4. Click the paperclip — upload your checklist PDFs, SOP docs, training docs, anything that lives in your playbook
5. In chat, ask: "Based on my SOPs, what's the correct procedure for opening the fry station?"

**Why:** Instead of hunting through files or pasting the same 10-page manual every conversation, you tell Claude "use my projects" and it remembers. Your brain stays on the problem, not on file management. Five-minute setup, saves you 30 minutes a week.

---

## 6. AI in the Wild — Restaurant Relevant

**Your competitors are waking up to labor scheduling.**

37% of restaurant operators are now adopting AI-driven automated scheduling (up from 22% last year). They're not doing it for fun — labor is the margin killer right now. Store with 32% labor is getting crushed by one with 29%, and that gap comes down to shifts matching demand.

**Five Guys specific:** You run 4 stores. If each one is building schedules on a spreadsheet with "I think we need more people on Saturday," you're leaving 2–3 points of margin on the table just by not matching labor to actual foot traffic. AI scheduling platforms are learning your patterns — weather, events, historical demand — and suggesting shifts before you even ask.

**Real play:** Teamworx (which Bobby uses for scheduling) likely has a forecasting layer now or coming soon. Check with your scheduler whether they've launched AI-assisted demand forecasting. If yes, try it for two weeks. If it cuts your overtime by 8 hours/week, that's worth the learning curve. If no, file it as "the real win is coming."

---

## 7. Skill Up — Do This Today

**Practice: Turn chaos into structure.**

Write down three real problems from your Five Guys job that live in your head right now. Don't organize them — just dump them:
- "Opening AM crew is slower than lunch crew, not sure why"
- "Food cost spiked last week, nobody knows which item"
- "Cashier station gets backed up around 5 PM"

Paste those three into Claude. Say: "These are my problems. For each one, tell me what data I need to collect to actually diagnose it."

You'll get back something like:
- Timing data: How long does each opening task actually take?
- Inventory data: Which items moved vs. which sat?
- Traffic data: How many customers per 15-min window at 5 PM?

**The question for next brief:** Did any of those "data points" surprise you? Which one would be easiest to pull?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
