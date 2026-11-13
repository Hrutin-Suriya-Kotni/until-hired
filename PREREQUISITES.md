# Prerequisites

## 1. What the agent needs to load and run the skills
**Required**
- An AI agent that can use [Agent Skills](https://agentskills.io) (`SKILL.md` folders), such as Claude Code, the Claude app with custom skills, or Google Antigravity. Agents that can't load skills can still use `until-hired/SKILL.md` pasted as instructions.
- Permission to **read and write files** in your workspace folder.
- Permission to **run shell commands** and **Python 3.9+** (the tools use only the standard library; nothing to `pip install`). See `skills/agent-setup/references/permissions.md` for permission settings that fit.
- An **always-on memory file** the agent reads every session (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`...); setup adds a short block there so the ground rules load every time.

**Recommended (setup detects these and adapts)**
| Capability | Without it |
|---|---|
| Subagents, ideally in parallel | solo mode: same steps, one at a time |
| A browser tool (Playwright MCP, Claude in Chrome, a built-in browser) | the agent prepares everything; you open links and submit |
| An email connector (Gmail, Outlook) | paste or forward important emails, or answer one check-in question per session |
| Notifications (native push, hooks, ntfy) | a digest file each session |
| Scheduled tasks | say "continue" when you sit down |
| Web search | discovery relies on your sources and pasted links; no market research |

## 2. What your machine needs
- macOS, Linux or Windows with Python 3.9+.
- **Memory decides how many browser agents can run at once:** under 8 GB → 1; 8–12 GB → 2; 12–24 GB → 3; 24–48 GB → 5; more → up to 8. `check_system.py` measures this for you.
- 5 GB+ free disk, a stable connection, and a plugged-in laptop for long sessions (a sleeping computer stops every agent).
- For browser automation: Chrome or Chromium, and a **separate browser profile for job sites** so your personal browsing is never touched.

## 3. What you need to bring
- **Your resume(s)** in any format, plus links (LinkedIn, GitHub, portfolio) and, ideally, a few things you've written (so drafts sound like you).
- **60–90 minutes for the intake**, splittable. Honest answers are the whole point: the agent can only defend what it knows to be true.
- **Accounts on the platforms you choose, signed in by you** in the job-site browser profile. The agent never logs in for you.
- **30 minutes a week** for the review, and 3-line debriefs after interviews.
- **A private place for the workspace**: a local folder that only your user account can read. It holds personal data, so avoid cloud-synced folders and shared or public git repositories (setup warns about both). Back it up the way you back up other private documents.

## 4. What the agent needs to learn before it's useful
The skills give the agent the *method*. Your workspace gives it *you*. Before results get good, it needs:
| It needs | Comes from | Ready when |
|---|---|---|
| Your verified facts and do-not-claim list | intake parts 3, 4, 9 | you've signed off `FACTS.md` |
| Your targets, filters and scoring weights | intake part 2, setup | `PREFERENCES.md` filled; calibrated after ~20 scored jobs |
| Your live pipeline | intake part 6, inbox sync (60-day look-back) | every open process is in the tracker |
| What the market asks for | every scored job description | about 20 JDs for a usable gap report |
| What works for you | the tracker's funnel | about 30 applications for meaningful conversion numbers |
| Platform quirks | `self-improve` lessons | grows with every session |

Until those thresholds are reached, the agent says so instead of overstating patterns.
