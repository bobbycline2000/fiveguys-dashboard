# Bobby's Daily AI Brief — June 18, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Nothing shipped this week that changes your day. Anthropic announced they're opening a Seoul office and there's some government-level noise about access restrictions on their newest models in certain jurisdictions—neither affects you. The real move last month was the Opus upgrade (better reasoning, better coding), which you're already using. Bottom line: Claude's stable. The toolbar doesn't break. Your automation doesn't rot. That's the story.

What SHOULD be on your radar: the NRN story about back-office automation in the "AI era" (webinar June 30). Why? Because Five Guys corporate will eventually see that story. When they do, they'll start asking DMs what they're doing with AI on P&L, labor scheduling, inventory. You're already months ahead of that conversation. Keep shipping.

---

## 2. Prompt of the Week

Use this exact prompt for your daily manual P&L review (the numbers you can't automate yet):

```
You are a Five Guys unit-level operations analyst. I'm going to give you yesterday's P&L snapshot. 
Your job: flag the THREE most material variances (biggest dollar or biggest ratio miss vs. last week 
or last year). For each, give me a one-line hypothesis about ROOT CAUSE (labor scheduling, food waste, 
customer count drop, or something I directly control). Then give me ONE specific question to ask 
the team that will confirm or kill that hypothesis.

Format:
VARIANCE 1: [Item] — [Hypothesis]
Question: [Specific ask]

Keep it tight. No fluff. Assume I know the business.
```

Why this works: You're teaching Claude to think like a detective, not a calculator. The prompt forces it to pick THE material variances (not list everything), to reason about cause (not just describe the effect), and to give you a checkable hypothesis. This is how you turn a raw P&L export into a five-minute conversation with your team that moves the needle.

---

## 3. Use Case Spotlight

**Before:** You get the weekly tip sheet from your payroll software with 23 employee names, hours, regular pay, overtime, tips. Some names are first-name-only. Some entries have notes like "called in Wed, covered Fri" scattered throughout. You manually match it to your roster, fix spellings, calculate the tip ratio percentage for payout purposes, and email it to Crystal. 30 minutes of manual work that's error-prone every week.

**After:** You paste the raw tip sheet (messy as it comes) into Claude with this prompt:
```
I need this tip sheet cleaned and standardized for payroll entry. Match each person to my 
active roster (I'll paste it below). For any name mismatches, flag them with [UNRESOLVED]. 
Output a table: Employee | Hours | Regular Pay | Tips | Total | Payout% rounded to 1 decimal. 
Sort by last name. Include a summary line: "Payout rows ready for entry."
```

Claude cleans it in seconds. You spot-check the unresolved names, correct them, and the sheet is ready to hand off. 5 minutes instead of 30. And because Claude built the table in a standard format, you can now feed it into your payout automation script instead of re-keying it manually next week.

This is where AI actually saves restaurant operators time: not big strategy, but the repetitive manual cleanup work that eats an hour a week you didn't even track.

---

## 4. Gotcha of the Week

**The trap:** You ask Claude "What should my food cost be?" and it gives you a number: "Typically 28-32% for QSR." You write it down. You've now got a made-up number with no reference to your actual store, your menu mix, your waste, or your supplier pricing.

**The fix:** Always ask Claude for the VARIABLES, not the number. Rephrase to: "What are the three biggest drivers of food cost variance in a Five Guys location, and what questions should I ask my supplier or POS to understand mine?"

Now Claude gives you: portion size creep, fry oil consumption, beef weight variance. You can actually CHECK those things. That's an insight. The generic percentage was a hallucination wearing a suit.

---

## 5. New Tool Worth Trying

**Claude Projects + Your Five Guys SOP.**

1. Open claude.ai → click "Projects" (top-left)
2. Create new project: "Five Guys Store 2065 Operations"
3. Upload your most painful SOP as a PDF (opening checklist, closing rundown, whatever you always reference)
4. Start a new chat IN that project
5. Ask: "Walk me through the opening checklist and flag any steps that are vague or could cause confusion."

Claude reads YOUR document, in YOUR project context, and gives you feedback on clarity. This takes 2 minutes to set up. The payoff: next week, you can chat with your team IN that project and say "Ask Claude about step 7 of the opening checklist" instead of texting the same explanation four times.

---

## 6. AI in the Wild — Restaurant Relevant

**Nation's Restaurant News is hosting a webinar on June 30: "Cash Out, Tech In: Enhancing the Back Office for the AI Era."** 

Translation: QSR chains know they have a back-office problem (POS integration, scheduling chaos, inventory counting), and they're looking for AI solutions. Five Guys corporate will see this headline. They'll start exploring back-office AI vendors. By the time that RFP lands on a DM's desk, you'll have already built dashboard dashboards and automated your schedule. You'll be the case study, not the slow follower trying to catch up.

Watch the webinar if you can. Not for the vendor pitches—they'll be generic—but for what problems the industry is admitting publicly right now.

---

## 7. Skill Up — Do This Today

**Task:** Turn a voice memo into an action item list.

1. Open Claude on your phone or computer
2. Record yourself for 2 minutes talking about whatever's bugging you today: "Labor was short yesterday, Bri called in, we had to cut breaks, the morning crew looked fried by 11 AM, need to adjust Friday's schedule, also noticed cold fries going out around 4 PM yesterday, might be timing or fryer temp, need to check with the line crew..."
3. Use Claude's voice mode OR paste a transcript
4. Prompt: "Extract the 3-5 concrete action items from this ramble. For each one, tell me: What needs to happen, Who does it, By when. Format as a bullet list I can email."

Claude turns rambling into a clean list. Tomorrow, ask yourself: which of those action items did you actually follow through on? That tells you what actually matters vs. what's just noise you vent about.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
