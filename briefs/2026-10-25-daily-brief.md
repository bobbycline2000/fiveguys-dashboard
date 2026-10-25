# Bobby's Daily AI Brief — October 25, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude's latest move is expanded voice mode in Claude for iPhone. You can dictate a voice memo at end of shift and get back structured notes without typing. Useful for you: shift recap ("three grill downs, had to call in two backups, food cost looked clean, Jessica needs retraining on the fryer") becomes a typed summary you can paste into your shift log. No editing a text box. Talk, get the text.

The desktop app is also rolling out smarter PDF handling—you can upload a CrunchTime weekly report or a Par Brink PDF and ask Claude to pull specific metrics without copying them manually. Cuts the "copy, paste, ask" loop down to just uploading and asking.

---

## 2. Prompt of the Week

**Use this when a crew member messes up and you need to document it fairly:**

```
You are a manager at a quick-service restaurant. A crew member made a mistake today. 
I'll describe what happened, and I want you to write a brief, factual incident note for the record 
that (a) explains what went wrong, (b) doesn't sound accusatory, (c) sets the expectation for how to do it right next time.

Keep it to 2-3 sentences. Use plain language, not corporate speak.

Here's what happened: [DESCRIBE THE INCIDENT]
```

**Why this works:** The prompt sets a role (manager, so Claude gets tone right), gives Claude guardrails (factual, not accusatory, forward-looking), and asks for constraint (2-3 sentences keeps you from writing too much). You get something documenting the issue without sounding like you're building a case against someone. That matters when the person reads it later.

---

## 3. Use Case Spotlight

**Turning a chaotic handoff note into a runnable action list.**

Your overnight crew leaves a note: *"Grill acting up again—fan sounds weird, temperature won't hold, had to nurse it all shift. Also we're out of the large red cups, someone needs to order. Fridge in back is making a noise."*

That's three problems mixed with frustration. Paste it into Claude with this:

```
Prioritize these by urgency and cost. I need to know: which gets my attention today, 
which can wait, which do I assign to someone, which do I report to the owner.
```

You get back:
- **Today, before service:** Grill fan (you can't limp through lunch service again)
- **Before EOD tomorrow:** Order large red cups (you'll run out tomorrow night)
- **This week:** Fridge noise (probably just a compressor, but track it before it dies)

One message went from a pile of half-thoughts to a sequenced action list you can actually work from.

---

## 4. Gotcha of the Week

**Claude invents plausible-sounding numbers when you ask about something it doesn't know.**

Example: You ask, "What's the average food cost percentage for quick-service restaurants right now?" Claude might come back with "32-37%" with confidence—and that number could be completely made up. It *sounds* right. You might use it to calibrate your own targets. Then your actual cost is 28% and you feel like you're winning when maybe you're not.

**The fix:** Always ask "where did you get that number?" If Claude says "this is an estimate based on general industry knowledge" or "I don't have current data," trust that answer over a specific number. When it matters for a decision, grab the real data yourself (call your distributor, check NRN, ask Phil).

---

## 5. New Tool Worth Trying

**Claude Projects: Save an SOP as a living document.**

Open claude.ai (or the app), create a new Project called "Five Guys Opening Checklist" or "Closing Procedures," upload a PDF of your current SOP or just type in what you do. Then every shift, you can ask Claude to walk you through it, or ask specific questions ("what's the temp check for the holding cases?") and get instant answers without hunting through a file.

Setup time: 3 minutes. Try it today. You'll use it within a week.

---

## 6. AI in the Wild — Restaurant Relevant

Toast (the POS system a lot of independent restaurants use) just rolled out AI-powered shift forecasting. Instead of guessing how many people you need Tuesday lunch, it learns your actual patterns and tells you. Five Guys corporate hasn't announced anything like this yet, but it's coming to the industry. The implication for you: soon, labor scheduling becomes "I feed Claude my last 8 weeks of sales and let it tell me how many people I need each shift" instead of guessing.

---

## 7. Skill Up — Do This Today

**Practice turning a vague problem into a specific Claude question.**

Pick something that's been bugging you about the store (labor costs are creeping up, the schedule feels wrong, you're not sure if your food cost is actually good). Write it down badly: "Why is everything so hard?"

Now rewrite it like you're explaining it to Phil: "October 15-20, labor dollars were 32% vs our target of 28%. Sales were 3% down from the previous week. Staffing pattern was the same. What would drive that?"

Paste that clearer version into Claude and ask it to identify possibilities (weather? unusual absence? more complex orders?). The vague problem becomes something Claude can actually help with.

**Your question for next time:** Did naming the specific dates and numbers help Claude give you something actually useful?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
