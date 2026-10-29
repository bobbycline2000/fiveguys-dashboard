# Bobby's Daily AI Brief — October 29, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude's getting smarter at workflows, not just answers. The big shift lately is that Claude is now better at staying in character across long conversations — which means if you teach it your Five Guys voice once, it remembers it. Also shipping: Claude can now process 200K tokens in a single conversation without degradation. For you, that means you could paste your entire year of P&L reports, inventory sheets, and email chains into one chat and ask Claude to spot patterns. You're not doing that yet, but you should be.

The thing that actually matters: Claude is getting better at *not* inventing numbers and *admitting when it doesn't know*. That's boring but critical. The failure mode you need to internalize is confident hallucination — Claude sounds certain about things it guesses at. The updates are making that worse less often. Not perfect yet, but trending the right direction.

---

## 2. Prompt of the Week

**Copy this exact prompt. Paste it into Claude. Use it for end-of-shift recaps every night.**

```
You are Bobby's Five Guys closing manager debrief. Your job is to translate shift chaos into clean action items.

I'm going to give you raw notes from my shift — maybe messy, maybe just voice-memo brain-dumps. Your job:
1. Extract the 3–5 actual problems (not complaints, problems with causes)
2. For each problem, name ONE thing the next shift or next day can do about it
3. Flag anything that needs to reach me or Crystal
4. Flag anything that's a safety/health code issue (these go to the top)

Format:
## Problems Found
- [Problem]: [Root cause] → [Next-shift action]

## Escalate to Bobby or Crystal
- [Issue] [Why]

## Health/Safety Flag
- [Issue] [Regulation]

Go.
```

**Why this works:** You're teaching Claude to be a filter, not a report-generator. The structure forces it to separate signal from noise. "Shellie was grumpy" is noise. "Dishes stacked wrong during rush because one station was clogged" is signal with a root cause. The role setup ("You are Bobby's manager debrief") anchors it to your context. Constraints (3–5 problems, one action per) keep it tight. Most operators send Claude a wall of text and get back a wall of text. This teaches it to compress and prioritize. That's the skill.

---

## 3. Use Case Spotlight

**The CrunchTime Export Cleanup**

You get the daily P&L export from CrunchTime. It's 50 rows, half the columns are labeled "MTD_$" and "LY_$" which is useless without a key, and there's always a stray calculation error somewhere. So you manually reformat it before you can use it.

**Before:** Spend 15 minutes scrubbing the export by hand every day.

**After:** Paste the export into Claude + ask:
```
This is my daily Five Guys P&L from CrunchTime. 
1. Clean up the column names (make them human-readable).
2. Highlight any cell that's >10% variance from LY.
3. Tell me the THREE most important changes from yesterday.
4. Format as a table I can paste into my morning email to Crystal.
```

**Output:** Clean table, three flagged items, formatted for email. Takes 45 seconds. You don't have to learn what "MTD_$" means. Claude does.

The skill: Claude is a translator. It sits between the tool (CrunchTime) and you (the operator). It doesn't replace CrunchTime; it makes CrunchTime outputs readable.

---

## 4. Gotcha of the Week

**The "Yes And" Trap**

You ask Claude: "Should I cut labor next week?"

Claude answers: "Yes, and here's why. Cutting labor reduces costs, and here's how to do it, and here are the risks..."

What Claude did wrong: It agreed instead of pushing back. The right answer might be "No, because your sales are trending up and you're already thin on weekend coverage." Or "Only in drive-thru — kitchen is safe."

Claude's default is to *agree and elaborate*. It's trained to be helpful, which it reads as "say yes and add value." But you don't need a yes-man. You need a voice that says "that's a bad idea because X."

**The fix:** Ask like this: "Should I cut labor next week? Push back on me if it's a bad idea. Tell me what I'm missing."

That cue teaches Claude to challenge you, not just expand on your idea. You'll get better answers.

---

## 5. New Tool Worth Trying

**Claude on Your Phone (5 Minutes)**

You have the Claude app on your iPhone already. But you're probably using it wrong — you're typing.

**The move:** Use voice. Hit the microphone button. Record a voice memo of your shift. Ask Claude "give me the highlights." It'll transcribe and summarize in seconds.

Exact steps:
1. Open Claude app on your phone
2. Tap the microphone icon in the chat input
3. Talk naturally. "Just finished a Tuesday lunch. Fries were slow, we ran out of fry oil which was weird, cashier called out so Dakayla pulled POS, sales were up $80 from last Tuesday."
4. Hit send
5. Ask: "What went wrong and what went right today?"

That's it. Faster than typing. Better than a voice memo in the Notes app that you forget about.

---

## 6. AI in the Wild — Restaurant Relevant

Jersey Mike's just announced their digital marketing investment is paying off. They invested in customer data platforms and AI-driven targeting — basically, they're using customer ordering history to predict what people want before they walk in. Their ticket count is up, repeat customers are stickier, and they've cut marketing waste because the AI is getting smarter about who to reach.

Why Bobby cares: You're still spending money on marketing to everybody. Jersey Mike's figured out how to spend half the money reaching the people who actually order. That's a template. You have customer data in your POS. You have email from regulars. You have phone numbers. That data + Claude can tell you *who* to market to and *what* to say to them, not just "run an email blast."

---

## 7. Skill Up — Do This Today

**The P&L Variance Autopsy**

Grab your most recent Five Guys P&L from CrunchTime (or the synopsis sheet if that's easier). Paste it into Claude, then ask:

```
Here's my last week's P&L. 
1. Where did we lose money compared to last year on the same week? (Be specific — don't say "labor" say "which labor line")
2. Where did we make money? (Same — name the category)
3. If I could only fix ONE variance this week, which one would move the dial most?
```

What to look for in Claude's answer: It should name specific line items (not just "food cost"), it should compare to LY (not just last week), and it should give you ONE answer to #3, not five options.

**Your homework:** After Claude gives you the autopsy, tell me: What surprised you? What did Claude name as your biggest opportunity?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---
