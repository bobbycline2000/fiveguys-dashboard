# Bobby's Daily AI Brief — Saturday, June 20, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude Opus 4.8 is live and shipping faster. The model layer shipped a week ago (May 28), but it matters now because you're actively using Claude Code and Projects — both get the faster foundation. If you've noticed snappier responses on complex JSON parsing or when you paste multi-tab CrunchTime exports, that's why. The speed gain is real for your use case (parsing reports + building dashboards), not theoretical.

Also live: Claude in Slack. If your team uses Slack internally (you're running one operator + crew), this isn't an immediate must-have. But if Estep corporate is ever on Slack, wiring Claude there means you can paste a customer complaint into Slack and get a response draft without copying to Claude chat. Low priority for you right now, but worth knowing it exists.

---

## 2. Prompt of the Week

You run a five-guy operation. Use this prompt to turn chaotic shift notes into a written SOP nobody has time to write:

```
You are an operations trainer writing a step-by-step SOP manual. Your reader is a new crew member on day 3 with zero restaurant experience.

Here is a shift debrief that captured what a strong opener does:
[PASTE SHIFT NOTES HERE]

From this, extract ONE specific operational task that took the most time or had the most moving parts. Write it as a numbered SOP (1. 2. 3. etc.) with:
- What you do
- Why you do it (the business reason, not the task reason)
- What success looks like (how to verify you did it right)
- One common mistake to avoid

Do NOT include information about how the day went, who was working, or personal observations. SOP only.
```

Why this works: shift notes are stream-of-consciousness. An SOP is a decision tree. This prompt forces Claude to extract the repeatable task from the noise and frame it in a way that's actually useful to someone learning it. The "why" line especially—nobody documents why, and it's the thing new people forget fastest.

---

## 3. Use Case Spotlight

**Before:** You manually track which crew members passed their Steritech audit task. You check email, cross-reference the PDF, update a spreadsheet somewhere.

**After:** Paste the Steritech PDF into Claude with this prompt:

```
Extract the non-critical findings from this Steritech audit. For each finding, tell me:
1. The violation (what was wrong)
2. The category (food safety / cleanliness / documentation / equipment)
3. Who on my crew owns fixing this (be specific—Equipment Manager, Shift Lead, Opener, Closer, or General Crew)
4. By when (today / this week / by next audit)

Format as a table.
```

You get a table you can paste directly into your crew Slack or a stand-up sheet. Steritech's PDF is a narrative mess. Claude turns it into an action grid in 20 seconds. This is real—try it on your next audit PDF.

---

## 4. Gotcha of the Week

Claude will invent closing times. You paste "what are the hours for the Five Guys in my area?" Claude says "typically 10 PM" because that's a common QSR closing time. But yours closes at 10 PM or 11 PM depending on the location. Now you're sending a customer the wrong hours via email because Claude sounded confident.

**The fix:** Always verify addresses and hours by naming the specific location. *"What are the hours for Five Guys, 9050 Dixie Hwy, Louisville KY?"* is different from *"Five Guys hours"* because the specific address forces Claude to acknowledge it doesn't know and admit it instead of hallucinating.

Same applies to competitor hours, menu items, pricing. Specificity kills hallucination.

---

## 5. New Tool Worth Trying

Claude Projects. If you haven't used it yet, try this:

1. Go to claude.ai/projects on your desktop
2. Click **New project**
3. Name it "2065 SOP Library"
4. Click the **Upload** button and pick any SOP you've written (a checklist, a form, anything)
5. Click **Add context** and paste your Five Guys manual or training doc
6. Now ask Claude: *"based on this manual, what is the standard closing checklist?"*

Claude now has context of your docs and can answer questions about them. It takes 2 minutes. You can add more files anytime. This is the single-highest-ROI Claude feature for small operators—everything Claude knows about YOUR rules, not generic rules.

---

## 6. AI in the Wild — Restaurant Relevant

Taco Bell is testing a **$3 Chili Cheese Menu** in Louisville. That's your city, your market. This isn't "AI uses AI"—it's actual operator strategy: they're testing value positioning to compete with Five Guys on price perception. You should know what they're pricing, because your customer overlap is real.

Also worth watching: SevenRooms just shipped a reservations aggregator. Your store doesn't take reservations (QSR), but if Estep corporate ever expands to casual dining (which Phil is exploring), this is the platform to know about. It unifies Resy + OpenTable + local booking + walk-ins into one dashboard.

---

## 7. Skill Up — Do This Today

Open your last customer complaint email (or imagine one). Paste it into Claude with this prompt:

```
Here's a customer complaint that came in:
[PASTE EMAIL]

Write a 3-sentence apology + resolution offer that:
1. Acknowledges what went wrong (specific detail from their message)
2. Takes responsibility (no "we're sorry you feel that way"—own the failure)
3. Offers a concrete fix (free item / discount / replacement)

Keep it to 3 sentences max. Sound like a restaurant manager, not a corporate chatbot.
```

Run it. Read the result. Does it sound like something YOU would send? If not, paste it back and say *"make this sound more direct, less formal."* Now you're training Claude on your voice.

Next time a complaint comes in live, you'll have a template in your head. Test it right now so you're not learning under pressure.

---

*One ask: What's one thing you wanted Claude to help with this week that you haven't asked yet?*

---

## Archive & Deployment

**File:** `C:\Users\bobby\OneDrive\BobbyWorkspace\briefs\2026-06-20-daily-brief.md`

**Deployment:** Pushing to origin/main in github/fiveguys-dashboard.
