# Bobby's Daily AI Brief — June 17, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

**Opus 4.8 shipped.** This is Claude's heaviest model yet. Better at long tasks, better at reasoning through messy problems, better consistency when you're running something end-to-end. The upgrade is live in Claude web, Claude Code, and the API.

More useful for you right now: **Claude Cowork just launched.** This is team collaboration built into Claude — you and Crystal can work in the same project space, see each other's chats, share context. The Five Guys dashboard, the SOP documentation, the sales analysis — all of it can be a shared project so you're not re-explaining context to Claude every session. This cuts your session setup time in half.

**Claude for Chrome works today.** You can hit Cmd+J on any website and ask Claude about what's on the screen. CrunchTime reports, vendor emails, competitor menus, your own dashboard — Claude reads it live. No copy-paste. This is the 5-minute time-save that compounds every day.

Why this matters: Opus 4.8 means you can trust Claude with longer chains of reasoning (multi-step P&L variance, complex staff scheduling). Cowork means Crystal can see your playbooks. Chrome integration means you stop switching between tools.

---

## 2. Prompt of the Week

Use this prompt structure for **daily shift handoff recaps**. Copy it, paste it into Claude, and adapt the brackets:

```
You are a Five Guys shift recap analyst. Bobby is the General Manager at Store 2065. 
He's closing out his shift and wants a quick debrief — what happened today, what to 
flag for tomorrow's team.

Process Bobby's notes below and produce:
1. Sales summary — dollar amount, if known; if not, relative to typical (busy/slow/normal)
2. Staffing — who showed, who no-showed, any issues
3. Labor performance — how the crew moved, any drag spots
4. Issues or incidents — anything the next shift needs to know
5. Quick wins — what went right today
6. One specific thing for the next manager to focus on

Bobby's shift notes:
[PASTE TODAY'S NOTES HERE — voice memo transcript, quick text, photos of the board, anything]

Keep the recap to 5 sentences max. Direct language. Actionable.
```

Why this works: The role setup (you are a QSR analyst who knows Five Guys) teaches Claude to interpret restaurant language. The output structure is what you actually need in a handoff. The five-sentence cap forces clarity — Claude won't bury the lead. Adapt the brackets to match what Bobby actually has at day's end (voice notes, texts, photos of the handoff board). The beauty is it works with messy input. Garbled voice memo? Claude reads through the noise.

---

## 3. Use Case Spotlight

**Cleaning a CrunchTime export for analysis.**

Before: Bobby gets a .csv from CrunchTime. It has every field CrunchTime tracks — time period flags, hierarchy codes, shift type encodings, product categories that don't matter for this analysis. 47 columns. Bobby spends 20 minutes in Excel figuring out what to keep and what to nuke.

After: Paste the CSV into Claude with this one-liner: *"I have a CrunchTime export. Delete columns I don't care about for labor % analysis — keep only: date, shift, hours worked, sales, labor cost, period. Make it readable as a table."* Claude cleans it in 30 seconds and outputs a markdown table Bobby can paste into a quick analysis. Or better: *"Give me a one-tab Excel file with just labor/sales data, sorted by date descending, with labor % calculated in a fourth column."* Claude writes the Python script to do it; Bobby runs it; it's done.

Real time-save: 20 minutes to 2 minutes. And the output is ready to think with, not ready to clean again.

---

## 4. Gotcha of the Week

**Claude can invent restaurant-specific numbers and sound totally confident.**

You ask Claude: "What's the typical labor % for a Five Guys?" Claude confidently says "22-26%." Sounds right. You trust it. Then you compare to your actual store and it doesn't match. Reality check: Claude doesn't know YOUR store's labor %. It's guessing from training data that might be old, might be for a different format, might be just plain wrong.

The fix: Never ask Claude for a number you need to rely on. Ask Bobby (or your own data). Ask Claude to *explain what a number means* ("my labor % is 28%, is that high for Five Guys?") — that's safe. Claude reasoning about your data is solid. Claude generating numbers from nowhere is not.

---

## 5. New Tool Worth Trying

**Claude Projects with voice memos.**

Step 1: Open Claude web. Click "Projects" (top left). Create a new project called "Shift Recaps."
Step 2: Hit the microphone icon, record a 60-second voice memo about your shift (how it went, what happened, what to flag).
Step 3: Claude transcribes it, adds it to the Project context, and you can ask "Summarize today" and it pulls from your voice notes. 

Total time: 3 minutes. No setup. Bobby's voice notes become searchable context Claude remembers across chats. Next session, Claude knows what happened yesterday without Bobby re-typing.

Try it once today. If voice transcription works (it does), this becomes your default shift-close move.

---

## 6. AI in the Wild — Restaurant Relevant

**The industry webinar you should know about: "Cash Out, Tech In: Enhancing the Back Office for the AI Era"** (Nation's Restaurant News, June 30).

The QSR industry is publicly focusing on back-office automation right now. Payroll, inventory pulls, variance analysis, reconciliation — the stuff that eats 10+ hours a week of manager time. The conversation is moving from "should we automate this?" to "how do we do it without breaking the store?"

That's where Bobby is already. He's not waiting for Five Guys corporate to wire up Claude. He's building it himself. This webinar is the industry catching up.

---

## 7. Skill Up — Do This Today

**Upload a CrunchTime export to Claude and ask one specific question.**

- Pull a typical daily export from CrunchTime (sales, labor, food cost — whatever you usually look at).
- Paste it into Claude (or use the document upload feature).
- Ask this exact question: *"What stands out to you about this day compared to what a normal day should look like?"*

Watch what Claude notices. It might flag: low labor productivity, food cost spike, sales dip at a specific time, a ratio that's out of whack. Claude is reading across multiple dimensions at once — something humans do but takes longer.

One question for you next session: **What did Claude spot that you would have missed if you'd just looked at one number?**

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
