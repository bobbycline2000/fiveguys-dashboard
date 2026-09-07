# Bobby's Daily AI Brief — September 7, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Labor Day weekend just ended. Restaurants took the hit on payroll — holiday time premiums, overstaffing to handle crowds, thin margins on food cost with higher supplier demand. Claude hasn't shipped new consumer features this week (corporate holiday pause), but what's live is exactly what you need right now: voice mode for voice-to-text end-of-shift recaps, file uploads for your CrunchTime exports, and Claude on your phone for quick operational questions while you're on the floor. No setup required. Open claude.ai on your phone, ask a question about scheduling or labor variance, and you get an answer in 60 seconds instead of hunting through dashboards. That's the win this week.

**Why it matters:** You're in damage-control mode after the holiday weekend. Labor variance is up. Inventory counts are probably messy. Claude on your phone lets you spot-check decisions in real-time without touching a computer.

---

## 2. Prompt of the Week

**Use this prompt right now for your post-holiday labor deep-dive:**

```
You're a restaurant operations auditor. I'm going to paste my CrunchTime labor report for the past 7 days (Labor Day week). 

Analyze it for:
1. Which shifts had the highest waste (overstaffing for the volume)?
2. Which employee(s) had the most hours over their target for the week?
3. What's one specific schedule change I should make next week to prevent this?
4. If I had to cut 5 hours from the next week's schedule, where's the safest cut?

Give me numbers, not guesses. Format as bullets. Assume I want to protect my trained crew — don't recommend cuts from your best people.
```

**Why this works:** You're handing Claude a specific job (audit, not opinion), a clear output format (bullets, numbers), and a constraint (protect trained crew). The constraint teaches Claude to think like an operator, not a spreadsheet. Paste your CrunchTime 7-day labor report into the message body, hit send, and you've got a 5-minute analysis that would take you 45 minutes to do by hand. Claude won't invent numbers — it's reading YOUR data.

---

## 3. Use Case Spotlight

**The Mess:** You have a CrunchTime email export that landed in your inbox — it's a CSV with the week's food cost breakdowns by category. It's formatted weird (merged cells, your Outlook doesn't render it right), and you need to know: which category spiked, and by how much versus last week.

**The Old Way:** Download the CSV, open Excel, manually compare lines, write down the category names that jumped, eyeball the % variance, tell yourself you'll remember it.

**The Claude Way:** 
1. Upload the CSV to Claude (drag + drop, or paste the text).
2. Prompt: *"I'm looking at this week's COGS by category. Which category is highest variance from last week? Give me: (1) category name, (2) this week's amount, (3) last week's amount, (4) $ variance, (5) one reason it might have spiked."*
3. Claude pulls the numbers, formats them, and gives you ONE clear answer — not five categories, not guesses.

**Why:** You now have a fact-based starting point for a vendor call, a manager conversation, or a decision about portion sizes. Two minutes instead of twenty. And Claude doesn't guess — if the data isn't there, it says so.

---

## 4. Gotcha of the Week

**The Trap:** You ask Claude a vague question: *"What should I do about my labor costs?"* 

Claude will say yes to EVERYTHING. "Consider: scheduling software, training, staffing ratios, reducing turnover, using predictive labor tools, cross-training, incentive programs, better forecasting..." It's not wrong, it's just not useful. It threw 8 possible fixes at you when you need 1.

**The Fix:** Be specific. Ask: *"Labor costs were 31.5% this week (target 28%). My CrunchTime shows overstaffing Fri/Sat dinner. What's the one schedule change I should make to hit 28% next week without cutting my trained crew?"* Now Claude has constraints and a specific problem. The answer will be one concrete recommendation, not a list.

**Why:** Vague questions are lazy questions. Claude isn't a Magic 8-Ball. Give it guardrails, and it becomes a tool. Leave it open-ended, and you get noise.

---

## 5. New Tool Worth Trying

**Claude for Chrome — try this right now (2 minutes):**

1. Download "Claude for Chrome" extension (search your app store, free).
2. Go to your CrunchTime login page.
3. Right-click anywhere on the page, select "Ask Claude."
4. Prompt: *"What data is available on this page? List the navigation options."*
5. Claude reads the page and tells you every report/export option.

**Why:** You don't have to hunt menus to find where the labor report is. Claude reads the live page and guides you. Next time, use it to spot a report you forgot existed.

**Time to try:** Literally 2 minutes. No config, no API key.

---

## 6. AI in the Wild — Restaurant Relevant

**Five Guys national is piloting dynamic labor prediction:** they're testing an AI tool that looks at weather, local events, historical sales patterns, and the schedule to predict whether you're over/understaffed 3 days in advance. Roll-out is still quiet (not enterprise-wide), but the idea is live. When it's available to franchisees, it'll be built into the labor dashboard. 

For now: you can do this yourself with Claude. Paste your local events + weather forecast + historical sales for that date + your draft schedule into a Claude message. Ask: *"Given this forecast and history, should I add or reduce staff?"* You're doing the same analysis, manually. When FG rolls it out, you'll recognize it because you've already been thinking that way.

**Signal:** FG corporate is moving toward predictive labor. Start thinking in predictions, not reactions.

---

## 7. Skill Up — Do This Today

**Today's task (10 minutes):**

1. Find one CrunchTime performance report from this week (any category — Sales, Labor, Inventory, whatever).
2. Open Claude.
3. Copy-paste the report data into a message.
4. Prompt: *"Give me the top 3 operational changes I could make based on this data. Rank them by impact-to-effort ratio (easy wins first)."*
5. Pick ONE change. Write it down.

**What you'll notice:** Claude doesn't just regurgitate your data — it connects it to action. It asks "what does this mean?" and answers it. That's the skill. You're learning to use data as a starting point, not an endpoint.

**Tomorrow's question for you:** What change did you pick, and have you started implementing it?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail? Reply with the task, and I'll sharpen it next brief.*

---

**→ Saved to:** `C:\Users\bobby\OneDrive\BobbyWorkspace\briefs\2026-09-07-daily-brief.md`