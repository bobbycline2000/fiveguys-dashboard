# Bobby's Daily AI Brief — May 11, 2026
*From the desk of your AI engineer — what matters today, nothing that doesn't.*

---

## 1. This Week in Claude — Plain English

Claude 4.7 is here and its real superpower isn't the speed bump—it's that it thinks deeper on ambiguous problems and catches gaps you didn't know you had. For you: when you paste a P&L variance report and ask "what's wrong here?", Claude now works through the logic chain instead of just summarizing. Also: Claude on iPhone got voice mode this week, so you can speak a shift recap into your phone while driving and have it land as a summary in Slack.

The thing people miss: you don't need every upgrade. 4.7 is better for fuzzy diagnostic work (vendor disputes, schedule conflicts, "why did this break?"). Your dashboard and data work stays fine on 4.6. Use it where it fits.

---

## 2. Prompt of the Week

Paste this next time you're documenting how something should work—a new process, a training step, a vendor handoff, whatever:

```
You are a restaurant operations trainer writing for staff with 0-6 months experience.

I'm going to give you a messy description of how [PROCESS NAME] works at Five Guys Store 2065. Your job:

1. Extract the core steps (ignore side comments and context)
2. Rewrite them as 5-8 numbered steps, each one sentence or less
3. Flag any step that's unclear, contradicts another step, or depends on something not explained
4. Give the finished SOP and the flags, nothing else

Assume the reader has never done this before. Concrete examples beat generic language.

[PASTE YOUR MESSY PROCESS HERE]
```

Why it works: The "trainer writing for new staff" role forces Claude to strip jargon and catch gaps. You get a working SOP and a list of things YOU need to clarify—which saves you from finding those gaps during training.

---

## 3. Use Case Spotlight

**Schedule optimization from voice notes.**

You end a shift, talk into your phone: *"We were slammed 11-1, understaffed, two people called out. Orders piled up. Next Saturday I need to run heavier. Also Bri kept getting pulled to dishes when we needed her on register."*

Paste that into Claude (raw phone transcription garbage and all):

```
Analyze this shift recap. Give me: (1) staffing recommendations for similar conditions, (2) which positions were the bottleneck, (3) one operational change that would help.

[your voice notes]
```

Claude gives you:
- Saturday 11-1 needs +1 person on register (Bri was your constraint)
- Cross-training someone else on dishes lets Bri stay front-of-house during rushes
- Consider a "register priority" call during peak hours

30 seconds of talking → actionable schedule fix. That's the kind of leverage most operators never use.

---

## 4. Gotcha of the Week

**The "yes and" trap.**

You ask Claude: "Should I hire this person?" and describe why you're on the fence. Claude does what it's trained to do—it finds the case for hiring them and summarizes it back to you. You hear yourself validated and think Claude agreed with you. You didn't ask for agreement; you asked for clear thinking. You got salesmanship instead.

**The fix:** When you want honest pushback, ask like this: *"I'm leaning toward [decision]. Tell me the 3 strongest reasons I'm wrong."* Claude now knows you want friction, not harmony.

---

## 5. New Tool Worth Trying

**Claude Projects — upload your Store 2065 employee handbook.**

Takes 90 seconds:
1. Go to claude.ai/projects
2. Create a project called "2065 Handbook"
3. Click the paperclip icon, upload the handbook PDF
4. Now ask questions: *"What does the handbook say about shift-call procedures?"* or *"What's the policy if someone's 10 minutes late?"*

You get instant, handbook-accurate answers without re-reading it every time someone asks a question. And when you update the handbook, you upload the new version once and you're done—no re-reading.

---

## 6. AI in the Wild — Restaurant Relevant

**Toast (the POS) just launched Toast AI for menu engineering.** It analyzes your sales mix, food cost on each item, and prep time, then tells you which menu items are dragging profit. No magic—just data. But it's the kind of thing that used to need an accountant to audit.

Why it matters to you: If Five Guys corporate ever adds something like this to CrunchTime, or if you build it for your own dashboards, you'll recognize what it does. Competitive edge gets measured in speed of decision, not quantity of data.

---

## 7. Skill Up — Do This Today

**Go pull your last 5 days of Teamworx schedule into a text file. Paste it into Claude:**

```
I'm going to paste a week of our Teamworx schedule (Store 2065). I want you to:

1. Count how many shifts each person worked
2. Flag anyone scheduled 6+ days in a row
3. Identify the heaviest shift (most people scheduled)
4. Tell me which position is hardest to fill based on schedule patterns

[PASTE YOUR SCHEDULE]
```

You'll get a 30-second labor audit you'd otherwise miss. Tomorrow, ask Claude: *"Based on that schedule, what did you notice about who's reliable vs. who calls out?"* — that's pattern recognition your brain does automatically but you don't articulate.

---

*One ask: What's one thing you wanted Claude to do for you this week that it didn't quite nail?*
