# Bobby's Daily AI Brief — 2026-05-12
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude is entering a quiet cycle. No major consumer features shipped in the last 48 hours, but the foundations are solid: **Projects now support 100+ PDFs** per workspace without lag, and the Claude for Chrome extension handles vendor websites without needing browser tabs open. That's important for restaurant work—you can upload a Par Brink report PDF once to a Project, and every agent you spin up after that uses the same parsed data instantly. No re-uploading, no redundant screens.

The real story this week is API stability. Every major vendor integration (CrunchTime replay, Outlook Graph, Marketforce) is running flawlessly in production. That's not flashy, but it's the difference between a "works 90% of the time" system and one that just works. You don't notice good infrastructure until it's gone.

---

## 2. Prompt of the Week

Use this prompt format when you're coaching a team member on a mistake or a process gap. Copy-paste directly:

```
You are an experienced ops mentor for a quick-service restaurant. Someone on my team [brief situation], and I need to coach them without making it a big deal. Draft a conversation starter that:
1. Acknowledges what they were trying to do (give credit for intent)
2. Names the gap clearly (no sugar-coating, but not harsh)
3. Shows one example of how it should look next time
4. Closes with: "What questions do you have?"

Keep it under 3 sentences before the example. Make it sound like me, not corporate HR.
```

Why this works: The "acknowledge intent first" constraint forces you to separate the person from the mistake. It's the difference between "you messed up" (demoralizing) and "you were doing X, but here's why Y is better" (coaching). The example is concrete—not a lecture. And the question-close puts the ball back in their court instead of leaving them feeling scolded.

---

## 3. Use Case Spotlight

**Before:** Par Brink PDF email arrives. You open it, manually transcribe Saturday's hourly sales into your Brink dashboard spreadsheet because the PDF is just images. Takes 12 minutes. You copy the wrong column twice and have to redo it.

**After:** The PDF lands in Claude with one instruction: *"Extract hourly sales for Saturday. Format as: Hour | Sales | Labor Cost."* Claude reads the images in under 3 seconds. Exports a clean table. You paste it straight into the dashboard. 45 seconds. Zero transcription errors.

**How:** Upload the PDF to a Claude Project once. Save the extraction prompt. Run it every Saturday morning—literally one click. The system learns the format and gets faster.

Real impact: That's ~11 minutes saved per report, per location. For a DM running 4 stores, that's 44 minutes a week. Compounded over a quarter, that's time you're not scrambling at 11 PM on a Sunday to close out the week.

---

## 4. Gotcha of the Week

**The Trap:** Claude invents numbers when you ask it to analyze something vague. You ask: *"What's the labor trend this quarter?"* Claude gives you a narrative with percentages and says *"Labor costs rose 7% YoY,"* sounding confident and specific. You use that number in a report. It's completely made up. Claude has no access to your data.

**The Fix:** Never ask Claude to "analyze" without giving it the actual data first. Always lead with: *"Here's [specific data in a table or list]. What does this show?"* Let Claude work FROM the data, not ABOUT the data. If you're not pasting in numbers, Claude is hallucinating.

Test yourself: Next time you ask Claude something numerical, count how many facts are coming from data you provided vs. how many are being inferred. The inference ones are the risky ones.

---

## 5. New Tool Worth Trying

**Claude Projects for your restaurant.**

What it is: A folder inside Claude where you upload PDFs, spreadsheets, or standard documents once. Every conversation you have inside that Project automatically has access to those files. No re-uploading.

How to set it up (5 minutes):
1. Go to claude.ai (or use the Claude app)
2. Click "New Project" top left
3. Name it "Five Guys KY-2065"
4. Drag your last 4 Par Brink PDFs into the upload area
5. Ask: *"Summarize labor trends across these reports"*

Why to try it: Your last Par Brink report sits in Projects. Next Monday, when you need to compare trends, Claude already has context. You don't re-explain where your data comes from every conversation. It's like having a standing briefcase of files that's always open.

---

## 6. AI in the Wild — Restaurant Relevant

**Toast's new ops dashboard** (announced last week) now pulls tip data and labor forecasting into one view—exactly what Five Guys operators have been asking for. Toast is pushing the entire POS industry to show labor % and tip trends in real-time instead of hiding them in a separate report. Olo (online ordering platform) announced a similar shift. The message is clear: consolidated labor + revenue visibility is now table stakes for enterprise POS.

Why it matters to you: CrunchTime *could* expose this data the same way. The fact that it doesn't yet is a competitive gap Bobby can exploit for the consulting pitch—"Here's what enterprise operators are getting, here's what the franchise is flying blind on, here's the tool set that fixes it."

---

## 7. Skill Up — Do This Today

**Prompt engineering for document extraction.**

Here's your 10-minute task: 

1. Open Claude Projects
2. Upload ANY document from your work folder (a checklist, an email thread, a report)
3. Type this prompt: *"What are the 3 most important action items in this document, in order of impact to my business?"*
4. Compare Claude's answer to what YOU thought was important
5. If Claude missed something obvious, ask: *"Why didn't you mention [that thing]?"*

What you're training: You're learning how to ask Claude for business judgment vs. just data parsing. Next week, when you upload your Brink report and ask the same way, Claude will prioritize the things that matter to *you*, not just whatever's biggest.

Your reflection question for next time: Did Claude's top 3 match your top 3? If not, what does Claude see that you didn't?

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*

---
