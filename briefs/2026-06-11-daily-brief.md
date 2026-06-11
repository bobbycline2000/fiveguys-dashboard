# Bobby's Daily AI Brief — June 11, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Two things shipped: **Claude Fable 5** and **Opus 4.8** (the fastest tier). You don't need either. Stick with what you have. Fable is for developers building AI products. Opus is your current baseline—it's rock solid and it's what you'll keep using. The real story is that Claude just cleared a threshold: it now runs natively in Slack and Gmail (your actual work email), which means you can prompt it without leaving your inbox. That's useful. No setup. Just type `@claude` in Slack or hit the Claude button in Gmail when you're looking at an email from a vendor or a team member. Use case: you get a wall-of-text vendor contract at 2 PM on Friday—pop it in Gmail, ask Claude to flag the three things that hurt you most. Done in 30 seconds. No copy-paste. That's worth trying today.

## 2. Prompt of the Week

Use this exact prompt when you're coaching a crew member through a task or discipline conversation. Paste it as-is. Don't edit it first.

```
You are Bobby, the General Manager at a Five Guys location in Louisville, KY. 
You are coaching [PERSON'S NAME] on [SPECIFIC BEHAVIOR—e.g., "why food waste jumped 
12% this week" or "why the 6 PM rush handoff was messy yesterday"].

Start with CURIOSITY, not accusation. Open with: "Walk me through what happened when..."
Then listen. Don't interrupt. If they get defensive, validate the constraint they felt
("that makes sense—you were alone and it was slammed").

Only after you understand their side, name the standard: "Here's what I need going forward..."
End with COMMITMENT, not compliance: "What support do you need to hit this?"

Generate a coaching conversation script. Make it sound like you, not a corporate module.
Make it 6-8 exchanges. Assume they're good at their job; they had a bad moment.
```

**Why this works:** The prompt gives Claude a role (you), context (the specific problem), and a structure (curiosity → validation → standard → commitment). That structure is the discipline model that actually sticks—it's not "you messed up," it's "here's what I need and how I'll help." Claude learns to ask clarifying questions first because the prompt tells it to. It models respect. And it gives you words you can actually say instead of the corporate-speak that makes your crew tune out.

## 3. Use Case Spotlight

**The Mess:** Par Brink sends you a PDF report every day with sales, labor, discounts. It's a wall of numbers. You skim it, maybe miss that breakfast sales dropped 18% Tuesday. Or you see the problem but don't know *why*—was it short-staffed? Weather? Bad batch?

**The Claude Move:** Upload that daily Par Brink PDF to Claude (or paste the data), ask: "What changed today? Flag anything that's worse than the last 3 days." Claude reads it in 2 seconds, compares patterns, and tells you: "Breakfast sales down 18% (vs. avg 2,400 to 1,965), labor % flat, ticket count down 22%. Likely traffic drop, not speed. Weather or local event?"

**Now you know what to investigate.** You don't waste time re-reading a PDF. You spend 3 minutes on the root cause instead of 15 minutes on the data.

## 4. Gotcha of the Week

**The Trap:** Asking Claude a vague question and acting on the vague answer.

Example: "What should I pay my crew?" Claude will say something confident like "Market rate is $7.50–$8.50" and you'll think it knows your Louisville market, your rent, your food cost, your local Five Guys standard. It doesn't. It's generalizing.

**The Fix:** Be specific. "I'm at Five Guys in Louisville, KY. Entry crew starts at $8.15. I want to raise it. What's the risk if I jump to $8.75 vs. $8.50 given that labor is 27% of my revenue and I can't cut hours?" Now Claude can actually help. It's not guessing. It has the constraints.

**Apply this everywhere:** Never ask Claude "what should I do?" Always ask "given X constraint and Y goal, what are the tradeoffs?" The difference is the difference between a guess and advice.

## 5. New Tool Worth Trying

**Claude for Chrome** (if you haven't activated it). Takes 2 minutes.

1. Go to Chrome Web Store, search "Claude for Chrome"
2. Click Add. Chrome will ask for permissions (clipboard, current page).
3. Grant them.
4. Now, when you're on any website (CrunchTime, your Outlook, a vendor site), click the Claude icon in the top right.
5. Ask Claude about what's on the page: "What's my labor % this week?" or "Does this email have any red flags?"

**First thing to try:** Open CrunchTime, click the Claude icon, ask "What was my food cost last week?" Claude reads the visible data and answers without you typing anything. That's the power of having Claude see what you see on screen.

## 6. AI in the Wild — Restaurant Relevant

Cava (the fast-casual chain) just announced they're hiring 2,500 crew members nationwide. Not newsworthy by itself—until you hear *why*: They're expanding because their scheduling and labor systems (powered by AI-optimized tools like Toast and Olo) let them run thinner management layers. One GM can run a tighter ship with better data. Better data = less waste = cheaper to add a location. You're not competing with Cava yet, but the trend is clear: restaurants that adopt data and AI first are the ones adding locations and taking market share. Every time you build a automation (like the safe drawer log or the daily brief), you're doing the same math Cava is—you're compressing the time it takes to know what's broken, which compresses the time it takes to fix it. That compounds into a faster-moving, more profitable operation.

## 7. Skill Up — Do This Today

**The Task:** Audit one week of your Par Brink labor report.

1. Download or screencap your last 7 days of labor data from Par Brink.
2. Paste it into Claude and ask: "Show me the three days with the highest labor %, the three days with the lowest. What's the spread? What changed between the high days and low days?"
3. Claude will highlight patterns you'd miss in a manual read.
4. Look for the low-labor days and ask: "What was different about [Day]? Same crew size? Fewer transactions? Better speed?"

**Your question for next time:** What day this week had your best labor efficiency, and what do you think the crew did differently that day?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---
