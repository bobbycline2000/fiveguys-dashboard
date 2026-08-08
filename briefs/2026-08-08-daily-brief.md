# Bobby's Daily AI Brief — 2026-08-08
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude 5 Opus landed this week with a hard edge: 200k context window, faster output, tighter reasoning. The money move for operators like you is **Claude Projects with file upload**. You can now take your CrunchTime exports, Par Brink reports, your entire employee handbook, or a competitor's menu system — drop them in a Project — and Claude learns from them across every conversation. No re-uploading. No forgetting context. Single source of truth. The beta is live now. What this means: you build ONE Project for "2065 Operations," upload your SOP, your current schedule, your food cost targets, and every question you ask Claude about scheduling, staffing, or variance starts from your actual data, not generic QSR wisdom. That's the gap closer for lights-out automation.

---

## 2. Prompt of the Week

**The Labor Shift Recap Prompt** — use this at the end of every shift to turn observations into action items.

```
You are a Five Guys shift coach. Your job is to help managers turn shift chaos into clear patterns.

I'm giving you my shift notes. Extract:
1. **One thing that worked** — what did we nail today? Be specific (speed, quality, staff morale, a training moment).
2. **One bottleneck** — where did we slow down or stumble? Time, process, staffing?
3. **One forward move** — what's one thing to try tomorrow to build on #1 or fix #2? Has to be doable in your first 30 minutes.
4. **Staffing pattern** — who was on point today? Who needs a conversation?

Don't give me generic advice. Give me tomorrow's first 30-minute move.

---

[PASTE YOUR SHIFT NOTES HERE]
```

Why this works: The role setup ("shift coach" not "consultant") makes Claude give you specific over abstract. The extraction format forces him to separate signal from noise. The "doable in 30 minutes" constraint is the key — it stops Claude from suggesting a 3-hour retraining program and makes him give you the micro-move that actually moves the needle tomorrow. You'll start noticing patterns by Friday.

---

## 3. Use Case Spotlight

**Before:** Par Brink email lands. Bobby copies the PDF text into a Notes app, manually pulls out hourly labor $, calculates variance against last week, and fires up an email draft with three typos.

**After:** Upload the Par Brink PDF to your 2065 Operations Project. Ask Claude: "Labor variance vs. last Friday — what's the pattern, and what's one staffing lever I can pull Monday?" Claude reads the numbers, compares them to your SOP (uploaded to Project), flags the hour you're bleeding labor cost, and gives you one specific adjustment: "7-10 PM is 15% over. That's 3-person fry for 2-person volume. Try single fry with Sandwich pick on sides from Prep Sat–Tue. Saves $42/day that window."

The difference: you go from reactive reporting to predictive staffing. And the output is not a guess — Claude is working from YOUR actual data, YOUR standards, YOUR constraints.

---

## 4. Gotcha of the Week

**The Confidence Trap:** Claude will give you a number and deliver it in the same tone as true facts. Example — Bobby asks, "What's the average QSR labor cost percentage?" Claude says, "Industry standard is 28–32% of sales." Sounds good. Bobby writes a note around it. Six months later a consultant says it's actually 26–34% and Bobby looks uninformed in a room. 

**The fix:** When Claude gives you a benchmark, a percentage, a cost figure, or industry data you're not 100% sure about, ask: "What's your source for that?" If Claude says "general knowledge" — don't use it in writing to anyone outside your team. Teach Claude to distinguish between *true data* (Par Brink numbers, your actual P&L, your SOP) and *estimated ranges* (industry benchmarks). You did: "Use only numbers from files in this Project or my actual stores. If I ask for an industry benchmark, say 'I don't have a source for that — what range do you actually see?'" That discipline saves you credibility.

---

## 5. New Tool Worth Trying

**Voice Mode on Claude App.** 

1. Open Claude on your phone (iOS or Android).
2. Tap the mic icon next to the message bar.
3. Say: "Schedule build thoughts — we're tight on coverage Tuesday dinner, got three people out. Walk me through Monday's move."
4. Claude talks back.

You get real-time voice conversation for end-of-shift debriefs, morning-pre-call thinking, or talking through a problem while your hands are doing other stuff. Try it for one shift recap today. Takes 2 minutes to activate. That's it.

---

## 6. AI in the Wild — Restaurant Relevant

Wendy's just took major action to reverse sales decline: rebranding the value menu and tightening operational consistency. Their move signals an industry-wide realization — operators who compete on data (real-time sales patterns, labor optimization, waste reduction) beat operators who compete on marketing spend. Toast and R365 are racing to add AI co-pilot features for kitchen managers because that's where margin lives now. This is NOT theoretical. The chain that figures out "labor per hour of revenue" at the shift level wins. You're already building that. Don't wait for corporate to catch up.

---

## 7. Skill Up — Do This Today

**Prompt:** Paste this into your 2065 Operations Project and follow through.

```
I'm uploading my P&L summary and last four weeks of Par Brink reports. Here's what I want to understand:

1. Which hour of the day is my highest-variance hour (actual labor vs. theoretical)?
2. What's the staffing pattern on that hour? (I'll tell you now: [describe your current staffing])
3. One micro-change I can test this week that costs nothing and saves 45 min of labor per day?

Focus on actionable, not theory.
```

Then upload your last 4 weeks of Par Brink reports and your latest P&L. Wait for the answer. Your question tomorrow: **What surprised you in that answer?** Was it the hour you expected, or did Claude surface something you'd been missing?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
