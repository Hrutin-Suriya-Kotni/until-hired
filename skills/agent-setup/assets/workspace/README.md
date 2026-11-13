# Career workspace

Everything the agent knows about you and your search lives here, in plain files you can read and edit.

| Path | What it is | Who writes it |
|---|---|---|
| `config.json` | Your choices: agent, platforms, inbox, notifications, submit mode, limits | `agent-setup`, with you |
| `profile/PROFILE.md` | Who you are, what you want, your constraints | `candidate-intake`, with you |
| `profile/FACTS.md` | Verified career facts. **The only source for resumes, answers and messages** | `candidate-intake`; you approve every line |
| `profile/DO_NOT_CLAIM.md` | Skills and claims the agent must never make | `candidate-intake` |
| `profile/PREFERENCES.md` | Roles, locations, pay, filters, scoring weights | `candidate-intake` |
| `profile/STORIES.md` | Interview stories (situation, action, result) | `candidate-intake`, `interview-coach` |
| `profile/ANSWERS.md` | Form answers: *Basic* (phone, notice) and *Sensitive* (pay, visa, date of birth). **Private** | you |
| `tracker/` | Every job, interview and contact, plus the event log | `job-tracker` |
| `knowledge/` | Skill graph, market demand, gaps, lessons | `growth-engine`, `self-improve` |
| `materials/<id>-<company>/` | Tailored resume, answers, prep sheets (folder name given by `tracker.py folder`) | `application-kit`, `interview-coach` |
| `proposals/` | Changes the agent suggests to its own skills (you approve) | `self-improve` |
| `SESSION_LOG.md` | One short entry per session: what happened, what's next | `until-hired` |
| `config.local.json` | Secrets: ntfy topic, mirror id, inbox address. **Never commit** | `agent-setup`, with you |
| `.inbox/` | Short-lived input files for the tools (deleted after use) | the agent |
| `bin/` | `tracker.py`, `knowledge.py`, `notify.py`, `check_system.py`, `uhlib.py` | copied by `agent-setup` (refreshed on every setup) |

Back this folder up. It is private by default: `.gitignore` keeps `profile/`, `materials/`, contacts, reviews,
secrets and notifications out of git. Check its health any time:

    python3 <skill folder>/scripts/setup_workspace.py --dir <this folder> --check

To delete everything when you're hired: delete this folder (and any mirror sheet or ntfy topic you created).
