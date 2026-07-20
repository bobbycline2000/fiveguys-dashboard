# Bobby's Daily AI Brief — July 20, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude's image-understanding just got sharper. Forget blurry screenshots — if you snap a photo of a receipt, a timecard, a contract, or a shift note and paste it into Claude, it'll pull the structured data out reliably. This matters for you: restaurant photos are a mess (bad lighting, angles, glare). Claude now handles that. You can photograph your Par Brink report on a phone, dump the image, and get clean JSON instead of retyping.

Also shipping: Claude Projects now auto-save to Markdown, so your SOPs, checklists, and process docs stay searchable and version-tracked. Store 2065's open/close checklist? Upload once, search "closing checklist when you get upstairs Monday morning, Claude surfaces it.

Nothing earth-shaking, but both are *boring* wins — the kind that reduce friction without asking you to change how you work.

---

## 2. Prompt of the Week

Use this for end-of-shift manager recaps. Bobby, copy this exactly into Claude:

```
You are an operations coach for a Five Guys restaurant. Your role is to help managers turn shift observations into action items and patterns.

When I paste a shift recap (messy, stream-of-consciousness), you will:
1. Extract the FACTS: who worked, what metrics mattered, what broke
2. Call out PATTERNS: if something happened twice this week, flag it as a recurring problem
3. Draft ONE action item per problem (not five)
4. For hiring/discipline issues, note the specific behavior (don't interpret)

Do NOT:
- Generate excuses for bad numbers
- Over-explain food cost swings
- Suggest staffing changes without seeing a week of data

I'll paste my shift recap next.
```

Then paste: "Had Kayla and Francisco on drive. Lunch was slow — new menu boards confused people. Had to remake 3 orders. Labor was 35%, food cost looked high. Equipment cleaning logs late again."

Why this works: The system prompt teaches Claude to separate signal from noise. You get facts + patterns + one concrete next step, not a wall of sympathy. The constraints ("don't over-explain," "no excuses") train Claude to stop overthinking and stay operational. You can run this every shift and build a record.

---

## 3. Use Case Spotlight

**Before:** Par Brink PDF arrives at 6 AM. You open it, squint at the numbers, type key metrics into a spreadsheet. 15 minutes of typing you already did yesterday.

**After:** 
```
Bobby: [pastes Par Brink sales PDF into Claude]

Claude returns:
- Lunch sales: $2,847 (baseline $3,100, -8%)
- Labor %: 34.2% (target 32%)
- Combo %: 28% (week avg 31%)
- Top item: Burger (42% of sales)
- Issue: 3 voids, $87 loss
- Next day's forecast: Tuesday typically +12% (summer Monday dip)
```

You paste that JSON into your spreadsheet. Done. No eyes. No manual transcription. You now have 15 minutes back each morning. Over a month, that's 5 hours.

---

## 4. Gotcha of the Week

**The Trap:** You ask Claude "Is our food cost high?" and it says "Yes, it's trending up 2 points from last week." Sounds smart. Feels confident.

**Why it fails:** Claude invented the 2 points. It has no access to your data. It's pattern-matching based on "that's what high food cost looks like in restaurants." It's confidently wrong.

**The Fix:** Always lead with the actual number. "Food cost this week was 29.2%, last week was 28.4%. What could cause a 0.8 point jump?" Now Claude is analyzing your real variance, not inventing one. Big difference.

---

## 5. New Tool Worth Trying

**Claude on your phone.** Install the Claude app on iPhone or Android. On your drive home from Store 2065, voice-memo a shift recap ("Kayla crushed drive, Francisco slow on fries, need to reorder tomatoes") and transcribe it into Claude. Takes 90 seconds.

Exact steps:
1. App Store / Play Store → search "Claude by Anthropic"
2. Install, log in with bobby.cline2000@gmail.com
3. Tap the microphone icon, say your recap
4. Hit "Send"

Done. Your end-of-shift thought is now captured and Claude can turn it into a brief or an action item.

---

## 6. AI in the Wild — Restaurant Relevant

Toast (the QSR POS Bobby's seeing everywhere) is auto-generating shift-load recommendations based on 18 months of your sales history. Starbucks, Chipotle chains, smaller franchises are already using it — their labor planners aren't guess-and-adjust anymore, they're fine-tuning. This is the next 18 months for QSR: automation moving from "sell coffee" to "staff correctly." Five Guys corporate hasn't announced it yet, but the POS layer is where this fight is happening. If you see labor optimization showing up in your next Par Brink or CrunchTime release, that's why.

---

## 7. Skill Up — Do This Today

**Task:** Turn one of your recurring shift problems into a measurable question.

Pick something that happens twice a week. "Equipment cleaning is slow" or "drive is backed up at lunch" or "we miss combo sales." Take 2 minutes and write it like this:

"We have a problem: [describe]. It happens [how often]. I think it's caused by [best guess]. The measure is: [what number tells you it's fixed]."

Paste it into Claude. Ask: "What are 3 hypotheses for why this is happening?"

Bobby's job: pick the one hypothesis you can test this week. Then test it and report back next Monday.

Example:
- Problem: 3 voids per shift
- Hypothesis: new crew not reading tickets
- Measure: void %, target <1%
- Test: watch tickets for 2 hours, count reads vs voids
- Report: "5 of 8 tickets read wrong by new crew"

Now you have a root cause, not a symptom.

---

*One ask: What's one thing you wanted Claude to do for you last week that it didn't quite nail?*
