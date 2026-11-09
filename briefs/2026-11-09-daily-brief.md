# Bobby's Daily AI Brief — 2026-11-09
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

### 1. This Week in Claude — Plain English

Claude got faster last month — the new inference optimization cut response time by ~25% on average. More important for you: Claude on iPhone works offline now. That means voice memos on shift, no data plan needed. You close the store, punch in a voice note on your phone ("ticket waste was high Friday, need to check broiler times"), and Claude transcribes + organizes it while you're driving home. No more "I'll write that down tomorrow." It's consumer-grade now, not beta.

The skip-on-this: every tech blog is talking about "multi-modal reasoning." Bobby, that's code for "Claude can see pictures better." Useful if you're running OCR on vendor invoices (you could be), but it's not the thing that changes your labor numbers tomorrow.

---

### 2. Prompt of the Week

You're going to coach a crew member this week. Maybe it's slowing down, maybe they're making mistakes, maybe they're drifting in a position. Instead of winging it, paste this into Claude and let it walk you through the conversation:

```
Role: You are a restaurant coach helping a GM have a difficult conversation with a crew member who is struggling in their role.

Scenario: [DESCRIBE THE SITUATION — e.g., "Fridays they're slow on fries, missing rushes, customer complaints up"]

Before the conversation, I need a plan. Give me:
1. What's the root cause question I should ask first (not a criticism, a question that makes them think)
2. Three things they might say — and how to respond to each one
3. One thing I should be careful NOT to do (the mistake that kills the conversation)
4. A one-sentence close that tells them exactly what happens next

Then draft the opening sentence I should use.
```

Why this works: You're not winging the hard conversation — you're learning what a structured coach does. Claude's responses teach you the *shape* of these talks (open with curiosity, not criticism; find the real problem, not the surface one; commit to next steps). After a few of these, you'll do it without Claude. That's the goal.

---

### 3. Use Case Spotlight

**Before:** You get the CrunchTime P&L email every week. It's a PDF. You read it, maybe you screenshot it, maybe you paste it into a chat tool and ask Claude what's wrong. Takes 10 minutes. You miss the second-order stuff.

**After:** You upload the PDF to Claude Projects (takes 30 seconds), save it in a project folder called "Weekly P&L," and give Claude one standing instruction: *"Every time I upload a new P&L, tell me: (1) the number that's worst vs. last week, (2) the one action that would swing it most, (3) one way I'm probably being too hard on myself about it."*

Then you ask Claude the PDF question once, it remembers the context, and next week's P&L conversation is instant — Claude knows your store's baseline and doesn't make you re-explain. That's what Projects is for.

---

### 4. Gotcha of the Week

Claude will confidently invent numbers when it doesn't know them.

You ask: *"What's the food cost percentage for a Five Guys location running $45k in weekly sales?"*

Claude answers: *"Typically around 28–30% depending on location efficiency."*

That sounds credible. It's completely made up. Your actual food cost is different. Your store's numbers are different. If you copy that 28% into a forecast without verifying it against *your* P&L, you're planning off a hallucination.

Fix: Whenever Claude gives you a number you haven't verified yourself — labor percentage, food cost range, labor hours per dollar of sales — treat it as a guess. Ask it: *"Where did you get that from?"* If it says "industry averages" or "typically," that's a red flag. Always anchor to your own data. If you don't have your own data, say so to Claude and ask it to help you find it instead.

---

### 5. New Tool Worth Trying

Claude for Chrome — five-minute activation.

1. Open Chrome
2. Go to `chrome://extensions/`
3. Paste this into the search box: `Anthropic` (or just browse for it — should be right there)
4. Click the Claude for Chrome extension and pin it to your toolbar
5. Walk to any website — your CrunchTime login page, your vendor's ordering form, your daily scorecard spreadsheet — and click the Claude icon. It reads the page in context.

First thing to try: open your CrunchTime Performance Metrics page, click Claude, and ask it *"What's the weirdest thing about today's numbers?"* It'll see your actual data and call out outliers. Beats scrolling.

---

### 6. AI in the Wild — Restaurant Relevant

Toast (the POS you don't use, but your QSR neighbors do) just shipped an AI order forecasting layer. Restaurants can now ask their POS system to predict Friday's ticket count based on weather, past Fridays, and staffing patterns. Toast is bundling it — no extra subscription yet. It's not revolutionary, but it matters: you're moving from "we're always understaffed Friday" to "staff THIS much because Friday prediction is 310 tickets." Competitor intelligence: if another Five Guys location starts running tighter labor on Fridays, they're probably doing something like this.

---

### 7. Skill Up — Do This Today

Open Claude. Paste in yesterday's sales numbers from CrunchTime or your POS — just the raw row: *"Saturday: $12,340 sales, $3,100 labor, 45 tickets, 15% food cost, 2 complimentary tickets."*

Ask Claude: *"I'm going to show you my numbers every week. Learn what 'normal' looks like for my store, then flag anything that's weird. Here's this week."*

Then ask: *"What's one thing I should check?"*

Don't get the right answer. Get Claude to START ASKING YOU QUESTIONS about your baseline. The question it asks you (something like "Is 15% food cost typical for you?" or "Was Saturday unusually slow?") is where the learning happens.

**Your question for next brief:** What did Claude ask you that made you think differently about your numbers?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
