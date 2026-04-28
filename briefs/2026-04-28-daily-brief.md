# Bobby's Daily AI Brief — 2026-04-28
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

**Claude Design just landed** (Apr 17). It's a visual design tool inside Claude that lets you build mockups, one-pagers, slides, and marketing materials. For you: this is how you build a professional-looking vendor proposal, a menu redesign mockup for Store 2065, or a dashboard printout that your DM can actually hand to corporate without embarrassment. No Canva login, no templates, no learning curve—paste your content, tell Claude what it should look like, get a clean design back.

**Claude Opus 4.7** shipped (Apr 16)—faster, smarter at multi-step tasks and vision (reading documents, photos, screenshots). You're already using Claude daily; you don't need to do anything. The next time you paste a labor report PDF or a photo of a CrunchTime screen, Opus will read it faster and more accurately. This matters less for you than it does for developers, but it's the floor.

**Skip the buzz.** Workplace integrations (Chrome, Slack, Excel) are already in your hands. The real story this week is Design—that's the new lever.

---

## 2. Prompt of the Week

Use this for your end-of-shift recap or any time you need to turn a messy voice note or journal entry into an action plan:

```
You are a Five Guys franchise operations coach with 15 years of QSR background. I'm going to paste my shift notes below. Your job is to:

1. Identify the TOP 3 issues that actually matter (not minor complaints).
2. For each, suggest ONE specific action I can take tomorrow.
3. Flag anything that needs to go up to my DM (be direct about severity).
4. Highlight any patterns you see (if this is the 3rd time this week we're seeing X, say so).

Keep it sharp. No corporate speak. I need to understand what happened and what to do about it in under 2 minutes of reading.

---
[PASTE YOUR NOTES HERE]
```

**Why this works:** The role framing tells Claude you want a coach's perspective, not a sympathetic ear. The numbered constraints force it to prioritize (top 3, not 12). The "flag for DM" section makes it safe to vent—Claude will help you figure out what's actually manager-level vs. shift-level noise. The "patterns" instruction trains Claude to spot the repeat issues you might miss when you're tired. The speed constraint at the end keeps Claude from padding the output. When you use this tomorrow after a rough shift, you'll notice: Claude stops agreeing with everything you say and starts pushing back. That's the payoff.

---

## 3. Use Case Spotlight

**CrunchTime Export → Labor Variance Analysis**

You pull a labor report from CrunchTime showing that yesterday you hit 31.2% labor, and your target is 28%. You know it happened, but you don't know *why* or *what* to fix.

Messy input:
```
DATE: 2026-04-27
SALES: $4,847
LABOR (SCHEDULED): 9.5 hours
LABOR (ACTUAL): 10.8 hours
VARIANCE: +$156 (unfavorable)

Staff breakdown:
- AM Shift (6-11am): 4 people, 5 hours = 20 hours scheduled, 21.5 actual (+ overage from no-show)
- PM Shift (11-5pm): 3 people, 4 hours = 12 hours scheduled, 14.2 actual (+ late stay for closing)
- Night Shift (5-close): 2 people, 4 hours = 8 hours scheduled, 7.1 actual (early close by GM approval)
```

Paste that into Claude with: "Break down my labor variance by shift. Which decisions are costing me the most? What would I need to do differently tomorrow to hit 28%?"

Claude output (real and actionable):
- AM shift's no-show cost you ~$67 (1.5-hour overage). Solutions: call-in backup sooner or reduce AM bench next day.
- PM shift's 2.2-hour overage = $73. Culprit: late stay. This wasn't an emergency—you approved it. Decision: close 15 min earlier or reduce PM headcount by 0.5 for lower-volume days.
- Night shift went *under*. You saved $16 by early close, but you've hit your 28% target if you kill the AM no-show buffer and tighten PM bench by 1 hour on mid-week days.

**The play:** You now have three levers to pull and know which one costs the most. Next time a no-show hits, you know it's a $67 swing—you'll be faster about calling backup.

---

## 4. Gotcha of the Week

**Claude will invent numbers and sound 100% confident.**

You ask: "What's the typical food cost percentage for a Five Guys?"

Claude might say: "Industry standard is 28–32% for fast casual." Sounds right. You use it to set your target.

Real problem: Claude doesn't know what Five Guys' actual food cost is. It's inferring from general QSR data. If Five Guys' real cost is 24% (which it might be—thinner margins in burgers), you just set a fake target that makes your real performance look terrible.

**The fix:** Never use Claude's numbers as a fact without verification. If Claude gives you a number—industry average, competitor metric, anything—follow it with: "Where does this number come from, and how confident are you?" Claude will usually admit it's a best guess. Then go verify it against your own data, your DM's reports, or corporate guidance.

For five guys food cost: ask *your* CrunchTime data. Ask your DM. Don't ask Claude and call it research.

---

## 5. New Tool Worth Trying

**Claude Projects + Your CrunchTime Weekly Export**

Takes 3 minutes:
1. Open Claude (any version, any device).
2. Click **Projects** (left sidebar).
3. **New Project** → Name it "CrunchTime Weekly Review."
4. Upload your last 2–3 weeks of CrunchTime exports (PDFs, CSVs, or screenshots).
5. Add a custom instruction: *"You are my CrunchTime analyst. When I paste shift data, break it down by: sales trend, labor %, food cost %, inventory movement, and any red flags. Keep it to a 1-minute read."*

Now, every time you export fresh numbers, paste them into that Project and ask Claude for the summary. Claude reads *all* your historical data and spots patterns you'd miss in real time.

Why: you're not starting from scratch each week. Claude sees that your Tuesday labor is always 2% higher or that your food cost dips on rainy days.

---

## 6. AI in the Wild — Restaurant Relevant

**The Joint Employer Rule just got real.** The U.S. Labor Department proposed new guidance (Apr 23, 2026) on when a franchisor is legally responsible for franchise employee labor practices—wages, scheduling, working conditions. For you as a franchise operator: this means Five Guys corporate might have more authority over your scheduling, staffing decisions, and wage decisions than they used to.

**Translation:** Your flexibility just got tighter. If corporate says "don't exceed 28% labor," they may now be liable if you pressure someone to work off the clock to hit that target. The chain is liable if you don't follow labor law. This is why your DM and corporate are going to be more prescriptive about how you staff and schedule.

**Action:** Don't wait for a memo. Start documenting your labor decisions now—why you made scheduling choices, when no-shows happened, where variance came from. That paper trail protects both you and Five Guys when questions come up.

---

## 7. Skill Up — Do This Today

**Exercise: Find Your Hidden Labor Cost**

Grab your CrunchTime export from last Monday–Wednesday (a full week). Paste it into Claude with this prompt:

*"Show me every day where actual labor was more than 1% higher than planned. For each day, tell me: what time did the overage happen (morning, peak, closing), and what's the ONE most likely cause (no-show, unexpected rush, extended break, manager approval)?"*

Claude will flag the pattern days. Pick the one that happened most often.

Then ask: *"If I could eliminate that one issue next week, how much would I save?"*

**What to look for:** You should see a clear picture of which shift, which day of the week, and which *type* of decision costs you the most. That's your leverage point.

**Question for next time:** Once you pick your top labor leak, how would you fix it—scheduling, training, backup plan, or different approval rules?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
