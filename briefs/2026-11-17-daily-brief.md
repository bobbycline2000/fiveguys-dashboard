# Bobby's Daily AI Brief — November 17, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude 5 landed in October and the bar for multi-modal reasoning just went up another notch. If you haven't tried uploading a photo of a messy paper schedule or a screenshot of a CrunchTime export and asking Claude to "make sense of this," you're leaving easy wins on the table. The accuracy on structured-data extraction from images improved enough that it's now genuinely useful for QSR operations — receipts, timecards, delivery tickets all process cleanly without you typing it in manually.

**Why it matters for you:** You're drowning in PDF exports and email attachments. Claude can now read a Par Brink PDF, extract the actual numbers, and spit out actionable summary in one shot. Same with any handwritten note, blurry timecard photo, or messy inventory sheet. This is not a parlor trick — it's a real time saver if you use it.

---

## 2. Prompt of the Week

**Copy and paste this into Claude.** Use it whenever you need to draft a memo, email, or text to your team about a decision or change.

```
You are a restaurant general manager writing to your crew. The tone is direct, respectful, 
and free of corporate jargon. You assume your team is smart and busy — no hand-holding, 
no explanation of obvious things. You name the change, say why it matters to them (not to 
corporate), and tell them exactly what to do. You assume they might push back, so you 
answer the objection before they ask.

Write a [memo / email / text] from Bobby to the team about [THE THING YOU WANT TO SAY].
```

**Why this works:** The role setup ("restaurant GM," "direct and respectful," "assume they're smart") teaches Claude to match the actual communication style that lands with restaurant crews. The objection-answering part keeps the message from sounding tone-deaf. When you use this prompt, Claude stops writing like HR and starts writing like you.

---

## 3. Use Case Spotlight

**Before:** You get the daily Par Brink PDF emailed to you. You skim it, see sales are down 12%, and don't have time to dig into what actually happened — was it traffic, was it ticket average, was it comps, was it a staffing gap?

**After:** You paste the PDF into Claude with: "What's the real story here? Break down sales variance by category, flag any weird patterns, and tell me which one is worth fixing today." You get back a crisp paragraph with the actual levers — "Traffic down 8% (normal Monday), but burger tickets up 2% and drink tickets flat (usually +4% on Mondays) — suggests slower throughput on the line." Now you know whether to staff up tomorrow or look at the grill queue.

This is the kind of work that takes a smart GM 15 minutes of head-scratching and a calculator. Claude does it in 30 seconds. The gap is real.

---

## 4. Gotcha of the Week

**The Trap:** You ask Claude "how much should I spend on marketing?" or "what's a good labor percentage for QSR?" Claude gives you a confident number. You believe it because it's specific and sounds right. It's often wrong or outdated or applies to a 100-unit chain, not your store.

**The Fix:** Every time Claude gives you a number or a "best practice," ask "where did you get that?" If the answer isn't "from a file you uploaded" or "based on data you gave me," treat it as a starting point for your own research, not gospel. Claude is great at reasoning through your numbers. It's unreliable when pulling from memory about industry benchmarks.

---

## 5. New Tool Worth Trying

**Upload a PDF SOP to a Claude Project.** Here's the exact sequence:

1. Open claude.ai → Projects → New Project
2. Name it "FG 2065 Procedures" or whatever
3. Click the paperclip icon, upload any existing SOP PDF (opening checklist, closing checklist, food safety guide, whatever)
4. Close the project
5. Next time you're in a session, type: "I uploaded my [checklist name]. Can you..." Now Claude has the actual document in context

You just went from "Claude, what's on a closing checklist?" (generic answer) to "Claude, what's on *our* closing checklist?" (accurate answer). And you can ask follow-ups. The same Project stays there for next month.

Takes 3 minutes to set up. Worth it.

---

## 6. AI in the Wild — Restaurant Relevant

**Toast (the QSR platform) announced order-time AI recommendations** earlier this week — suggesting drink upsells and comps based on what's moving. Starbucks already does this. It's not a game-changer, but it matters: a 2% ticket-average lift from "would you like a water?" vs. AI-suggested upgrade is real money on 400 transactions a day.

Five Guys corporate isn't there yet, but this is coming. The operators who start thinking about *how* they'd handle AI-driven suggestions in their flow (training on how to override without killing the vibe, coaching new crew on the recommendations) will adapt faster when it lands. It's not "should we do this" — it's "when we do this, what does it look like?"

---

## 7. Skill Up — Do This Today

**Pick one email you wrote this week to your team or a vendor. Paste it into Claude with:** 

"I wrote this email. Make it sharper — same message, but remove every word that doesn't earn its keep. Be direct. No corporate tone."

Look at what Claude trimmed. Tomorrow, write one new email cold using the same tightness. Notice the difference.

This is a 10-minute exercise that trains your eye for clarity. It's not abstract. You'll see the bad habits in your own writing and stop repeating them.

**Next time:** What was one sentence Claude cut that you actually *liked* and wanted to keep?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
