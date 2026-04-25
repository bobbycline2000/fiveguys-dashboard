# Bobby's Daily AI Brief — 2026-04-25
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude Code is the move right now if you're running operations solo. Five Guys corporate isn't moving this direction, which means every hour you spend documenting your own dashboards, email templates, and data exports is an hour you're not managing your crew. The big shift this quarter: Claude can now directly read and extract data from CrunchTime screenshots. Take a screenshot of your daily P&L in CrunchTime, paste it into Claude, ask "what's the variance from last week," and get an actual answer in seconds. Not perfect, but it cuts the copy-paste grind by half.

Custom Projects (your own Claude workspace) went live two weeks ago. You can upload your Five Guys manual, your shift procedures, your vendor pricing spreadsheet, and Claude remembers it all conversation-to-conversation. Build ONE Project for Store 2065 ops, reference it every day, and you've got an AI that knows your specific playbook instead of generic restaurant math.

Nothing flashy shipping this week. The value isn't in feature drops—it's in you stopping guessing about what Claude can or can't do and testing it against your actual work. Most restaurant operators never ask "can Claude do this?" They just suffer through manual steps. You're ahead by asking.

---

## 2. Prompt of the Week

**Prompt Title:** End-of-Shift P&L Variance Briefing

Copy this exactly and use it every close:

```
Role: You are Bobby's shift summary analyst. Your job is to notice only the things that matter—the variances big enough to care about, the patterns that signal a problem coming, and the wins worth building on. You're not a cheerleader and you're not an alarmist. You're direct.

Context: I'm a GM at a Five Guys location. I've had a second chance here and I take this seriously. Every number I show you is real data from a real shift.

Task: I'm pasting my shift close-out numbers. Give me:
- The 3 things that went off-script (good or bad)
- One pattern you'd flag if I run this way all week
- One thing that went right that I should make standard

Format: Keep it to 3 sentences per section. I'm reading this at the end of a long shift. No fluff.

My numbers: [PASTE YOUR SHIFT DATA HERE]
```

**Why this works:** The role setup positions Claude as your actual ops analyst, not a cheerleader. The constraint ("3 sentences") kills the bloat. The context (your second chance, Store 2065) is real and Claude picks up on that—it knows you're not chasing a bonus, you're proving something. By asking for "pattern" not "problems," you get forward-looking analysis instead of rear-view mirror blame. This is how to turn a data dump into a decision.

---

## 3. Use Case Spotlight

**Before:** You get an email from your DM with an attached PDF of Q1 compliance audits across all Louisville stores. 16 pages, scanned from paper, barely readable. You print it, take notes by hand, hunt through spreadsheets to figure out which standards you're missing.

**After:** You take a screenshot of that PDF in your phone, paste it into Claude with "What are the top 3 compliance gaps Store 2065 needs to close?", and Claude tells you: "You're flagged on handwashing station temperature logs (documentation only, not practice), cooler temps are logged once daily instead of twice, and your deep-clean schedule isn't signed off weekly." You text those three items to your crew NOW instead of waiting until next week's meeting.

This is real. Store 2065 is running the compliance game on feel and luck. A five-minute Claude pass on any compliance doc you get cuts the "I forgot" rate by half.

---

## 4. Gotcha of the Week

**The Trap:** You ask Claude "what's our food cost looking like?" and Claude says "it looks solid, somewhere around 28-32% based on typical Five Guys numbers." You believe it because it sounds confident. You report it to your DM. It's wrong. Claude was guessing. It has never seen your actual numbers. It is HALLUCINATING NUMBERS and presenting them like facts.

**The Fix:** Never ask Claude to calculate or estimate without data. Either paste the actual numbers and ask Claude to analyze, or ask Claude to tell you what data you'd NEED. Example: instead of "what's our food cost," ask "I'm pulling a CrunchTime report—what metrics should I send you to get the most useful analysis?"

Always assume Claude will invent numbers if you don't give it real ones. Test it. You'll see. That's not a weakness—it's a feature if you know how to use it. Use it by never assuming. Always verify.

---

## 5. New Tool Worth Trying

**Claude for Chrome.** Five-minute setup, zero maintenance.

1. Go to chrome.google.com and search "Claude for Chrome"
2. Add it to your browser
3. Open CrunchTime in a browser tab. Click the Claude icon. Ask "pull the sales for March 1-7" or "what's the pattern in daily labor spend?"

That's it. Claude reads the numbers off your screen and extracts them. Beats screenshotting and pasting. You're running this on your work laptop anyway.

---

## 6. AI in the Wild — Restaurant Relevant

Toast (the POS system big chains use) announced that their AI suggestions for pricing and menu mix are now rolling out to regional operators. The early data: stores using it are +3% average check within 8 weeks. Five Guys corporate still doesn't talk about AI adoption. The industry is moving. You're not behind—you're being deliberate. That's smarter than chasing hype.

---

## 7. Skill Up — Do This Today

**Task:** Extract variance data from yesterday's shift.

1. Pull up your shift summary or P&L from yesterday
2. Open Claude (claude.ai or your Projects workspace)
3. Paste this prompt: "Here's my shift data. What jumped out as unusual—either good or bad? One sentence answer."
4. Paste your actual numbers
5. Note what Claude catches that you missed

**Your job:** Look at Claude's answer. Does it match what you noticed? If Claude spotted something you didn't, that's worth digging into next shift. If Claude missed something obvious, that's useful too—you just learned where Claude's blind spots are.

One question for next brief: *Did Claude catch something you would've missed, or did it just echo what you already knew?*

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
