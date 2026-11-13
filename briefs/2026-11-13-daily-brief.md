# Bobby's Daily AI Brief — November 13, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude Fable 5.2 and Claude Mythos 5.2 shipped November 9. Skip the marketing language—here's what changed: these are faster and cheaper than Opus 5, with smarter reasoning for complex technical work. For you: nothing breaks existing Claude in your dashboard or operations. But if you're building new automation, Fable 5.2 is your default now—it's 2-3x faster at the same quality you're used to, which means cheaper scheduled runs. Mythos 5.2 is the real deal for hard reasoning problems, but you won't hit it unless you're reverse-engineering APIs or debugging complex logic flows.

The bigger move: Anthropic went public this week (IPO roadshow Nov 10). You don't need to care about stock price, but you should know Claude is now owned by shareholders who care about quarterly ARR. That means two things: Claude stays here, and pricing will eventually move. It won't tank your usage budget tomorrow, but multi-year cost assumptions get riskier. Hedge by capturing the efficiency wins you can now—the window for "free optimization" closes faster once investor scrutiny hits the feature roadmap.

---

## 2. Prompt of the Week

Use this exact prompt structure for end-of-shift labor recaps—the kind of thing you'd otherwise text yourself notes about or tell the next manager:

```
You are a Five Guys operations consultant who has seen 200+ shift handoffs. 
Your job is to extract what MATTERS from a chaotic shift recap and flag what the next shift needs to know.

Shift date: [DATE]
Location: [STORE]
Manager on shift: [NAME]

Raw notes from the shift:
[PASTE YOUR SHIFT NOTES HERE — doesn't matter if messy, voice memo transcription, scattered thoughts]

Generate a handoff with three sections:
1. **Labor wins / losses** — was labor% where it should be? Did you hit your target? Why or why not?
2. **Crew flags** — who's not pulling weight, who impressed, who needs a one-on-one before next shift
3. **Operational debt** — what broke, what you deferred, what the next shift will inherit

Keep it short. Assume the next shift manager is tired and has 90 seconds.
```

Why this works: The "consultant who has seen 200+ shifts" role teaches Claude to pattern-match, not recite. The three-section structure forces prioritization—Claude stops trying to capture everything and focuses on signal. The tired-manager constraint kills fluff. You paste in chaotic notes and get back a memo that's actually *readable* at handoff time, not a wall of text. Try it tomorrow after a shift and see what you notice—does Claude catch things you'd normally miss in the handoff?

---

## 3. Use Case Spotlight

**Before:** You get an email from CrunchTime with labor variance for the day. It's a PDF export, numbers everywhere, no clear story. You spend 10 minutes digging to figure out whether you're hitting labor% or not, and you still don't know whether it was a scheduling miss or an execution miss.

**After:** Upload that PDF to Claude, paste this prompt:

```
Show me labor% for Store 2065 in a summary table. Then tell me:
1. Are we hitting our target? (What's the target?)
2. Is the variance a schedule problem or an execution problem?
3. What one thing should the manager focus on tomorrow?
```

Claude reads the PDF, extracts the numbers, compares to whatever context you've told it about your target (you can paste last week's target sheet in Projects), and gives you one paragraph with the answer. Takes 90 seconds. No more hunting through the PDF yourself.

Real example from QSR Magazine this week: chains are now using AI dashboards to catch margin problems *during* the shift, not after. They upload daily POS and labor data to Claude or a similar tool, and the dashboard flags when food cost is running high or labor is soft. You're one month away from doing this for CrunchTime data. The question is whether you start the experiment now or wait until you're under more pressure.

---

## 4. Gotcha of the Week

**The trap:** Claude gets a complex question about your business—say, "how should I handle franchisee bankruptcy issues?"—and it gives you a confident 500-word essay with case law, precedent, and numbered recommendations. You read it, feel smart, maybe even forward it to someone. Then a lawyer or accountant finds a glaring blind spot you all missed.

**Why it happens:** Claude sometimes generates confident-sounding advice on topics where it hasn't seen your specific constraints. It fills gaps with plausible-sounding generics. Not lying, just incomplete.

**The fix:** Treat Claude like a smart intern, not a lawyer. When asking for advice on anything material—contracts, labor law, financial decisions, tax strategy—always add: "What am I probably missing? What questions should I ask a [lawyer / accountant / consultant]?" and wait for Claude to surface blind spots before you act on anything.

Real story this week: Papa Johns franchisee filed Chapter 11 bankruptcy. The story doesn't say why, but franchisees don't file lightly. If you were pondering taking on a second Five Guys location, Claude could give you a plausible franchise roadmap—but it would miss the specific covenant structures in Five Guys' franchise agreement, the market dynamics of your district, and the personal financial risk. Get actual advice first, use Claude to validate and expand on it.

---

## 5. New Tool Worth Trying

**Claude Projects for SOPs** — 5-minute setup, real payoff.

1. Open Claude on your phone or desktop.
2. Create a new Project called "Five Guys 2065 SOPs".
3. Upload ONE PDF or document you already own—your GM handbook, a checklist, your opening procedure doc, whatever.
4. Now type: "I'm doing [task]. What's the relevant section from the handbook?"

Claude searches your uploaded SOP and gives you the exact procedure without you hunting through a folder. Takes 5 minutes to set up, saves 30 seconds per lookup. Scale this to 3-4 key docs and you've got an always-on procedure assistant.

(If you have 10+ docs, there are fancier tools, but Projects is the 5-minute version that actually works.)

---

## 6. AI in the Wild — Restaurant Relevant

**This week's real story:** Restaurants can now claim and manage their profiles on AI chat platforms. Starting this month, QSR chains and franchisees can tell Claude (and other AI systems) accurate info about their location—hours, menu items, current promotions, delivery status. When a customer asks Claude "where's the nearest Five Guys" or "does this location do late-night", Claude returns accurate, operator-controlled info instead of guessing.

**Why it matters to you:** This is real. Customers are asking AI where to eat. If Five Guys corporate hasn't claimed the chain profile with current info yet, customers asking Claude about Five Guys locations get stale or wrong data. You can't control corporate's move, but you should know this is happening—within 6 months, customer behavior shifts from Google Maps to "ask Claude." The operators who adapt first win.

**Parallel story:** Starbucks is paying baristas more (Nov 12). Not AI, but context: labor markets are still tight. If you're hiring or holding crew right now, pay velocity is part of the story—competing chains are adjusting compensation. Bobby's competitive edge is efficiency (you know the ops, you're building the dashboard), not wage-matching.

---

## 7. Skill Up — Do This Today

**Today's exercise:** Pick one recurring task you do weekly and turn it into a Claude checklist.

Examples:
- Weekly P&L review
- Monday schedule handoff
- End-of-day deposit check
- Crew one-on-one talking points

**Step 1:** Write down the steps. Don't overthink it. Just list what you actually do.

**Step 2:** Paste it into Claude with: "Turn this into a checklist I can use every week. Add a section for red flags."

**Step 3:** Copy Claude's output into a Projects note and use it next week instead of your old approach.

**Do this today, and here's what to notice:** Does using a Claude-generated checklist change how thorough you are? Does it catch something the old approach missed? Text me tomorrow and tell me—I want to know if the template saves time or if it adds friction. That tells me which recurring tasks are good candidates for full automation.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
