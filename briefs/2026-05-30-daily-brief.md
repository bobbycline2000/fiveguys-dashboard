# Bobby's Daily AI Brief — May 30, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude Opus 4.8 shipped on May 28, and the headline isn't flashy but it's real: cheaper fast mode (3× cost reduction), effort-control sliders so you can dial down thinking depth for quick answers, and "dynamic workflows" in Claude Code that can break huge problems into parallel steps. 

What this means for you: Fast mode got cheaper right when you need to run a lot of daily scrapers and dashboard rebuilds. The effort control is a dial you'll use in the brief-generation workflow — you don't need full reasoning overhead to extract P&L variance, you need speed. Worth testing on CrunchTime extracts this week.

Also shipping: KPMG just embedded Claude into their entire software stack for tax and legal work — 276,000 people using it daily now. The pattern matters: when a large org locks in Claude as "the tool we use for X," that's the adoption arc Five Guys franchising could follow if you nail the operations side.

---

## 2. Prompt of the Week

Use this prompt for end-of-shift recaps with your managers (especially useful for onboarding training or debrief Fridays):

```
You are a Five Guys operations coach reviewing a shift recap from a manager. Your job is to:
1. Extract the three key metrics: what went right, what went wrong, what's the fix
2. Avoid generic advice. Tie every suggestion back to ACTUAL Five Guys numbers/systems (labor%, food cost%, order accuracy)
3. Ask ONE follow-up question that forces the manager to think ahead to tomorrow's shift

Here's the shift recap:
[PASTE MANAGER'S NOTES]

Give me a tight debrief in three sections:
## What Worked
## What Didn't  
## Tomorrow's Play

Then ask your one question.
```

Why this works: This prompt role-plays the coach mindset you want your DMs and GMs to internalize — not "did it go OK," but "did we move the needle on the metrics that matter?" The one-question rule forces the manager to translate feedback into action, not just nod. Five Guys operations are measurement-driven; this prompt teaches that rhythm.

---

## 3. Use Case Spotlight

**Before:** Your GM sends you a text thread of seven messages recapping the lunch rush: "Labor was high," "Fries burnt twice," "Phone orders backed up," "new hire struggled on the register." You read it, remember fragments, move on.

**After:** You paste those seven text messages into Claude with the shift-recap prompt above. Output: Three bullet points under "What Didn't" pinpoint that phone-order backlog is YOUR labor-staffing gap (not a training issue), burnt fries suggest the fry station needs a second person during peak, and the new hire's register speed is a hand-job task not a discipline issue. You reply with a one-sentence fix: "Move Brooklyn to phone support during 11–1 lunch rush starting Monday."

Result: One shift, three data points, one precise fix. Not platitudes. Not guessing.

This pattern works for any chaotic input — email threads, voice memos, handwritten notes, Slack dumps — that needs to become a decision. Claude is the parsing layer between chaos and clarity.

---

## 4. Gotcha of the Week

**The trap:** You ask Claude, "What should our labor percentage be?" Claude says, "Industry standard is 28–32%" and cites a restaurant management website. You trust it, benchmark your 34% against the industry number, and worry you're over.

**The failure:** Five Guys at KY-2065 with Bobby in the role of GM is NOT the same as "industry average." Your store's labor % is a function of: traffic mix, how many high-wage crew you kept vs. paid off, whether you're running 100% or 85% staffed, local wage pressure in Louisville, and what metrics your own profit model actually requires. Industry averages are noise for Bobby's decision.

**The fix:** Never ask Claude for "industry standard" numbers without stating YOUR actual constraints first. Instead: "My CrunchTime shows 35% labor on weeks I do $32k sales. My food cost is 28%. What's the margin picture?" Now Claude can math your actual numbers and give you an answer that applies to STORE 2065, not to "restaurants in general."

Claude's good at reasoning within YOUR reality. It's bad at guessing what reality is.

---

## 5. New Tool Worth Trying

**Claude Projects just got better for operator playbooks.**

In claude.ai, hit "+ New Project" → name it "Five Guys 2065 Ops Playbook" → drag in:
- Your P&L template (Excel)
- Your CrunchTime manual-export sample (PDF or spreadsheet)
- Any SOP docs you've written (PDFs)
- Last week's brief (markdown)

Then in the chat, ask: "What's the pattern in my labor % trend?" or "Where's my biggest variance to last month?" Claude reads all the files at once and answers against YOUR actual data, not generic restaurants.

**Time to set up:** 3 minutes. Payoff: One reference source for all your analysis, no more "where did that number come from."

---

## 6. AI in the Wild — Restaurant Relevant

Five Guys just extended its partnership with SoundHound AI after hitting 1 million AI-driven phone orders. The bot is now answering 100% of incoming calls during peak hours, never missing an order, and handling questions about allergens, promotions, and menu items—all while talking like a human.

**What this means:** SoundHound trained its voice model on Five Guys' menu and speech patterns. Every call the bot fields is one less ring that interrupts your crew. The franchise found that voice AI isn't a "nice to have"—it's labor arbitrage. One bot replaces 0.5 FTE (full-time equivalent) of phone-order staff.

**The story underneath:** When Five Guys corporate invests in voice AI across 1,500+ locations, that's not "tech for tech's sake." That's franchise economics. Labor shortage + thin margins = capital (robots, AI) replaces labor (crew). The franchise wins. The crew who now isn't doing 8 hours of transcription can do 8 hours of prepping or customer service (higher-touch work). That's the operational trade Bobby should think about: where is crew doing repetitive intake work that a bot could own?

**For Bobby:** If you've got 2065's phone order volume documented in CrunchTime, you can calculate your own labor-savings ROI for voice AI. It's not "fancy tech." It's margin defense in a tight labor market.

---

## 7. Skill Up — Do This Today

Pick any text your managers sent you this week (an email, a Slack message, a shift note, a complaint). Paste it into Claude and ask:

```
Rewrite this as a numbered action plan with one owner and one deadline for each item.
```

Do it once. Notice what Claude extracts as action vs. what was just venting. What did Claude add? What did you have to clean up?

**Your question for next brief:** Did Claude miss anything, or did it surface stuff you'd been living with but not saying out loud?

---

*One ask: What's one thing you wanted Claude to do for you this week that it didn't quite nail?*

---

**Generated:** 2026-05-30 at 1:26 PM ET | Source: Anthropic news (May 2026), QSR industry reports, Five Guys partnership data
