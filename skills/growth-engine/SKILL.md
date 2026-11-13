---
name: growth-engine
description: "Turns everything the search produces into growth: a knowledge graph of what the candidate can prove, a market map of what employers ask for, a ranked skill-gap report, proof-project and learning recommendations, positioning and targeting advice from the funnel, and a 30-minute weekly review with a plan. Use for 'skill gaps', 'what should I learn', 'what is the market asking for', 'why am I not getting interviews', 'weekly review', or when the funnel stalls."
license: MIT
metadata:
  author: Hrutin Suriya Kotni
---
# Growth engine

Applying is half the job. The other half is getting more hireable every week, guided by real evidence instead of guesses.

## The knowledge graph (`<workspace>/knowledge/`)
Built and kept by `python3 <workspace>/bin/knowledge.py`:
- **Nodes:** skills (with a level: evidenced, claimed, learning, none), projects, roles the candidate scored, gaps, learning resources.
- **Edges:** project *uses* skill · role *requires* skill (must-have or nice-to-have) · gap *about* skill · skill *learning_from* resource.
- **Market map** (`market.json`): how often each skill appears in the job descriptions scored so far, and how often it is a must-have, per track.
It grows by itself: intake adds skills and projects, every scored JD adds demand, every debrief or rejection reason adds gaps, every finished proof moves a skill to evidenced.

## 1. Gap report
`knowledge.py gaps --write` → `knowledge/GAPS.md`, ranked by (times asked + times required + 3 × interview mentions):
| Class | Meaning | Default recommendation |
|---|---|---|
| STRENGTH | evidenced and in demand | lead with it in the resume summary, notes and interviews |
| DEEPEN | a strength interviewers still probed | deeper answer, one sharper story, a mock round |
| UNPROVEN | claimed, nothing to show | highest interview risk: a small public proof, or stop claiming it |
| LEARNING | in progress | finish the proof |
| MISSING | in demand, not theirs | close it only if it fits the target track; otherwise filter those jobs out |
| INTERVIEW | raised in interviews, not a JD keyword | honest answer + practice |
Trust the shares only after about 20 scored JDs; say so when there are fewer.

## 2. Recommendations (write them in `knowledge/RECOMMENDATIONS.md`, newest first)
For the top 3–5 gaps, decide with the candidate:
1. **Close it or route around it?** Weigh demand share in their target track, distance from what they already know, and time to a proof.
2. **Proof project** for gaps worth closing: the smallest public piece of work that an interviewer would accept as evidence, done in 1–2 weeks. Spec: goal, scope, the measurable result, what to publish (repo, write-up, demo), and the exact line it adds to `FACTS.md` when done.
3. **Learning plan:** 2–3 resources (official docs and courses first), hours per week the candidate can really give.
4. **Honest wording until then** ("I've used X in a side project; in production I've done Y").
When a proof is done: file `{"skill": "<skill>", "proof": "<link>"}`, then `knowledge.py learn --status done --json <path>`, then a quick **candidate-intake** update so `FACTS.md` gains the line (signed off by the candidate).

Also recommend, from the evidence:
- **Positioning:** which strengths to lead with; headline and summary wording (drafts the candidate edits; never edit their public profiles yourself).
- **Targeting:** from `tracker.py funnel`, which sources, tracks and score bands produce responses and interviews; propose more of those and less of the rest. Needs about 30 applications before the numbers mean much.
- **Adjacent roles** where their evidenced skills already match the market well.

## 3. Weekly review (about 30 minutes, on `cadence.weekly_review_day`)
Prepare it before asking for the candidate's time:
1. **Numbers:** `tracker.py funnel` and `dashboard`: applied, responses, interviews, offers this week and overall; median days to response.
2. **What worked / what didn't:** by source, track and score band; interview debriefs this week.
3. **Gaps:** top 5 from the refreshed `GAPS.md`, with movement since last week.
4. **Decisions for the candidate** (they decide; you write them down): learning goal and proof project, targeting changes, limits, platforms to add or pause, score weights.
5. **Plan for next week:** applications target, interviews and prep, learning hours, one profile improvement.
6. **Check-in:** "How are you holding up? Anything to change about pace?" Adjust the plan to their energy; a sustainable search beats a burnt-out one.
Write it to `knowledge/reviews/<YYYY-MM-DD>.md`, update `PREFERENCES.md` / `config.json` with the decisions, and run `knowledge.py summary --write`.

## 4. Market research (monthly, or when targets change)
With web search, if available: hiring trends and typical pay for the candidate's target roles and locations, with sources and dates. Add findings to `knowledge/MARKET.md`. Treat it as context, not advice; the tracker's own funnel beats general trends.

## Never
- Never move a skill to `evidenced` without a proof the candidate can point to.
- Never present recommendations as guarantees, or salary research as financial advice.
- Never turn the review into pressure: the candidate sets the pace.
