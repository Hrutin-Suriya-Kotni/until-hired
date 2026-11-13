---
name: candidate-intake
description: "Frank, structured interview that builds the candidate's full context before any application goes out: goals, targets, every role and project with real numbers, proof for each skill, weak spots, search history, constraints and pay. Grills vague answers, separates evidenced from claimed skills, and writes PROFILE, FACTS, DO_NOT_CLAIM, PREFERENCES, STORIES and the knowledge graph. Use on first run, when the candidate says 'interview me', 'grill me', 'update my profile', after a big change (new project, new skill, new job), or when facts are missing."
license: MIT
metadata:
  author: Hrutin Suriya Kotni
---
# Candidate intake: the grill

Everything this system writes for the candidate is only as good as what it knows about them. This interview is where that knowledge comes from. Done well, it takes 60–90 minutes and can be split across sessions.

## How to run it
- **Ask for frankness first, and give it back.** Open with: "I'm going to ask a lot of direct questions and push back when an answer is vague. It's how I avoid writing anything an interviewer can break. Answer as honestly as you can; 'I don't know' and 'skip' are fine." Then be kind and direct, never flattering.
- **One question at a time** (two only if they are tightly linked). Wait for the answer.
- **Read what exists first.** If the candidate has a resume, LinkedIn export, portfolio or old notes, read them before asking, so you probe instead of asking for what's written.
- **Push on vague answers** with follow-ups like:
  - "What did *you* do, not the team?"
  - "What's the number? Before and after?"
  - "How would you prove that in an interview? Is there a link, a repo, a demo?"
  - "If your manager heard this, would they agree with the wording?"
  - "Which part was someone else's work?"
  - "Have you used it in real work, or followed a tutorial?"
- **Catch both inflation and underselling.** Inflated claims get moved to `claimed` or `DO_NOT_CLAIM`. Undersold work ("I just fixed some scripts") gets probed until the real impact is clear.
- **Reflect back.** After each part, summarise in 5–8 lines and ask "Is this right? Anything I've overstated or missed?" Only then write the files.
- **Save after every part.** Update `profile/INTAKE_PROGRESS.md` so the next session resumes where this one stopped.
- **Sensitive topics are optional:** health, family, visa, gaps in employment. Record only what changes the search (e.g. "needs remote", "visa sponsorship required"), in the words the candidate approves.
- If the candidate sounds stressed or discouraged, acknowledge it briefly and keep the pace manageable.

## The nine parts
### 1. Goal and urgency → `PROFILE.md` (Situation)
- What are you looking for, in one sentence? Why now?
- Employed, serving notice, or between jobs? By when do you need an offer? What happens if it takes longer?
- What would make the next job a clear win in two years?

### 2. Targets → `PREFERENCES.md`
- Roles in order of preference; seniority you can honestly defend.
- Industries and company types (stage, size, product vs services). Dream companies; companies to avoid and why.
- Locations: preferred, acceptable, remote, relocation and its conditions.
- Pay: current, expected range, a single number if forced, a private walk-away floor. Notice period, earliest start.
- Job types to skip (internships, contract, gig, unpaid trials, night shifts...).

### 3. Experience inventory → `FACTS.md`
For **every** role, internship, freelance gig and serious project:
- Dates, title, company, location or remote.
- 3–6 things *they* did, each with a number (users, latency, accuracy, cost, revenue, time saved, scale).
- Tech actually used in that work.
- Evidence: link, repo, paper, demo, or "internal: can explain in detail".
Also: education, awards, papers, certifications, open-source work, talks.
Then ask: "How many years do you want to state, in total and per skill?" Use their answer only if it is defensible from the roles above; if not, say so plainly and agree on honest wording.

### 4. Proof check → knowledge graph + `DO_NOT_CLAIM.md`
Go through every skill mentioned so far and agree a level with the candidate:
- **evidenced:** real work or a public project, with something to point at;
- **claimed:** they say so, but nothing to show yet;
- **learning:** in progress;
- **none:** not known.
Record each skill: write `{"name": "<skill>", "evidence": "<link or note>"}` to a fresh input file (agent-setup `references/safe-commands.md`) and run `python3 <workspace>/bin/knowledge.py skill --level <level> --json <path>` (`evidenced` needs evidence). Each project: `{"name": "<project>", "skills": ["a", "b", "c"], "evidence": "<link>"}` → `knowledge.py project --json <path>`.
Anything that is `none`, or `claimed` and central to a job type, goes into `DO_NOT_CLAIM.md` with what would make it claimable.

### 5. Gaps and history → `PROFILE.md` (Weak spots) + `knowledge.py gap`
- Which interview questions went badly, ever? What feedback or rejection reasons have you had?
- Which job requirements make you close the tab? Why?
- What do you avoid at work? What do you want to get better at?
Record recurring gaps: `{"topic": "<topic>", "source": "intake: <context>", "note": "<detail>"}` → `knowledge.py gap --json <path>`.

### 6. Search so far → tracker
- Where have you applied, what happened, what's still open? Any interviews scheduled or offers pending?
- Which platforms do you already use, and which have worked?
Add each live or recent application: `{"company": "...", "role": "...", "source": "...", "notes": "from intake", "evidence": "candidate said so"}` → `tracker.py add --json <path> --status <applied|assessment|interview|offer|rejected> --applied-on <date>`; add scheduled rounds with `tracker.py interview-add --json <path> --job-id N --when "YYYY-MM-DD HH:MM"`.

### 7. Constraints and working style → `PROFILE.md`
- Hours, on-site vs remote, travel, family or health constraints that matter (optional).
- Team and manager style that brings out your best work; what drains you.
- Deal-breakers.

### 8. Assets → `FACTS.md` (links) + `materials/`
- Current resume(s) (files), LinkedIn, GitHub, portfolio, writing samples (to match their voice), references (names only with their OK).
- Copy resume files into `materials/_base/`.

### 9. Facts sign-off (required before any application)
Show the candidate `FACTS.md` and `DO_NOT_CLAIM.md` in full and ask them to confirm or correct every line. Add a dated line to the FACTS change log: "signed off by candidate". Also build `STORIES.md`: 4–6 stories (Situation, Task, Action, Result, What I'd do differently) from their strongest work, one of them about a failure.

Then fill `PROFILE.md` (one-paragraph summary, strengths with proof, weak spots), mark every part `done` in `INTAKE_PROGRESS.md`, and hand back to **until-hired**.

## Keeping it current
- **Quick update** ("I learned X", "I shipped Y"): run only parts 3–4 for that item, then sign off the changed lines.
- **Full re-intake:** every 2–3 months, after a job change, or when the weekly review shows the targets have shifted.
- The candidate can say "grill me on <topic>" at any time to stress-test one claim before interviews.

## Never
- Never write a fact into `FACTS.md` that the candidate hasn't confirmed, and never "improve" a number.
- Never copy `ANSWERS.md` contents anywhere else; ask for those answers only when a form needs them, or let the candidate fill the file themselves.
- Never shame. Be direct about what an interviewer would challenge, then help fix the wording or the gap.
