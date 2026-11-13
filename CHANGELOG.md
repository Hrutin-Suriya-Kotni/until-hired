# Changelog

## 1.0.0 (2026-11)
First public release. Designed and reviewed with the Elephant Goldfish Model; see `docs/design/`.

**Security and reliability**
- Every tool command accepts `--json FILE` (keys = option names). Text from job posts, emails and pages never goes on a command line; `tracker.py new-input` gives each agent a unique input file in `.inbox/`, deleted after use.
- Claude Code guard hook: blocks tool commands with free-text options, `$( )`, backticks, heredocs, pipes or chains, and asks the candidate before edits to consent files, private answers, lessons and the tools.
- Shared core `uhlib.py`: text sanitiser (control, bidirectional and zero-width characters), reversible spreadsheet-formula neutralisation, atomic writes with `.bak` copies, detection of files changed by other programs, an operating-system lock released automatically if a process dies, private file permissions.
- `tracker.py disclose`: private answers only on known hiring systems or hosts the candidate allows; a log of which fields went where (never the values).
- Material folders are named by the tracker (`materials/<id>-<name>`).
- Lessons wait for the candidate's approval (`knowledge.py lesson` / `lessons --approve`).
- Verification codes are never passed between agents or to forms.
- `notify.py`: counts-only notifications by default, topic kept in `config.local.json`, never on a command line.
- `setup_workspace.py` upgrades and repairs workspaces (secrets moved to `config.local.json`, CSV headers repaired with backups) and has a `--check` health report and `--invariants` data audit.

**Packaging**
- One repository, many agents: Claude Code plugin and marketplace, Antigravity manifest, Codex manifests (experimental), and `install.py` (never replaces folders it didn't install).
- 58 unit tests on Linux, macOS and Windows; pinned CI actions; Dependabot.
- Live run by an agent that had never seen the skills; its findings are fixed (`docs/live-run-2026-11.md`).

## 0.1.0 (2026-11, not published)
Internal preview: 13 skills, 5 subagents, standard-library tracker and knowledge-graph tools.
