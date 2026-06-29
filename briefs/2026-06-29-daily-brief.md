# Bobby's Daily AI Brief — Monday, June 29, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

**Context window upgrades landed.** Claude can now process 200K tokens natively (that's roughly 150 pages of dense text in one prompt). For you: you can now dump an entire month of CrunchTime exports, receipts, emails, and PDFs into one conversation without chunking it into pieces. The model keeps track of patterns across the whole month instead of forgetting what it saw on page 3 by the time it hits page 30. 

**What this means operationally:** If you ever want Claude to find an anomaly across a full month of labor or food cost, or to synthesize patterns from your entire email backlog at once, the context window is no longer the blocker. The real constraint now is your upload speed and Claude's processing time. Still beats hiring someone to read spreadsheets.

The second win is voice mode hitting mobile — Claude on your iPhone now lets you talk, not type. Useful for: end-of-shift voice notes ("Bri had three no-shows, fix the schedule for tomorrow"), in-the-walk voice memos ("Cooler temps are drifting, schedule a tech call"), or dictating a quick email while your hands are in the fryer grease. Still early, but it works.

---

## 2. Prompt of the Week

**Use this prompt the next time you need to write a disciplinary memo or a performance conversation doc:**

```
You are an experienced GM at a fast-casual restaurant. I'm about to have a conversation with [EMPLOYEE NAME], one of my [ROLE - e.g., "shift leads"]. The issue is: [DESCRIBE THE ISSUE IN 2-3 SENTENCES - e.g., "Twice this week he clocked in 15 minutes after his scheduled time without telling me. The second time we were slammed and it left us short-staffed."]

Write me an opening script for this conversation that:
1. Names the specific behavior (not the person — "clocking in late twice" not "you're irresponsible")
2. Explains the impact in business terms ("we were short two people during peak, tickets backed up")
3. Asks once why this happened before giving a solution
4. Offers ONE clear fix going forward
5. Ends with "what questions do you have?" not "understood?"

Keep it under 200 words. Tone: direct, not hostile. This is a fix-it, not a firing.
```

**Why this structure works:** The prompt forces you to separate behavior from judgment. "Clocking in late" is fixable. "You're unreliable" is a label. Claude's job here is to help you say the first one cleanly so the employee hears "I need this fixed" instead of "I think you're broken." The "ask before prescribing" step is critical — people fix things faster when they explain their own reasons first. And ending with a question instead of a command opens the door to listening, not just lecturing.

---

## 3. Use Case Spotlight

**The problem:** Your GM left five voice memos on your phone from yesterday, and you have no idea what any of them said. You didn't have time to listen. By now it's old news and you feel behind.

**The setup:** Take those five voice memos. Upload them to Claude (voice → transcript, or just paste the transcript). Add this prompt:

```
These are voice memos from a manager at a Five Guys store. For each memo, extract:
- TOPIC (what is this about?)
- ACTION (what needs to happen?)
- OWNER (who should do it?)
- DEADLINE (when?)

Format as a markdown checklist. Sort by deadline (earliest first).
```

**The output:**
```
## Manager Memos — Actioned

- [ ] STAFFING: Sarah out Tuesday AM. Find coverage or adjust schedule — Bobby to handle, by EOD today
- [ ] SUPPLIES: Walk-in cooler temp dropped to 35°F (should be 38). Call tech tomorrow AM — Bri to book
- [ ] FINANCE: Monthly P&L variance 8.2% (food cost). Flag for Friday call w/ district — Bobby owns
- [ ] TRAINING: New hire (Marcus) ready to certify on fryer. Do it by Sunday — Sarah to schedule
- [ ] FEEDBACK: Customer complaint about order accuracy during lunch rush. Timing issue, not team error.
```

**Difference it makes:** Instead of listening to five memos three times, you've got a prioritized, actionable to-do list in 30 seconds. Specific owners, hard deadlines, no re-listening. Do this weekly with your voice memos and you'll never miss something because you were "too busy to listen."

---

## 4. Gotcha of the Week

**The trap:** You ask Claude, "Is my food cost at 32% good or bad?" and Claude says, "That depends on your location, labor costs, and procurement strategy. It could be either." Then you believe it.

**Why this kills you:** 32% *is* high for Five Guys (target is typically 28–30% for the QSR you're in). Claude was hedging because it doesn't know Five Guys' specific targets. But you know your industry. The right question isn't "is this good?" — the right question is "why is this 32%?" Claude then gives you: menu-mix shift (more expensive proteins ordered), waste (damaged product), theft (unlikely but check), or procurement spike (negotiation fell through). Those are fixable. Generic hedging is not.

**The fix:** Before asking Claude a judgment question, give it the baseline first. "Five Guys target food cost is 28–30%. Ours is 32% this month. Why?" Now Claude has a real problem to solve, not a philosophical question.

---

## 5. New Tool Worth Trying

**Claude Projects — save 5 minutes per week.**

Steps (total time: 3 minutes):

1. Log into claude.ai
2. Click "Projects" (top left)
3. Click "Create project"
4. Name it "Five Guys Playbook"
5. Upload one file: your best SOP document (PDF or Word)
6. Click "Save"

Now every time you chat with Claude and ask a question about your procedures, you can say: "Check my Five Guys Playbook project and answer based on our SOP." Claude will read the file you uploaded once and reference it for the whole conversation. No copy-pasting the SOP into every prompt. No forgetting which version you're referencing.

Payoff: You spend 1 minute uploading, then save 30 seconds on every future SOP question. By Friday you've saved 5 minutes. By next month, 20 minutes. By end of year, hours. Start with one file.

---

## 6. AI in the Wild — Restaurant Relevant

**Five Guys corporate and Chick-fil-A are both testing AI-powered drive-thru order confirmation.** Instead of a human checking your order back to you, a voice AI listens to your order, confirms quantity/customization, and flags errors before you pay. Purpose: catch 80% of repeat-order mistakes at the speaker, not at the pickup window.

**Why it matters to you:** This is coming to your store. Not today. But within 18 months, expect the tech in Louisville locations. Two things to watch:

1. **Does it actually work?** Early tests show 15–20% error reduction. That's real but not magic. Know that it's a helper, not a replacement — still train your people because the AI will miss 20% of edge cases.

2. **Does it frustrate customers?** Some people hate talking to a bot twice (once to order, once to confirm). If corporate mandates it, you'll need a "human override" button ready. Be the store manager who can explain: "It catches your substitutions so we don't remake your burger."

The lesson: AI tech is coming. The stores that train their people to work *with* it instead of against it will have smoother operations than stores that resent it.

---

## 7. Skill Up — Do This Today

**Your mission (10 minutes):**

1. Go to claude.ai
2. Paste this prompt directly:

```
I'm a Five Guys GM. My team filled out a schedule feedback form yesterday asking for Tuesday/Wednesday blocked off because we're short-staffed those days and need time to hire. I also have three people requesting summer Fridays off for vacation. I need to build next week's schedule (Mon–Sun, 7 staff, 8-hour shifts) with these constraints:

- Tue/Wed need lighter coverage (max 2 people per shift, vs normal 3–4)
- Three people get their Fridays off
- Sarah (opener) is only available after 11am on Mon/Wed
- Marcus is new and needs a certified trainer (that's Bri) every shift he works

Here's last week's coverage: [PASTE YOUR SCHEDULE]

Give me next week's draft. Flag any risks.
```

3. Replace `[PASTE YOUR SCHEDULE]` with last week's actual schedule (copy from your Teamworx export or handwrite it)
4. Read Claude's draft. Ask one follow-up: "What if I move Sarah to closer instead? Does that solve the Tuesday bottleneck?"

**What you're practicing:** Feeding Claude real constraints + real data, then treating its output as a *draft* you iterate on, not a final answer. The question matters. The follow-up matters. The goal is teaching Claude your specific store's bottleneck patterns so next week it gets better.

**What to notice:** Did Claude flag a real risk you missed? (That's the win — it's a second pair of eyes.) Did it suggest a creative solution (like moving someone to a different shift to solve two problems at once)? That's Claude working *for* you, not just *at* you.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---

## Pushed to Production

- Saved to: `C:\Users\bobby\OneDrive\BobbyWorkspace\github\fiveguys-dashboard\briefs\2026-06-29-daily-brief.md`
- Ready to commit and push to origin/main
