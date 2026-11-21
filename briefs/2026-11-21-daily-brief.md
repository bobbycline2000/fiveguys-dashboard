# Bobby's Daily AI Brief — 2026-11-21
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude 5.5 models shipped last month and they're the foundation of your operation now. **Haiku 5.5 is the one that matters for you** — it's 40% cheaper to run than its predecessor, twice as fast, and built specifically for the kind of work you do: summarizing reports, running repetitive analyses, feeding data into dashboards. The speed means you can run five-minute verification passes instead of ten. The cost means your automation stays lean.

The bigger news? Anthropic is going public (S-1 filed with SEC in October). That's not hype — it means Claude gets better funded R&D and longer credibility runway. When you're betting your operations dashboard on an AI tool, the company's public commitment matters.

The one thing **not to touch yet**: the new drug-discovery work Anthropic announced. That's enterprise pharma. Not your problem.

---

## 2. Prompt of the Week

You run a franchise location. You need to make quarterly decisions fast — usually late Sunday night when you're alone with the P&L. Here's a prompt structure that cuts through noise:

```
You are a CFO analyst reviewing a single-location Five Guys franchise P&L.

Your job is NOT to praise or reassure. Your job is to surface the two biggest problems.

Look at:
- Food cost %; target is 28%. Anything above 30% is a bleeding hole.
- Labor %; target is 24–26%. Anything above 28% is a staffing problem.
- Sales trending. Last four weeks vs prior year same weeks.

For EACH problem you find, tell me:
1. The exact variance (dollars and %)
2. The three most likely root causes (in order of likelihood)
3. What you'd check first if you were walking the store Monday morning

Don't sugarcoat. Don't tell me "you're doing great." Tell me what's broken.

P&L data:
[PASTE YOUR P&L HERE]
```

Why this works: You're not asking Claude to generate strategy. You're asking it to **see what you're not seeing** — the second-order problem hiding behind the first. The constraints ("surface two problems," "likely causes in order") force specificity instead of generic advice. And the final instruction ("don't sugarcoat") inoculates against Claude's default politeness. You get the brutal read first, then you decide what to do about it.

---

## 3. Use Case Spotlight

Here's something most Five Guys operators haven't tried: **Turning your daily/weekly email summary into a structured action log.**

**Before:** You get a P&L email, a labor report, a Brink PDF. Three different formats. You read them, make mental notes, forget half by Tuesday.

**After:** You paste all three into Claude with this instruction:

```
Extract action items only. Format: | Date | Issue | Root Cause | Action | Owner | Deadline |

Ignore commentary. Ignore praise. Only lines where someone needs to DO something.
```

You get back a one-page table. Pin it next to your POS. Check it daily. By Friday, you know what actually got done.

We built exactly this into your dashboard — the brief captures it every morning and dumps it straight into the team chat. That's what "lights out" looks like. No clipboard. No missed steps.

---

## 4. Gotcha of the Week

**Claude will confidently invent numbers.**

You ask: "What was our average ticket for November?"

Claude sees you've mentioned "November" and "average" and "ticket" in past conversations, pattern-matches, and returns: "$8.47"

Sounds good. Very specific. Completely made up.

**The trap:** You paste it into a deck, into an email to your DM, into a forecast. It propagates.

**The fix:** Every single number Claude gives you, ask "where did you get that?" If the answer is "I don't have that data, I inferred it," you need to verify it yourself. Claude is a pattern engine. It's very good at patterns. It's terrible at "I don't know." So make it say "I don't know" first by asking for the source.

---

## 5. New Tool Worth Trying

**Claude on mobile (iPhone/Android)** — 2-minute setup.

Go to claude.ai on your phone, pin it to your home screen. That's it. Now you have a voice-to-text tool for end-of-shift recaps.

**Use it like this:** 5 minutes before you clock out, hit voice, say: "Shift recap: ticket average was high, labor ran 25%, food cost looked tight, two call-outs, Halo effect is strong this week." 

One minute of dictation. Claude transcribes, you drop it in your running notes. By Friday you have a full week of voice memos without typing anything.

No app install. No login shenanigans. Just mobile web + voice input.

---

## 6. AI in the Wild — Restaurant Relevant

QSR Magazine ran a story about **AI dashboards helping operators catch margin problems sooner.**

The theme: multi-unit operators are building real-time dashboards (sound familiar?) to surface variance before the month closes. The operators who spot a food-cost spike on day 8 instead of day 30 have 22 days to fix it. That's the difference between a 29% month and a 28% month.

Five Guys corporate hasn't announced any AI initiatives that I can see. But the operators building their own are seeing 0.5–1 point margin improvement in the first 90 days. That's real money on a 2000-a-week store.

You're ahead of the curve on this one.

---

## 7. Skill Up — Do This Today

**Extract one margin problem from your most recent P&L and ask Claude to diagnose it.**

Exact steps:
1. Grab your last week's P&L
2. Find your highest variance line (food cost, labor, discounts, whatever stands out)
3. Paste this into Claude:

```
Here's one line from my P&L that's off:
[PASTE LINE WITH BUDGET VS ACTUAL]

This was a [INSERT DAY OF WEEK, e.g., "Friday night"] and the [food cost] came in at X% vs our 28% target.

What would you check first to find the root cause?
```

4. Read Claude's answer. Tomorrow or Monday, go check those three things in your POS.

**Tomorrow's question for you:** Did Claude's first suggestion match what you actually found in the POS, or did it miss something? Reply with what you found.

---

*One ask: What's one thing you wanted Claude to do for you yesterday that it didn't quite nail?*
