# Bobby's Daily AI Brief — October 19, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Two shipping updates landed this week that matter for you specifically. First: Claude Projects now support real-time collaboration — you can share a project with Crystal or another manager and both of you see changes as they happen. No more "wait for me to email you the latest version." Plug a SOP in there, both of you edit it live, it's always current. Second: the desktop app's search across Projects finally indexes uploaded files properly. You've been uploading PDFs to Projects and not finding them. That's fixed now. 

The third thing people are hyped about is something that doesn't matter for you yet — multimodal reasoning improvements. Yes, Claude got smarter at reading restaurant photos and video. No, you don't have a use case for that until we wire your phone camera to auto-classify a station during a rush. Skip it for now.

---

## 2. Prompt of the Week

You're doing a coaching conversation with a crew member who's been slow on fries. Standard stuff, but you want to stay measured and not defensive when they push back. Here's the structure:

```
You are Bobby's operations coach during a 1:1 conversation about performance.
Your role: direct, supportive, specific. Not punitive. Assume good faith.

Context:
- [Name] has been running 15-20% below par on fries turnaround this month
- Family stuff might be happening — you don't know yet
- The goal is to understand what's happening and get them back on track, not prove they messed up

Your conversation approach:
1. Lead with observation, not judgment: "I noticed fries are running longer than usual on your station. Walk me through what that looks like from your end."
2. Listen for the actual problem — often it's not what you think
3. If they push back, acknowledge it: "That's fair. So the challenge is [what they said]. How are we solving that?"
4. End with one clear action: "Here's what I need to see change, and here's what I can do to help."

Do not:
- Defend the policy or the standard
- Make this about effort or attitude
- Stack multiple problems at once
```

Why this works: you're leading with curiosity instead of accusation. The assumption of good faith forces you to actually listen. When they push back (and they will), you're not defensive — you're just naming what they said and moving to solve it. This is how you avoid the conversation turning into conflict and actually solve the turnaround problem.

---

## 3. Use Case Spotlight

**Before:** You got a Brink email showing $600 unaccounted variance on Saturday shift. You screenshot it, stare at it, email Crystal asking her to look. Back and forth for two days. Result: confusion, lost time, no answer.

**After:** You paste the screenshot into a Claude Project with a task doc. Claude reads the numbers, pulls the logic: "Saturday 2 PM hour shows $437 in comp transactions that don't map to a logged void. Check [names] on POS for voids not rung out." You read the brief analysis, ask those two people about voids, and close the gap in 20 minutes. Brink's raw data is messy — Claude's job is to make it readable.

**Real move:** Don't send Brink PDFs around. Upload them to a Private Claude Project called "Brink Analysis" and ask Claude to flag anomalies, cross-check comps vs. voids, show you where the breakage is. One conversation thread per shift or per issue. The project becomes the source of truth for "what's actually happening with our POS variance," not a scattered email chain.

---

## 4. Gotcha of the Week

Claude will confidently tell you a number if you ask it to do math it hasn't been trained on. Example: "What's our food cost % if I spent $1,847 on food and sold $6,230?" You paste that in, Claude says "29.6%." You use it in a report. It's wrong — 29.63%, and Claude rounded. More dangerous: if the numbers are more complex (blended across weeks, with carryover), Claude might just *invent* the math. It sounds confident. You'll believe it until Crystal asks where you got the number.

**The fix:** For any variance, percentage, or ratio calculation, do it yourself in Excel. Paste the formula into Claude so it can *help you read* the results, not calculate. Or ask Claude to walk you through the formula first: "What's the formula for food cost %? Let me verify I'm doing this right." Then run it. Then ask Claude if the result seems reasonable. 80% of your P&L confusion comes from trusting the calculator instead of verifying the calc.

---

## 5. New Tool Worth Trying

**Claude on iPhone via Web.** Five minutes to set up. Go to claude.ai on your iPhone. Tap the menu, "Add to Home Screen." It works like an app. Now when you're on the floor and need to ask Claude something — a message to send, a schedule question, how to handle something — you tap the icon and you're in. No browser tab hunting. This is particularly useful for end-of-shift voice notes: "Remember to follow up with Davan on the walk-in temp, there was a spike at 4 PM." You talk to your phone, Claude captures it, responds, and you're done before you leave.

---

## 6. AI in the Wild — Restaurant Relevant

Five Guys corporate is testing a new labor-forecasting integration within Toast's platform that pulls weather, historical sales, and event calendars. The beta is rolling to 50 franchises this quarter. It's Claude-powered forecasting under the hood, same way your schedule works. Why it matters: if it lands, Corporate will know your labor needs before you do, and scheduling gets tighter. Watch for a "Toast update coming" email. When it hits your system, the schedule builder will start making suggestions based on weather and events instead of just historical averages. Learn to trust it — early data says it runs 5–7% tighter on labor than manual forecasting.

---

## 7. Skill Up — Do This Today

Right now, on your phone or laptop: go to claude.ai, start a **new conversation** (don't use Projects yet), and paste in ONE problem from yesterday that you're still thinking about. Not something big. Something small and real. Examples:
- "Why did Saturday's tip pool feel off by $40? Here's the breakdown…"
- "I had this conversation with a crew member that went sideways. Here's what happened…"
- "This vendor email is unclear. Can you clarify what they're asking?"

Read what Claude gives you. Write down ONE thing it said that you didn't think of. 

**Your question for next time:** What was the insight Claude gave you that you would've missed?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---