# How to use until-hired

1. [The idea](#1-the-idea)
2. [Day 0: install, setup, intake](#2-day-0-install-setup-intake)
3. [Every day](#3-every-day)
4. [The tracker](#4-the-tracker)
5. [Skill gaps and the knowledge graph](#5-skill-gaps-and-the-knowledge-graph)
6. [Recommendations and the weekly review](#6-recommendations-and-the-weekly-review)
7. [Interviews](#7-interviews)
8. [Offers and the finish line](#8-offers-and-the-finish-line)
9. [Subagents: team, sequential or solo](#9-subagents-team-sequential-or-solo)
10. [Notifications](#10-notifications)
11. [Making it yours](#11-making-it-yours)
12. [Phrases cheat sheet](#12-phrases-cheat-sheet)
13. [Troubleshooting and FAQ](#13-troubleshooting-and-faq)

## 1. The idea
Sending more applications rarely fixes a job search. What helps is knowing exactly what you can prove, aiming at roles where that proof matters, applying with materials that sound like you, never losing track of a process, and closing the gaps the market keeps pointing at. until-hired does all of that as one loop and keeps the evidence in files you own.

## 2. Day 0: install, setup, intake
Allow about two hours in total, splittable across days.

**Install** (see the [README](README.md#quick-start)), open your agent in a private folder, and say "start my job search".

**Setup (10–15 min, skill `agent-setup`).** The agent:
1. creates your workspace (default `career/`);
2. checks your machine (memory, CPU, disk, Chrome, Python) and recommends how many browser agents it can run without freezing;
3. checks itself: can it launch subagents, in parallel? Does it have a browser tool, an email connector, notifications, scheduling?
4. asks you, one question at a time: platforms and the mode for each, inbox, notifications, daily limits, scoring thresholds, networking (off by default), schedule, and a separate browser profile for job sites;
5. saves everything to `config.json` and adds a short always-on block to your agent's memory file (`CLAUDE.md`, `AGENTS.md`...).

Platform modes:
| Mode | Agent | You |
|---|---|---|
| `discover` | finds and scores, prepares the kit | open the link and apply |
| `prepare` (default) | fills the whole form | review and click Submit |
| `submit` | submits when the score and answers allow | spot-check; only where the site allows automation and you accepted the risk |

**Intake (60–90 min, skill `candidate-intake`).** The agent interviews you in nine parts: goal and urgency, targets, your experience role by role, a proof check on every skill, gaps and history, your search so far, constraints, assets, and a final sign-off of your facts file. It will push back: "What did *you* do?", "What's the number?", "How would you prove that?". Be frank; that is how it avoids writing anything an interviewer can break. You can skip any question and resume any time.

What you get: `PROFILE.md`, `FACTS.md` (every line confirmed by you), `DO_NOT_CLAIM.md`, `PREFERENCES.md` (with your scoring weights), `STORIES.md` (interview stories), your current pipeline in the tracker, and a seeded knowledge graph.

## 3. Every day
Say "continue" (or schedule it). A session runs roughly like this:
1. reads the last session log and `tracker.py due`;
2. syncs your inbox: interviews, tests, rejections, offers, your own applications;
3. briefs you in six lines: what changed, what needs you, what it'll do now;
4. interviews first: prep sheets for anything in the next 48 hours, debriefs for anything past;
5. finds and scores new jobs on your sources, within your limits;
6. prepares kits and applies in each platform's mode;
7. (optional) drafts networking notes for you to send;
8. closes: dashboard, gap report, lessons, session log, a notification with counts.

What it needs from you: answering unknown form questions once (they're saved if you agree), clicking Submit in `prepare` mode, clearing hand-offs (logins, CAPTCHAs, codes), and three-line debriefs after interviews.

## 4. The tracker
`career/tracker/` holds `jobs.csv`, `interviews.csv`, `contacts.csv` (open them in any spreadsheet app), `events.jsonl` (every change, for the funnel) and `DASHBOARD.md`.

**Statuses:** `found → shortlisted → preparing → ready → applied → assessment → interview → offer → accepted`; endings `rejected`, `withdrawn`, `closed`, `skipped`.

**Rules the agent follows:**
- `check` before preparing or applying: duplicates (exit 3) and companies where you're already interviewing (exit 4) are never applied to again.
- Every job it scores is recorded, skips included, with the reason.
- Status changes need evidence: confirmation text, an email subject and date, or your word.
- Every open item has a next step and a date; `due` surfaces them.
- One polite follow-up at most for silent applications; after 21 days they're closed as "no response".

**Commands you can run yourself:**
```bash
python3 career/bin/tracker.py due                  # what needs attention, most urgent first
python3 career/bin/tracker.py list --status interview,offer
python3 career/bin/tracker.py funnel               # what converts, by source, track and score band
python3 career/bin/tracker.py dashboard            # writes tracker/DASHBOARD.md
python3 career/bin/tracker.py interviews --upcoming
```
Editing the CSVs by hand is fine; the agent re-reads them.

## 5. Skill gaps and the knowledge graph
`career/knowledge/` grows on its own:
- **Intake** adds your skills (each with a level: `evidenced`, `claimed`, `learning`, `none`) and your projects.
- **Every scored job description** adds what the market asks for (must-have vs nice-to-have) to `market.json`.
- **Every interview debrief or rejection reason** adds a gap.
- **Every finished proof project** moves a skill to `evidenced`.

`knowledge.py gaps --write` ranks them in `GAPS.md` by (times asked + times required + 3 × interview mentions):
| Class | Meaning |
|---|---|
| STRENGTH | evidenced and in demand: lead with it |
| DEEPEN | a strength interviewers still probed: prepare deeper |
| UNPROVEN | you claim it, nothing to show: biggest interview risk |
| LEARNING | in progress: finish the proof |
| MISSING | in demand, not yours: close it or filter those jobs out |
| INTERVIEW | raised in interviews though rarely in job posts |

The shares become meaningful after about 20 scored job descriptions. `knowledge.py summary --write` gives a readable overview in `KNOWLEDGE.md`.

## 6. Recommendations and the weekly review
`growth-engine` writes `RECOMMENDATIONS.md`: for the top gaps, whether to close them or route around them, the smallest **proof project** an interviewer would accept (1–2 weeks, public, measurable), resources, honest wording until it's done; plus positioning (what to lead with) and targeting (which sources and roles actually convert, from your funnel).

**Weekly review (30 min, on your chosen day):** numbers → what worked → top gaps → your decisions (learning goal, proof project, platforms, limits, weights) → next week's plan → a short check-in on how you're holding up. Saved in `knowledge/reviews/`.

## 7. Interviews
- **Prep sheet** for every round, readable in 15 minutes: likely questions (most likely first), your real stories and numbers, honest lines for weak spots, company facts with sources, questions to ask them, logistics. It starts from your known gaps.
- **Mock interviews:** "mock interview for <company>" or "grill me on <topic>". One question at a time, follow-ups like a real interviewer, a score and a better answer after each.
- **Debrief the same day:** three lines (went well, probed, struggled) + a self-rating. Weak spots become tracked gaps, so the same weakness doesn't cost two interviews.

## 8. Offers and the finish line
`offer-coach` captures every term, chases verbal promises into writing, compares options side by side under *your* priorities, and prepares honest negotiation points (never invented competing offers). When you accept: polite withdrawal drafts for other processes, a resignation checklist, a final retro, and the daily routine stops.

## 9. Subagents: team, sequential or solo
Setup tests your agent and picks one:
- **Team mode** (subagents in parallel): `scout` per source, `applicant` per platform, `inbox-keeper`, `researcher`, `reviewer`, at most `max_parallel_agents` at once (the lower of what the agent supports and what your RAM allows, roughly 1 browser agent under 8 GB, 2 at 8–12 GB, 3 at 12–24 GB, 5 at 24–48 GB).
- **Sequential mode:** same roles, one after another.
- **Solo mode:** the main agent does everything and runs the reviewer checklist on its own work.
Every subagent gets only file paths and tracker ids, never the whole conversation, and returns `lessons` for `self-improve`.

## 10. Notifications
Choose at setup: the agent's native notifications, free phone push through [ntfy](https://ntfy.sh) (works with any agent; the topic stays in `config.local.json`), hooks that ping you when the agent waits for you (Claude Code, Antigravity), a digest file, or none. You get pinged for interviews, tests, offers, deadlines and blockers. By default a notification only says how many updates of which kind are waiting ("until-hired: 1 interview update"), so nothing about your search shows on a lock screen; you can switch to company names. Quiet hours are respected except for urgent items.

## 11. Making it yours
- Scoring weights and thresholds: `config.json → scoring` and `PREFERENCES.md`.
- Platforms, modes, limits: say "change my platforms" or edit `config.json`.
- Corrections stick: tell the agent when it's wrong; `self-improve` writes it down, and proposes skill changes for you to approve.
- Platform quirks the agent discovers are proposed as lessons at the end of a session; the ones you approve go into `knowledge/LEARNINGS.md` (`knowledge.py lessons` shows what's waiting).
- Which sites may receive your form answers: `config.json → apply.allowed_hosts` (known hiring systems are allowed already).
- Health check any time: `python3 <agent-setup skill>/scripts/setup_workspace.py --dir career --check`.

## 12. Phrases cheat sheet
| Say | Happens |
|---|---|
| start my job search / continue / what's next | the daily session |
| set up / change my platforms / turn on notifications | setup questions |
| grill me / update my profile / I learned X / I shipped Y | intake (or the part that changed) |
| find jobs / score this job <link> | discovery and scoring |
| prepare #12 / apply to #12 | kit and application |
| what's due / show my tracker / how is my search going | tracker reports |
| prep me for <company> / mock interview / debrief | interview coach |
| what should I learn / skill gaps / weekly review | growth engine |
| I got an offer / compare offers | offer coach |

## 13. Troubleshooting and FAQ
- **"No tracker at …"** → run setup again; it never overwrites your files.
- **The laptop slows down** → lower `max_parallel_agents`; make sure agents close their tabs.
- **A platform keeps blocking** → switch it to `discover` mode; don't fight it.
- **Scores feel wrong** → ask for a calibration: the agent shows five scored jobs and adjusts weights with you.
- **Can it apply to 200 jobs a day?** It can be configured to, but reply rates drop, platforms restrict accounts, and recruiters notice. The funnel will show you what volume actually works.
- **Where is my data?** Only in your workspace and whatever connectors you chose. `profile/ANSWERS.md` is git-ignored.
