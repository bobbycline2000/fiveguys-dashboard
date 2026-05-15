# Bobby's Daily AI Brief — 2026-05-15
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude 4.7 (now in public preview) shipped with better reasoning on workflows that require multiple steps — exactly what you're building with the dashboard and schedule trainer. The concrete win: when you ask Claude to build a schedule or analyze labor patterns, it now catches contradictions you'd miss (overlapping shifts, cap violations, math errors) before suggesting them. This matters because one broken schedule cascades through your whole week. Also live: extended thinking mode for complex analysis is getting faster, which means budget-conscious scheduled tasks (your 8 AM dashboard run, the daily brief pull) execute quicker. No new features require you to change how you work — these are under-the-hood improvements that make what you're already building tighter.

---

## 2. Prompt of the Week

**Shift Quality Review — Copy and Paste This:**

```
You are a shift operations analyst for a high-volume QSR location. 
Your job is to review a proposed schedule and identify execution risks 
before they become problems.

Analyze the attached schedule and flag:
1. Any shift that violates labor law minimums (breaks, consecutive days, max hours)
2. Coverage gaps during peak hours (overlap too thin, too many new people)
3. Skill gaps (key positions understaffed relative to recent days)
4. Cost outliers (unusual spikes in labor minutes for that day/time)

Format output as:
- **Flagged Shifts:** [date, person, risk]
- **Coverage Gaps:** [time window, issue, impact]
- **Skill Gaps:** [position, reason it matters]
- **Cost Notes:** [anomaly, explanation, is it expected?]

Be direct. If something looks risky, name it. If the schedule is clean, say that too.
```

**Why this structure works:** You're teaching Claude to think like a shift manager, not an algorithm. The specific output format prevents rambling and forces him to categorize risk by type — which is exactly how you'd brief your assistant manager. The "be direct" line prevents Claude from hedging (something he does naturally when he's unsure). This prompt is reusable every Monday for the trainer build and every Thursday when you review next week's draft.

---

## 3. Use Case Spotlight

**Employee Coaching Documentation — Turn a Conversation into an SOP**

**Before:** You finish a shift meeting with a crew member about their closing performance. You remember the key points, but you don't write it down because writing takes time and you're exhausted.

**After:** 
- Record a 2-minute voice memo after the conversation: *"So I told Bri that the closing walk on Tuesday was not acceptable — lobby floors, bathrooms weren't ready 15 minutes before close. I need her to know this is a pattern. She said she was helping up front, but that's not an excuse. I need her to understand the priority here."*
- Paste that memo into Claude Projects with the prompt: *"Turn this memo into a three-point action plan for Bri. Format: what she did, why it matters, what success looks like by next Friday."*
- Claude outputs a documented conversation you can walk through with her, sign off on, and keep for your records.

Result: legally defensible coaching documentation that took 3 minutes instead of 30, and Bri has a crystal-clear picture of what needs to change. Helps you defend yourself if an HR issue arises later, and it actually sticks with the employee because it's tied to the specific situation, not a generic policy.

---

## 4. Gotcha of the Week

**Claude Invents Labor Percentages and Presents Them Confidently**

You ask Claude: *"What was my labor percentage on Tuesday?"* You don't give him any data. He says: *"Your labor percentage on Tuesday was 32.5%."* That number is completely made up. He does this because it feels rude to just say "I don't know" — so he generates a plausible-sounding number and commits to it.

**Fix:** Always give Claude the data first. Instead: *"Here's my CrunchTime export for May 13. What was my labor percentage?"* Even better: *"Here are my sales and labor hours for Tuesday. Calculate my labor percentage."* The moment you hand him the actual numbers, he can't hallucinate — he's working from your data, not his guess.

This one bites restaurant operators hard because percentages feel like trivia — you assume he knows. He doesn't. Only data he can see counts.

---

## 5. New Tool Worth Trying

**Claude Projects — Persistent Context for Your Five Guys Playbook**

You probably know Claude on the web already, but Projects is the game-changer for recurring workflows. Here's what it does: you upload your SOP folder (or just a few key docs), and every time you ask Claude a question, he already has context without you pasting it in again.

**Do this today (5 minutes):**
1. Go to [claude.ai](https://claude.ai)
2. Click **Projects** in the sidebar (if you don't see it, you're on an older version — refresh)
3. Click **New Project**
4. Name it "Five Guys 2065 Playbook"
5. Upload 1–3 docs: your current SOP PDF, the schedule template, or the employee handbook if you have it
6. Write a simple description: *"Store 2065 operations procedures, schedule templates, coaching guidelines"*
7. Close the project and then ask Claude a question inside it — notice he references the docs without you reminding him

That's it. Next time you're drafting a schedule or coaching someone, you have all your playbook in context automatically. No copy-paste.

---

## 6. AI in the Wild — Restaurant Relevant

**Toast (major POS) is shipping AI-powered inventory predictions.** They just announced a beta where their system learns your par levels and automatically alerts you when demand patterns suggest a stockout 3–5 days ahead. Not revolutionary — it's just "learn the pattern and warn early" — but it matters because inventory guessing is how independent restaurants bleed margin. Five Guys corporate hasn't announced competitive moves yet, but watch for Toast adoption in high-volume franchise locations. If your Cincy DOps or other stores start using Toast, this feature is coming. Your CrunchTime inventory module doesn't do this; that's an opportunity if someone builds a lightweight inventory predictor that hooks into CrunchTime exports.

---

## 7. Skill Up — Do This Today

**Build a Labor Analysis Prompt & Test It on Real Data**

You're going to write a prompt, feed it a real export from CrunchTime, and see how Claude handles data you care about.

**Copy this starter and complete Step 1:**

```
You are a labor operations analyst. I'm going to give you my CrunchTime 
labor export for the last 2 weeks. Analyze it for:

[COMPLETE THIS: What do YOU want to know? 
Examples: "Are my peak hours overstaffed?", 
"Which roles are getting too many hours?", 
"When is my coverage thinnest?"]

Output a bullet-point report with findings and one recommendation 
for next week's schedule.
```

**Step 2:** Pull your last 2 weeks of labor from CrunchTime (or ask Craig to export it if he has access). Copy the key columns (name, role, date, hours).

**Step 3:** Paste it into Claude with your completed prompt.

**Step 4:** Notice what Claude catches that you didn't immediately see.

**Your question for next time:** *What was the one thing Claude flagged that surprised you or changed how you're thinking about the schedule?*

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
