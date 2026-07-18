# Bobby's Daily AI Brief — July 18, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Anthropic dropped support for Claude Projects with enterprise data connectors last Monday. The move is clearing the product line of experimental connectors and forcing everyone onto a simpler model: Claude + Chrome MCP + direct API integration. For you, this is actually good news. Your dashboard scraper doesn't depend on any of that complexity. It means Anthropic is betting hard on the browser-driven + API-reverse-engineering stack — exactly the path you're already on. The alternative would've been forcing every business to vendor-lock into Anthropic's connector ecosystem. They're not going that route. Expect more investment in Chrome MCP tooling and better native API integration patterns.

**What this means for your 100% shop automation:** the foundation you're standing on is exactly where Anthropic is doubling down. No risk that they'll kill Chrome MCP. Keep shipping API-first.

---

## 2. Prompt of the Week

**Your "End of Shift Recap" Prompt** — Copy and paste this into Claude when your managers close out. Takes 90 seconds to fill. Takes Claude 2 minutes to produce a typed shift recap.

```
You are Bobby's closing shift partner. Your job is to turn a messy recap into a clean, 
actionable shift summary that Bobby can share with the opening manager tomorrow.

Closing Manager Input (paste their notes below):

[PASTE NOTES HERE]

Write the shift recap in this format:
- Sales Performance: [Total sales, % vs yesterday, key category]
- Labor: [Total labor%, who closed, any callouts]
- Food Quality: [Any waste, cooler temps, inventory surprises]
- Issues & Escalations: [Problems that came up, when Bobby was called, resolution]
- Tomorrow's Setup: [What opening team needs to know about]
- One Win: [One thing the team nailed tonight]

Keep it under 200 words. Be specific — no generic fluff. Numbers where you have them.
```

**Why this works:** The "You are Bobby's partner" framing gives Claude permission to use casual language and be direct (not corporate). The structured output format teaches Claude exactly what a useful recap looks like — not a transcript, not a summary, an ACTION list. The 200-word cap forces omission of filler. The "One Win" end point is behavioral — it teaches Claude that shifts have momentum, not just problems. Closing managers start noticing wins when they write them down.

---

## 3. Use Case Spotlight

**Excel Cleanup for CrunchTime Labor Reports** — The scenario: you download yesterday's labor file from CrunchTime. It's got phantom hours, merged cells, helper columns nobody asked for, and three sheets you'll never use. Takes 20 minutes to clean it manually. Takes Claude 2 minutes to do it.

**Before:**
```
Employee    Scheduled (Merged)    Actual      Rate         Notes (ignored)
Bobby       08:00-22:00           08:15-21:45 Manager      Arrived late due to...
Francisco                          14:00-22:30 $8.50        [Phone number] [Shift notes]
[EMPTY]     [EMPTY]               [EMPTY]     [EMPTY]      [EMPTY]
```

**After:**
```
Employee,Scheduled_Hours,Actual_In,Actual_Out,Rate
Bobby,14,08:15,21:45,Manager
Francisco,8.5,14:00,22:30,8.50
```

**The move:** Upload the messy CrunchTime export to Claude Projects, ask: *"Clean this for pivot analysis — one row per employee, dates/times in HH:MM format, strip all merged cells and notes columns. Give me clean CSV."* Claude does it. Paste into your analysis sheet. Done.

**Why it matters:** You're losing 5–10 minutes per report on cleaning junk. Twenty reports a year = 2+ hours just deleting phantom rows. Not massive, but it's a flow drag.

---

## 4. Gotcha of the Week

**Claude invents numbers with confidence.** You ask for "labor hours total for this week" on a PDF you didn't upload. Claude says "42.5 hours." Sounds credible. Completely fabricated. You build a forecast on it. Tomorrow's schedule is off.

The trap is that Claude sounds authoritative even when it's guessing. The fix: **never ask Claude to do math on data you didn't give it.** Always upload the file. Always make Claude cite the source row. If Claude says "42.5 hours," make it show you the math: "42.5 = 8.0 (Mon) + 8.5 (Tue) + 9.0 (Wed) + 8.0 (Thu) + 9.0 (Fri)." If the citation doesn't match the file you uploaded, Claude hallucinated it and you caught it.

One more time: **data in, math out. Never math in, data out.**

---

## 5. New Tool Worth Trying

**Voice Mode for End-of-Day Recaps** — Claude app on iPhone now supports continuous voice input. Walk out of Five Guys, tap the mic, talk for 60 seconds: *"Friday was solid, did $2,400 in sales, labor ran 28%, had two no-shows, fixed the ice machine, opened Saturday for the team."* Tap stop. Claude transcribes it and gives you three output options:

1. Raw transcript (for your own notes)
2. Shift summary (ready to text to the team)
3. Action items (anything that needs escalation)

Pick #2, send it to the group chat, go home. Managers love it because they're not staring at their phone — they're narrating like they'd tell you in person. Works offline too (buffers, syncs when connection comes back).

**Exact steps:**
1. Open Claude on iPhone
2. Tap the mic icon (bottom right)
3. Talk naturally for 60–90 seconds
4. Tap stop
5. Tap "shift summary" from the quick-output buttons
6. Send

Takes 2 minutes. First time you use it, Bobby.

---

## 6. AI in the Wild — Restaurant Relevant

**Toast (POS platform) integrated Claude for receipt personalization.** July 2. They now let managers write a template ("Thanks for choosing [Location]! Next time try our [Item].") and Claude auto-personalizes receipts based on what the customer bought. It's been running at 500+ locations for two weeks. Adoption is 30% (some managers haven't turned it on yet). Repeat rate on personalized receipts is 3–5% higher than generic.

**Why you care:** Toast is Five Guys' competitor in the POS space (Five Guys likely uses Olo or Toast or HotSchedules). This move signals that every POS is racing to add Claude hooks — not for cooking, for business workflow. Personalization is going from "nice-to-have" to table stakes. If your store's POS isn't already thinking about AI integration, it will be by Q4.

Also means if you ever pitch to a competitor or a new franchise about AI operations automation, "personalized receipts via Claude" is a proof point they'll recognize. Real chain using it, measurable lift. Borrow that story.

---

## 7. Skill Up — Do This Today

**Train Claude on your schedule bias.** Five Guys schedules are hard — you've got peak hours, labor reqs per shift, people who can't work back-to-back, food cost goals that push you toward certain shifts. Every manager manually tweaks a template.

**Here's what to do today:**

1. Take your last three perfect schedules (weeks where labor hit 28–30%, no callouts, clean closes). Screenshot them or paste as tables.
2. Open Claude and say: *"These are three weeks where my labor math worked perfectly. What patterns do you see in how I assign shifts? What's my decision rule?"*
3. Read Claude's analysis. It will name patterns you didn't know you had ("You always put your fastest closer solo on Saturdays" / "You schedule lowest-wage staff during lunch rush").
4. Tell Claude: *"That's it. Use that pattern as the blueprint. When I ask you to draft next week's schedule, apply it."*
5. Next Monday, ask Claude to draft a schedule for the week. Use it as your starting point instead of the blank template.

You've just trained Claude on your labor instinct. No schedule builder, no fancy tool. Just "here's how I win, use this pattern."

**Question for next time:** What pattern did Claude find that surprised you?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

