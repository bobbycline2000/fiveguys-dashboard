# Bobby's Daily AI Brief — May 3, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Anthropic shipped structured outputs as a standard feature across all Claude models this week — meaning you can now ask Claude to return data in exact JSON shapes without the guesswork. For a QSR operator, this means: grab a CrunchTime report, ask Claude to parse it into a specific format (sales by daypart, labor hours by role, food cost by category), and get back perfectly structured JSON you can pipe directly into a dashboard or spreadsheet. No more "Claude sometimes adds extra fields" or "the numbers have quotes around them." The output schema is locked.

Why this matters: The five-minute data massage (copy-paste, find-replace, fix formatting) becomes zero minutes. On a daily brief, a weekly schedule rebuild, or a P&L variance analysis, that's the friction gone. You'll use this more than you think.

---

## 2. Prompt of the Week

**Shift Recap SOP Generator**

Copy this and save it in Claude Projects under "Operations":

```
You are a Five Guys shift recap analyst. Your job is to help me structure 
a manager's closing notes into an actionable shift summary.

I will give you raw closing notes—messy, stream-of-consciousness, whatever 
a GM texted at the end of a shift. Your job is to:

1. Extract the FACTS: sales, headcount, any incidents or breaks
2. Identify the PROBLEMS: what didn't go right (staffing gaps, waste, 
   quality issue, customer complaint)
3. Suggest the ACTION: one thing the next shift should know/do about it
4. Flag TRENDS: if this is the 3rd mention of the same problem this week, 
   call it out

Format as:
- Facts (bullet list)
- Problem (one sentence max)
- Action (imperative, one line)
- Trend flag (yes/no, with context if yes)

Do NOT add commentary, do NOT speculate, do NOT soften the language.
```

**Why this works:** You're giving Claude a role ("shift recap analyst"), a clear input shape ("raw closing notes"), a specific output structure (4-part template), and a constraint ("do NOT add commentary"). The constraint is key—it stops Claude from turning a closing note into a therapy session and forces it to be analytical. A GM can dump a 10-sentence voice memo; Claude turns it into a 5-line brief that the next shift can act on in 30 seconds. Run this every shift close and you'll surface patterns by Thursday that otherwise stay buried until the PL meeting.

---

## 3. Use Case Spotlight

**From Messy Excel Export to Clean Labor Report**

**Input** (what CrunchTime spits out):
```
Name,Date,In,Out,Meal_Deduct,Net_Hours,Rate,Gross
Maria,05/02,10:30:15,18:45:22,0.5,7.75,15.50,119.88
James,05/02,14:00:00,22:30:45,0.5,8.00,16.25,130.00
  [50 rows of bad formatting, duplicates, typos in names]
```

**Paste into Claude with this prompt:**
"Clean this labor export. Fix name typos against our employee list. Verify hours make sense (nothing over 10 hours in one shift, no 24-hour gaps). Flag any rate that doesn't match our wage structure. Return as JSON array with [name, date, hours, rate, gross, any_flags]."

**Output** (what you get back):
```json
[
  {"name": "Maria Garcia", "date": "2026-05-02", "hours": 7.75, "rate": 15.50, "gross": 119.88, "flags": null},
  {"name": "James Rodriguez", "date": "2026-05-02", "hours": 8.00, "rate": 16.25, "gross": 130.00, "flags": null},
  {"name": "Tommy Chen", "date": "2026-05-02", "hours": 10.50, "rate": 16.00, "gross": 168.00, "flags": "exceeds 10-hour shift max"}
]
```

You now have clean data, caught the shift violation, and spotted a rate mismatch — all in one call. Paste that JSON straight into your dashboard or a spreadsheet. No copy-paste cleanup. No hunting for typos. This is the single biggest payoff of structured outputs.

---

## 4. Gotcha of the Week

**Claude will invent numbers and sound confident about them.**

You ask: "What's the average check size at Five Guys?"

Claude (hallucinating): "The average check size at Five Guys locations is approximately $18.75 per transaction, with combo orders trending toward $22–25."

You take that as truth and build a forecast around it. Then you realize it's completely made up—Claude has no access to Five Guys financial data and just blended "fast casual burger chains" into a guess.

**The fix:** When Claude answers a factual question about your business, always ask: "Is this based on my actual data, or are you estimating?" If it's estimating, throw it out and ask him to work from the numbers you feed him instead. Same rule applies to dates, counts, and any statistic. If you haven't given him the data, the answer is a guess wearing a suit.

---

## 5. New Tool Worth Trying

**Claude for Chrome — Highlight Any Menu and Ask Questions**

Takes literally 2 minutes to try:
1. Install [Claude for Chrome extension](https://chromewebstore.google.com/detail/claude-for-chrome/aiaalpklncjnkhkimhkhnhodjdkbngah) (if you haven't already).
2. Go to your vendor's website (Sysco, US Foods, whatever you use for ordering).
3. Highlight any product section on the menu — say, the burger toppings list or the supplier's pricing tier.
4. Right-click. Choose "Ask Claude."
5. Ask: "What's the cost-per-unit if I order 10 cases? What's the shelf life on this?"

Claude reads the web page in real-time and answers. No copy-pasting. No jumping between tabs. No forgetting what you were looking up.

Try it once on your supplier's website. It'll stick.

---

## 6. AI in the Wild — Restaurant Relevant

**Toast (the POS platform used by 10,000+ restaurants) announced native AI order recommendations** — the system now watches what a customer orders, what's slow-moving in inventory, and what's profitable, then suggests add-ons at the point of sale. Early reports from indie pizza shops and ramen joints: +3–5% average check, zero customer friction.

Why it matters to you: This is the playbook. You don't need a new POS. But you could ask Claude to build a simple add-on suggestion list for your Five Guys menu — "If someone orders a burger, suggest..." — based on your actual sales patterns. Feed it two weeks of transaction data, get back a ranked list of high-margin combos to train your counter staff on. It's Toast's feature, built on Five Guys data, for zero dollars.

---

## 7. Skill Up — Do This Today

**Parse a real CrunchTime report using structured output.**

1. **Export your last week of CrunchTime sales data** (even just one day is fine). Grab the CSV, don't edit it.
2. **Go to claude.ai. Start a new chat.**
3. **Paste this prompt:**
```
I'm going to paste a CrunchTime sales export. Parse it into a JSON object 
with this exact structure:

{
  "date": "YYYY-MM-DD",
  "location": "Store name",
  "total_sales": number,
  "transactions": number,
  "avg_check": number,
  "daypart_breakdown": {
    "breakfast": number,
    "lunch": number,
    "dinner": number
  },
  "top_5_items": [
    {"name": "item name", "qty": number, "revenue": number}
  ],
  "staff_hours": number
}

Return ONLY valid JSON. No explanation. If the data is missing, use null.
```
4. **Paste your CrunchTime export.**
5. **Look at the JSON Claude returns.** Notice: zero guessing, zero typos, perfectly formatted, ready to plug into a script or sheet.

**Question for next brief:** Did the JSON structure match what you needed, or would you change the fields?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
