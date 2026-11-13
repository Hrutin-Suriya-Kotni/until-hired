# Contributing

Thanks for helping job seekers. Good contributions:
- **Platform notes:** form quirks, limits, safe ways to read job listings (public APIs first). Respect each site's terms; nothing that bypasses logins, bot checks or rate limits will be merged.
- **Interview material:** question banks per role, better debrief prompts.
- **Agent support:** install notes and capability checks for more agents.
- **Translations** of the skills and docs.
- **Tools:** improvements to the scripts in `skills/agent-setup/scripts/` (standard library only, Python 3.9+, backward-compatible CSV/JSON). Shared safety code lives in `uhlib.py`; use it rather than copying it.

## Layout
| Path | What |
|---|---|
| `skills/` | the 13 skills (each a `SKILL.md` folder) |
| `agents/` | the 5 subagents |
| `.claude-plugin/` | Claude Code manifest, marketplace, icon and the guard hook (`hooks/`) |
| `plugin.json` | Antigravity manifest and **the single source of the version number** |
| `.codex-plugin/`, `.agents/plugins/` | Codex manifests (experimental) |
| `tests/` | unit tests (standard library `unittest`) |
| `evals/` | behaviour scenarios for real agent runs |
| `docs/design/` | the design, its reviews and the drift report |

## Before a pull request (this is the only checklist; the PR template links here)
1. `python3 -m unittest discover -s tests -v` passes. It covers the tools, the security properties, the guard hook, the manifests and a lint of every command example in the skills.
2. `agentskills validate skills/<name>` for any skill you changed (`pip install skills-ref`), and `claude plugin validate .` if you have Claude Code.
3. Every tool command in a skill or agent file follows `skills/agent-setup/references/safe-commands.md`: text from outside goes in a `--json` file, never on the command line. The lint test enforces this.
4. No personal data in examples, tests or fixtures: use fictional candidates and companies (`example.com`). A test scans the repository for phone numbers, email addresses and spreadsheet ids.
5. Don't weaken the ground rules (honesty, consent, privacy, platform terms) in any skill.
6. A version bump changes `plugin.json` and every other manifest and `uhlib.__version__` together (a test checks they match), plus a CHANGELOG entry.

## Behaviour changes
Changes to skill wording can change what agents do in ways unit tests can't see. For those, run the relevant scenarios in `evals/scenarios.md` with at least one agent and include the outcome (and `setup_workspace.py --check --invariants` output) in the pull request.

## Security
Report vulnerabilities privately (see `SECURITY.md`), not in a pull request or issue.
