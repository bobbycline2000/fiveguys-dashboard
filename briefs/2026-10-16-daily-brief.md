# Bobby's Daily AI Brief — 2026-10-16
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude Haiku 5.5 shipped Oct 7, and it changes the math on what you can automate for cheap. It's faster and cheaper than the previous version, which matters if you're running scheduled tasks or building repetitive workflows. For your dashboard pull jobs, your daily brief, your tip-entry automation — the cost-per-run just dropped. You don't need to do anything. Your existing automations already get the speed bump when they run against Haiku. The real play: anything that runs daily or hourly and used to feel too expensive is now genuinely lightweight. If you've been sitting on a "wouldn't it be nice if Claude could X every hour" idea, the cost barrier just got lower.

---

## 2. Prompt of the Week

**When you need Claude to turn chaotic end-of-shift notes into an action list for tomorrow's manager:**

```
You are a Five Guys shift manager's operations assistant. Your job is to take messy shift notes and turn them into a clean morning brief for the next manager.

Rules:
- Extract ONLY factual observations (what happened, what broke, what ran out)
- Flag anything that needs a decision or action — don't bury it in narrative
- Separate URGENT (fix before opening) from NORMAL (handle during shift)
- For each issue, name WHO should know (manager, owner, supplier, corporate)
- Use First names only for crew issues
- Do NOT add your own analysis — stick to what was written

Format output as:
## URGENT — Fix Before Opening
- [issue]: [who needs to know]

## Normal Operations
- [issue]: [what needs to happen by end of shift]

## Heads-Up for Tomorrow's Manager
- [pattern/observation]

Now, process these shift notes:
[PASTE NOTES HERE]
```

**Why this works:** You're teaching Claude to be a filter, not an author. The "do NOT add your own analysis" line forces Claude to stick to facts. The WHO column makes accountability explicit. The three-bucket structure means the next manager spends 30 seconds on the urgent line and doesn't have to read a wall of narrative to find it. Shift notes are usually garbage — timestamps missing, names shortened, abbreviations, thoughts mid-sentence. This prompt structure turns that garbage into a usable morning queue in one pass.

---

## 3. Use Case Spotlight

**Turn a Par Brink sales export into a shift-by-shift variance story.**

Par Brink PDFs come out as dense tables: Daypart, Items, Qty, Mix%, Sales, Labor %, Discounts, whatever. You already pull these. Here's what you're NOT doing: asking Claude to read the PDF and tell you what actually happened.

**Before (current state):**
- You open the PDF
- You skim it visually
- You notice "discount rate spiked" or "labor was weird" but you're guessing why
- You file it and move on

**After (one Claude call):**
1. Upload the Par Brink PDF to Claude (or paste the table)
2. Paste this prompt:
```
You are a QSR profit analyst. Read this Par Brink report.
Ignore the noise. Tell me:
1. Biggest variance from yesterday (sales, discount %, labor %)
2. What likely CAUSED it (daypart mix shift? promotion? staffing?)
3. One thing the manager should know for scheduling next week
Keep it to 5 bullets. Be specific (don't say "labor was high" — say "labor spiked 4% during lunch daypart").
```
3. Claude gives you a 30-second read of the business that day

You go from "I noticed some numbers" to "the discount rate jumped because we ran a Buy-2-Get-1 promo yesterday and it crushed labor during lunch." That's the difference between managing by looking and managing by reading the room.

---

## 4. Gotcha of the Week

**Claude will confidently invent numbers in summaries.**

You ask Claude: "Give me the average tip percentage from last month's employee tips data." If Claude has seen the data (you pasted it or uploaded it), it will compute correctly. But if you ask it to REMEMBER a number from a file you showed it last week, or ask it to "estimate" or "approximate" a number, Claude will produce a number that sounds reasonable and present it as fact. You'll read it into an email or a report, and it'll be completely made up.

**The fix:** Whenever you're asking Claude for a number, demand the source. "Tell me the average AND show me the calculation so I can verify it." If Claude can't show the math, it's a guess. Don't trust guesses with numbers. Run them through your spreadsheet first, or ask Claude to check against your actual data file.

---

## 5. New Tool Worth Trying

**Claude on your phone for voice memos.**

You're walking the store at 6:30 AM, something breaks, or you notice a gap in next week's schedule. Open Claude on your phone, hit the voice button (if you're on the Claude app), and say: "Voice memo: the walk-in fridge is making a grinding noise, started yesterday afternoon. Someone needs to call the tech."

Claude transcribes it, cleans it up, and drops it into your chat. 90 seconds later you have text you can forward or paste into your notes instead of typing it in a memo app.

**How to do it right now:**
1. Download Claude on your iPhone/Android if you don't have it
2. Open the app
3. Tap the microphone icon (bottom-right area)
4. Speak naturally
5. Hit send

That's it. No setup, no config, no "AI" — just voice → text that actually makes sense.

---

## 6. AI in the Wild — Restaurant Relevant

The 2026 QSR Mobile Ordering Study (released today) found that digital ordering adoption has leveled off — the gap between early adopters and laggards is now a maturity question, not a yes/no. Translation: every Five Guys probably has mobile ordering working. The operators winning now aren't the ones who have it. They're the ones who read the order data, notice patterns, and adjust staffing or menu focus based on what's actually selling through the app. That's the Claude play in QSR in 2026: the technology is table stakes. The edge is in the operator who can turn the data into decisions in real time. You're already doing that with your dashboard. Stay paranoid about keeping it fresh.

---

## 7. Skill Up — Do This Today

**Build a 2-minute Claude skill: Turn a shift handoff note into a problem list.**

You're going to practice the spotlight use case right now.

1. Grab a shift note from yesterday (or write a fake one if you don't have one handy):
   ```
   Oct 15 — 11-7 Shift
   Fries station down 1-3pm, used backup warmer
   Jeanie called in sick last minute, Bri picked up her last 3 hours
   Lady yelled about a soggy burger (remade it)
   Dishwasher acting up — had to hand-wash some stuff
   Ran out of sesame seed buns at 5:30, switched to regular
   ```

2. Paste it into Claude with this prompt:
   ```
   Turn this shift note into a 3-part operations brief:
   1. URGENT — what the morning manager needs to know
   2. STAFFING IMPACT — what labor today revealed
   3. SUPPLY/EQUIPMENT — what's broken or running low
   Keep each section to 2 bullets max.
   ```

3. Look at Claude's output. Does it match the facts you wrote? Is it cleaner and faster to read than the raw note?

**Your question for next time:** How would your week change if you had this kind of breakdown every morning instead of mentally parsing handoff notes?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
