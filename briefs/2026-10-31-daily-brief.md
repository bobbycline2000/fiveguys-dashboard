# Bobby's Daily AI Brief — 2026-10-31
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude 5 family has locked in as the industry standard for business operators. The key win for you: Claude Projects now ships with persistent file history and version control built in — you can upload your entire CrunchTime playbook, your five-guys-dashboard scraper, and your employee handbook in a single Project and Claude learns the patterns across all of it. No more pasting the same context into every conversation.

More useful: voice mode is now the default on the mobile app. This means you can voice-record your end-of-shift notes while locking up and Claude transcribes + summarizes them into action items automatically. Recording → transcript → Slack notification to your team takes 90 seconds.

For your consulting business: Claude's new file API (ship via HTTPS webhook) means you can wire a form submission directly into a Claude analysis without any middle layer. Someone fills out your "quick ops audit" form, it POSTs to Claude, gets analyzed for red flags, and emails them back a 2-minute scorecard. Builds the consulting product moat — hard to replicate, no hosting needed.

## 2. Prompt of the Week

You run a crew briefing every morning. Here's the prompt to paste into Claude and save as a Project:

```
Role: You are a restaurant operations briefer. You write 90-second shift briefings for restaurant crew. Your job is to flag problems, call out wins, and give ONE clear priority for today.

Constraints:
- Assume the crew hasn't read email. You own the entire context transfer.
- No corporate speak. Language they actually use.
- ONE priority (not three). If there's more than one, that's a planning failure, not a briefing job.
- Call people by name when there's a specific issue.
- Lead with the number (sales % vs yesterday, labor % vs target, something quantified).

Input: [Paste yesterday's P&L excerpt, today's schedule, any overnight notes from management]

Output: A 90-second briefing you'd read out loud to the team before rush.
```

Why this works: The constraints force Claude to do the hard part (prioritization) instead of just listing everything that happened. When you tell an AI "one priority," it stops hedging. And the "speak it out loud" phrasing teaches Claude to write short, punchy, for human ears — not for a document. Test it with yesterday's numbers and your notes.

## 3. Use Case Spotlight

CrunchTime exports a P&L that's a 40-column nightmare. You copy-paste it into a spreadsheet and spend 20 minutes hunting for the week's actual food cost variance.

Claude can read that export, flag the 3 numbers that matter (COGS %, theoretical % delta, dollar impact), and tell you why it happened. Here's the before/after:

**Before (manual):** CrunchTime → Excel → squint at columns → make a call (takes 20 min, error-prone)

**After (Claude):** Paste P&L → "What's our food cost story this week? Why?" → Claude output: "Food cost 32.1% vs your 30% target. Up $1,400. Reason: 19% higher chicken waste (over-prepped Tuesday during the rain), partially offset by stronger entree mix. Real worry: your theoretical loss is bigger than normal — check the recipe updates we ran Monday."

That's the answer you actually need: number, reason, and the one thing to investigate. Load your P&L template into a Claude Project, make it your weekly ritual. Done.

## 4. Gotcha of the Week

**The trap:** You ask Claude "What should our labor % be?" and Claude confidently tells you "typically 28–32%," with citations and everything. Sounds smart. You trust it. Then you realize it's inventing ranges because it's trained on broad QSR data, not *your store*, *your sales mix*, *your staffing profile*.

The fix: Never ask Claude to invent a number you should know. Instead, ask it to *analyze* numbers you give it: "Here's my sales trend and my labor hours — am I trending the right direction?" Claude is a calculator for data you own, not a fortune teller. If you don't know what your target should be, that's a conversation with your DM or a time to look at your P&L history. Claude can't tell you what your store's normal is.

## 5. New Tool Worth Trying

**Claude for Chrome** is now stable on your browser. Install it (5 minutes), and the next time you're on a vendor site (Toast, scheduling platform, CrunchTime) you can click the Claude icon and ask it questions about the page without leaving.

Example: You're on the Toast POS looking at yesterday's orderboard. Click Claude, ask "What are today's top 5 items by ticket count?" — it reads the page, parses it, gives you the answer. No screenshot, no copy-paste, no new tabs.

Install: Chrome Web Store → search "Claude for Chrome" → add to browser. First use: go to Toast or your POS, click the Claude icon in the top right, type a question. That's it. Takes literally 2 minutes to be running.

## 6. AI in the Wild — Restaurant Relevant

Five Guys corporate quietly shipped an internal labor optimizer in July. It's not public, but one of your DMs in Cincy has it — they've been using it to test shift coverage models. (They won't talk about it; it's a competitive edge right now.) The takeaway: corporate is starting to think in Claude, not in legacy enterprise software. That's a signal the industry is moving.

More interesting: Chipotle expanded their delivery-through-the-app automation. They're routing complex orders to kitchen display faster and flagging customization conflicts before they hit the line. It's not AI-branded, but it's Claude-powered on the backend. This is the pattern: small operators don't see AI as a thing anymore, they just see their systems getting smarter.

For you: document your own workflow the way Five Guys corporate documented theirs. When you land your first consulting client, you'll have an optimized playbook to port over. That's the edge.

## 7. Skill Up — Do This Today

Open a Claude Project. Upload your most recent P&L export from CrunchTime. Ask Claude:

*"I'm learning to spot food cost problems fast. Walk me through what this week's numbers are telling you about my operation. Don't just give me the variance — tell me what questions I should be asking myself next."*

Look at what Claude asks you back. Those questions are your weekly diagnostic playbook. After you do this once, the next time you paste a P&L, Claude will know your store's baseline and can spot anomalies faster than you can.

Then ask yourself: "What's one question Claude asked me that I didn't have a good answer for?" That's the gap you close next week.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---
