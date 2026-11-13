# Security policy

## Reporting a vulnerability
Please report security problems privately through GitHub: **Security → Report a vulnerability** on this repository (a private security advisory). Don't open a public issue for them, and don't include anyone's personal data in a report.

You'll get an acknowledgement within 7 days. Fixes are released as a new version with a CHANGELOG entry; reporters are credited unless they ask not to be.

## In scope
- The workspace tools (`tracker.py`, `knowledge.py`, `notify.py`, `uhlib.py`, `check_system.py`, `setup_workspace.py`), the Claude Code guard hook (`.claude-plugin/hooks/guard.py`) and `install.py`: code execution, data corruption or loss, unsafe file permissions, injection into spreadsheets or shells.
- The skills and subagent instructions: anything that leads an agent to leak personal data, act without the candidate's consent, claim facts that aren't verified, or follow instructions planted in job posts, emails or web pages.
- Plugin manifests and CI configuration.

## Out of scope
- Problems in the AI agent products themselves, or in job platforms (report those to their vendors).
- A user changing the skills to remove the safety rules.

## Supported versions
Only the latest release receives fixes. Install a tagged release (see README) if you want to review what you run.

## How the project protects users
See [SAFETY.md](SAFETY.md) for the rules, and the design notes in [docs/design/until-hired-1.0.md](docs/design/until-hired-1.0.md) for which protections are enforced by code, tests or the hook, and which rely on the agent following instructions. The independent reviews are in [docs/design/reviews](docs/design/reviews).
