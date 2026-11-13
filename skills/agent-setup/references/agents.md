# Notes per agent product

Products change quickly. Treat these as starting points and confirm against what you can actually see and test.

## Claude Code (terminal, desktop or web)
- **Install:** as a plugin from this repository's marketplace (recommended: it adds the guard hook that blocks unsafe tool commands and asks before consent files change), or `python3 install.py --agent claude-code` (skills and agents only, no hook).
- **Subagents:** yes; the plugin ships `scout`, `applicant`, `inbox-keeper`, `researcher` and `reviewer`. Parallel runs are supported.
- **Memory file:** `CLAUDE.md` in the project folder.
- **Browser:** a Playwright MCP server pointed at a dedicated browser profile, or the Claude in Chrome extension (which drives the candidate's own Chrome; agree which sites you may open).
- **Notifications:** hooks can run `bin/notify.py` when Claude needs input or stops. See `notifications.md`.
- **Permissions:** see `permissions.md` for allow / ask / deny rules that fit until-hired.
- **Inbox:** an email MCP server or connector, if the candidate has one.

## Claude app (web, desktop, mobile)
- **Install:** upload the skill folders as custom skills, if your plan offers it, or paste `until-hired/SKILL.md` into a project's instructions and attach the other skills as files.
- **Connectors** (for example Gmail, Google Drive, Google Sheets) can serve as the inbox and a tracker mirror.
- Subagents, browser control, scheduled tasks and push notifications depend on the plan and the surface: check the tool list.
- Files persist only where the product gives you a persistent workspace. If it doesn't, keep the workspace in a connected folder on the candidate's computer. A synced drive works but sends private answers to that cloud too; say so and let the candidate choose.

## Google Antigravity (agy CLI / IDE)
- **Install:** `agy plugin install https://github.com/Hrutin-Suriya-Kotni/until-hired`, or `python3 install.py --agent antigravity` (copies `skills/*` to `.agents/skills/` and `agents/*` to `.agents/agents/` in the current folder).
- **Memory file:** `AGENTS.md` in the workspace folder.
- **Subagents:** yes. Don't list MCP tool names in a subagent's `tools:` frontmatter (it can break the subagent's start); let it inherit MCP tools instead.
- **Browser:** a Playwright MCP server in `.agents/mcp_config.json`, attached over CDP to a separate Chrome profile.
- **Notifications:** hooks (`~/.gemini/config/hooks.json`) that run `bin/notify.py` (never a raw `curl` with the topic). Hooks may not fire for subagents' tool calls, so important checks live inside the tools, not only in hooks.
- **Guard:** the Claude Code guard hook does not run here, so the safe-command rules are instructions only. Keep "ask before running commands" on for anything outside `<workspace>/bin/`.
- Approval prompts for ad-hoc commands slow long runs: prefer the workspace tools (`tracker.py`, `knowledge.py`) over one-off scripts.

## Other agents (Codex CLI, Gemini CLI, Cursor, GitHub Copilot, ...)
- **Codex (experimental):** `codex plugin marketplace add Hrutin-Suriya-Kotni/until-hired`, or `python3 install.py --agent codex`.
- If the product reads `SKILL.md` folders, copy the skills into its skills folder (`python3 install.py --agent generic --target <folder>`).
- If it reads `AGENTS.md`, put the always-on block from `agent-setup` §6 there.
- Otherwise paste `until-hired/SKILL.md` as the system or project instructions and keep the other skills as reference files.
- Without subagents, use solo mode: same steps, one at a time, with the reviewer checklist.
