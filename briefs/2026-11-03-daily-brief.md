# Bobby's Daily AI Brief — November 3, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude Code just dropped multimodal editing in the terminal — you can now paste a screenshot directly and ask Claude to identify what you're looking at without leaving your workflow. For you: snap a photo of your Par Brink dashboard, dump it in the terminal, ask "what's the variance here," and get an instant read. No more hunting for the Excel export or trying to remember what the numbers were. It's the equivalent of having someone who actually knows restaurants look over your shoulder.

The bigger move: Claude's voice mode now supports restaurant language better. Shift recaps, voicemail transcription, even coaching conversations — the model's gotten sharper about domain-specific vocabulary. Still not perfect on industry jargon, but the delta is real.

---

## 2. Prompt of the Week

**Coaching a team member on tip-out inconsistency**

Copy and paste this into Claude:

```
You are a restaurant GM writing a coaching conversation with a crew member about their tip-out accuracy. The employee has been inconsistent — sometimes accurate, sometimes off by $5–20. You want them to understand why this matters (compliance, fairness to other crew, P&L visibility) without being punitive.

Write a 2–3 minute conversation script that:
1. Opens with a non-accusatory observation ("I noticed the tip-out totals varied last week")
2. Explains the why in their language, not compliance-speak
3. Gets them to commit to one simple fix (e.g., count twice, use the same calculator)
4. Closes with a positive next step

Keep it conversational. Make it sound like you, not an HR department.
```

**Why this works:** The role setup tells Claude you're a coach, not a judge. The constraints (2–3 min, their language) force conciseness. The "explain the why" step is crucial — crew members care about fairness and their own accuracy more than "compliance"; Claude picks that up from the framing and adjusts tone. You'll get something you can actually say without sounding like you're reading a script.

---

## 3. Use Case Spotlight — Cleaning Up a CrunchTime Export

**The mess:** You pull a Labor Report from CrunchTime for the week. 47 rows, half the fields are formatted wrong, pay codes are abbreviated in ways only the system knows, and you need to send this to Crystal for the payroll tab.

**Before Claude:** Spend 20 minutes hand-fixing cells, looking up pay-code mappings, formatting dates.

**After Claude:** Paste the export into a Claude project, upload the legend file that shows pay-code mappings, and write: *"Clean this up for payroll entry. Map pay codes to the legend, format dates as MM/DD/YYYY, remove any rows with missing hours, and give me a summary of hours by code."* Claude handles it in 30 seconds. You get a clean, ready-to-paste table.

This same pattern works for: inventory exports, timecard PDFs scanned as images (Claude reads the image), schedule exports before posting.

---

## 4. Gotcha of the Week — The Confident Wrong Number

Claude will present made-up numbers with absolute confidence. You ask: *"What's our labor percentage if payroll is $8,500 and sales are $40,000?"* Claude will happily answer: *"That's 21.25%"* — and sound like it did math instead of hallucinating. It didn't. (The right answer requires knowing your tip structure and whether payroll is just wages or wages+benefits.)

**The fix:** Treat Claude like a calculator that needs YOU to verify the inputs. Before you trust a number, ask Claude to show its work. *"What numbers did you use and where did they come from?"* If it made them up, it'll usually admit it. If they came from something you pasted in, you know the source.

**In practice:** Never use a number Claude generates for decisions until you've verified the source of the numbers it used. This isn't Claude being dumb — it's how language models work. The model prioritizes sounding confident over saying "I don't know."

---

## 5. New Tool Worth Trying — Claude on Your Phone (5 Min)

If you're not running Claude on your iPhone yet, start today. Download the Claude app, log in with your same account, and spend 5 minutes on these:

1. **End-of-shift voice recap** — hold your phone, say "recap today: rush hit 1:45 PM, Francisco called out, we ran lean, sales still solid, cleaning took longer than usual" — Claude transcribes and organizes it.
2. **Snap a photo of your till count** — ask Claude to verify the math on your counted cash vs. the register tape.
3. **Screenshot a vendor invoice** — ask Claude to flag anything that looks off (quantity mismatches, price spikes, terms change).

That's it. You've got three real workflows in your pocket. No learning curve.

---

## 6. AI in the Wild — Restaurant Relevant

Toast (the POS platform) rolled out AI-assisted scheduling last week. System looks at your labor history, customer patterns, and known callouts, then suggests a schedule. The catch: it's a suggestion layer, not autopilot. The operators I know who tested it say it's good at catching understaffing but misses the human stuff (who's training who, who shouldn't close together). You still drive. But for a multi-location operator (like you will be if the DM role comes through), this is the direction the industry is moving. Restaurant tech is moving toward "AI suggests, operator decides," not "AI does."

Worth watching: Olo (Ordering platform) and R365 (recipe costing) are both prepping AI features that integrate their platforms. By next quarter, you'll probably see both announce something. The play isn't to chase every AI vendor tool — it's to watch which ones your existing tools are integrating WITH, because that's where the real leverage lives (CrunchTime → AI costing analyzer, for example).

---

## 7. Skill Up — Do This Today

**Task:** Write your own SOP for something you've been doing the same way for months. Pick any repetitive thing — opening checklist, end-of-shift cutover, how you enter tips, vendor order review, anything.

**Prompt:** Paste this into Claude:

```
I run a Five Guys location. Here's what I do [paste your SOP or describe the process in 3-4 sentences]. 
Write me a tight, numbered checklist version that takes someone new [time it takes you now] to do. 
Include any gotchas or things that trip people up. Make it sound like I'm talking, not like a manual.
```

**What you're looking for:** Does Claude's version match what you actually do? Did it catch something you always forget to mention but always remember to do? That's where you'll find hidden efficiency.

**Your move:** Pick ONE thing from the checklist that Claude suggested and try it for three shifts. Report back: Did it work, or did Claude miss something?

---

## One Ask

What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?

---

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
