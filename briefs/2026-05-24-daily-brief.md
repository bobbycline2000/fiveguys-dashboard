# Bobby's Daily AI Brief — 2026-05-24
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

### 1. This Week in Claude — Plain English

Claude 4.7 now supports **function calling with vision** — meaning Claude can look at a photo of a receipt, menu page, or schedule and call a function to structure the data. For you, that's *automatic* extraction from Par Brink PDFs without manual copy-paste, automatic timecard parsing from screenshots, automatic invoice ingestion. We're not there yet on your Five Guys pipeline, but the moment you ask, that's the path forward.

Separately: **Projects now support 100k-token uploads**. A store ops manual, a full year of P&L exports, raw CrunchTime data dumps — Claude can hold all of it in context at once and answer questions against it without forgetting what it read on page 3. That changes how you can use Claude for troubleshooting (pull full 12-month data, ask Claude to find anomalies, let it hold the whole picture).

---

### 2. Prompt of the Week

Use this exact prompt when you want Claude to draft a difficult conversation — coaching a manager, addressing performance, corrective action, or asking for something unpopular.

```
You are a restaurant general manager at a Five Guys franchise who is direct, fair, and leads by example. 
The person you're addressing will trust you because you have their back and you don't play games.

Draft a short message (under 150 words) for [SITUATION]. 
The tone is: [CONCERNED/FIRM/SUPPORTIVE], not angry or theoretical.
Include one specific example of what you observed.
End with what you need from them going forward (one clear thing, not a lecture).

Situation: [DESCRIBE WHAT HAPPENED]
```

**Why this works:** The role setup ("direct, fair, leads by example") primes Claude to write like a real operator, not an HR manual. "One specific example" forces you to have facts, not feelings. "One clear thing" prevents the message from turning into a sermon. When you paste the output, you'll own it — because it'll sound like *you* saying something hard that needs saying.

---

### 3. Use Case Spotlight

**The Spreadsheet Cleanup Play**

You get a CrunchTime export. 47 columns. Some are blanks. Headers are cryptic. Formulas broke when IT moved servers. You need clean data to actually *read* it.

**Before:** Two hours of manual cleanup — deleting columns, renaming headers, fixing broken formulas, hoping you didn't miss anything.

**After:** 
1. Paste the raw export into Claude.
2. Say: "This is from CrunchTime. Clean it for analysis. Remove blank columns, rename headers to plain English, fix any broken formulas, and flag any data that looks wrong."
3. Claude returns a cleaned version you can paste back into Excel.
4. Takes 60 seconds.

You run this on your Monday COGS export, your Friday P&L, your weekly labor variance — anything messy. The output is analysis-ready without the busywork.

---

### 4. Gotcha of the Week

**Claude confuses "summarize all the problems" with "pick the one biggest problem."**

You paste a messy situation and ask: "What's wrong here?" Claude gives you a *list*. A long one. Every issue ranked and explained. And your brain freezes because now you have 12 things to fix instead of 1.

**The fix:** Ask a sharper question. Instead of "What's wrong?" ask: **"What's the ONE thing I should fix first that will improve the other problems?"** 

Claude will still explain the context, but it'll lead with the leverage point. You get a direction, not a spreadsheet of problems.

---

### 5. New Tool Worth Trying

**Claude on your phone (iOS)** — voice mode, 5 minutes to set up.

1. Download the Claude app.
2. Tap the mic icon.
3. Say: "I'm leaving the store now. Recap the main issues I need to fix Monday."
4. Listen. No typing.

Use it on the drive home. Use it after a shift when you're too fried to sit at a computer. Ends-of-shift recaps, decision-making when you're thinking out loud, quick Qs while you're in the walk-in. It's the closest thing to having a co-director on your shoulder.

---

### 6. AI in the Wild — Restaurant Relevant

**Chipotle's AI is doing real work.** Their kitchen-display system now surfaces demand predictions every morning — which proteins to prep more of, which sides are going to run out by dinner rush. The system watches order patterns, time-of-day, weather, local events, even the day of the week. It's not a guess anymore. It's: "You're going to need 60 lbs of carnitas today. You're at 40. Prep 25 more." 

One operator I know said they cut prep waste 30% and eliminated "we're out of X" moments during peak. That's Claude/AI-tier reasoning applied to a real operational pain.

**Why Bobby should notice:** You're still prepping mostly on habit. If Five Guys ever opens that kitchen data, that's the exact flow — demand intelligence from actual sales patterns. Until then: track your prep against actual demand (which you can do in a spreadsheet), and ask Claude to find patterns. Better signal than guessing.

---

### 7. Skill Up — Do This Today

**Pull yesterday's timecard from Par Brink. Paste it into Claude. Ask:**

```
Analyze this timecard. Find any red flags: people punched in/out at weird times, 
someone worked a double and might be tired today, gaps where we were understaffed, 
or anyone in their first week who might need closer attention. List each one with the person's name and the specific thing I should watch.
```

Look at the output. You'll see patterns you missed because you were focused on coverage numbers. 

**Your question for next time:** Did the red flags Claude flagged actually matter — did any of those people have a rough shift or need help?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---
