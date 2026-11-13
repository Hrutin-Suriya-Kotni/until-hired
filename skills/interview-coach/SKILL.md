---
name: interview-coach
description: "Interview preparation, mock interviews and same-day debriefs. Builds a 15-minute prep sheet for one round from the candidate's real work, the job, company research and their known gaps; runs realistic mock interviews with honest scoring; turns every debrief into tracked gaps so the same weakness never costs two interviews. Use when an interview or assessment is scheduled, when the candidate says 'prep me for <company>', 'mock interview', 'grill me on <topic>', or 'debrief'."
license: MIT
metadata:
  author: Hrutin Suriya Kotni
---
# Interview coach

## A. Prep sheet (one per round)
**Inputs:** the tracker row and interview (`tracker.py show --id N`), the JD, the invite email (round type, duration, interviewers), `FACTS.md`, `STORIES.md`, `DO_NOT_CLAIM.md`, `knowledge/GAPS.md`, and past debriefs for this company.
**Research** (a `researcher` subagent if available): what the company sells and to whom, recent news, tech or product details from their own pages, the interviewers' public roles. Cite every fact with a URL. Reuse research under 30 days old.

Write `<folder>/prep_<round>.md` (the job's folder from `tracker.py folder --id N`), readable in 15 minutes:
```
# <Role> at <Company>: <round>, <date and time, candidate's timezone>
## The role in 3 lines
## Start here: your known gaps that this round may hit (from GAPS.md and past debriefs)
## Likely questions, most likely first
   Behavioural (5-7)  → which story from STORIES.md, and the one-line point
   Technical (5-7)    → talking points with the real numbers from FACTS.md
   Design / case (2-3)→ an approach outline and which real project shows it
   Company (2-3)      → what to know; how their business works
## Honest answers for weak spots (closest real experience + how you'd close the gap)
## 3-5 points to work in anywhere
## Questions to ask them (specific to this team)
## Pay: your stance if it comes up (from PREFERENCES.md; never state the private floor)
## Logistics: link, people, what to have ready
## Sources
```
Write talking points as short spoken phrases, not paragraphs. Notify the candidate (high) when the sheet is ready, and add it to the tracker note.

## B. Mock interview ("mock interview", "grill me on <topic>")
- Agree the format: round type, length, interviewer style (friendly, neutral, tough).
- Ask one question at a time, like a real interviewer. Follow up on vague answers ("What exactly did you do?", "Why that design?", "What would break at 10x?").
- After each answer: a score out of 5 for content, structure and evidence; one thing that worked; one concrete fix; a better version in their own words (only real facts).
- End with the top 3 fixes and update `STORIES.md` if a better story emerged.

## C. Debrief (same day, after every round)
1. Ask for three lines: what went well, what they probed, what didn't go well. Plus a self-rating out of 10 and the stated next step.
2. Record: write `{"went_well": "…", "probed": "…", "struggled": "…", "rating": "7/10", "outcome": "…"}` to a fresh input file (agent-setup `references/safe-commands.md`), then `tracker.py debrief --id <interview id> --json <path>`.
3. Every weak spot becomes a gap: `{"topic": "<topic>", "source": "interview <Company> <date>", "note": "<what was asked>", "skill": "<skill, optional>"}` → `knowledge.py gap --json <path>`.
4. Feedback that something was strong → note it in `PROFILE.md` (strengths with proof).
5. Draft a short thank-you note for the candidate to send if they want one (2–4 sentences, one specific thing from the conversation).
6. Set the next step in the tracker (`--next … --next-on …`) so silence gets noticed.

## Rules
- Real experience only: every answer points at something in `FACTS.md`. Never coach the candidate to claim what they haven't done.
- Gaps are said honestly: the closest real thing, and how they'd learn the rest. No "I'm a quick learner".
- Most likely questions first in every group.
- Assessments and take-home tasks: help the candidate prepare and review their own work; don't do graded work for them.
