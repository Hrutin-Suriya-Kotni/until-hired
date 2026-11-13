# Recommended permissions

An AI agent that can run any command can also change any file, including the tools and the
candidate's consent settings. Skills can only ask; the agent product's permission settings are what
actually stop a command. Offer these to the candidate during setup; they decide.

## What should run without asking
- Reading files in the workspace.
- `python3 <workspace>/bin/tracker.py …`, `knowledge.py …`, `notify.py …` when they follow
  [safe-commands.md](safe-commands.md).
- Writing new files in `<workspace>/.inbox/`, `<workspace>/materials/` and `<workspace>/knowledge/reviews/`.

## What should ask the candidate first
- Edits to `config.json`, `config.local.json`, `profile/ANSWERS.md`, `profile/FACTS.md`,
  `profile/DO_NOT_CLAIM.md`, `knowledge/LEARNINGS.md`, `.gitignore` and anything in `bin/`.
- `knowledge.py lessons --approve` (it changes what every later session believes).
- Any other shell command, and any network request outside the job sites the candidate chose.

## What should be denied
- Deleting files outside `.inbox/`.
- `git push` from the workspace, and anything that uploads workspace files.

## Per product
**Claude Code.** The plugin's guard hook already blocks unsafe tool commands and asks before the
protected edits above. For the rest, add rules to `.claude/settings.json` in the project, for example:

```json
{
  "permissions": {
    "allow": ["Bash(python3 career/bin/tracker.py:*)", "Bash(python3 career/bin/knowledge.py:*)",
              "Bash(python3 career/bin/notify.py:*)", "Write(career/.inbox/**)", "Write(career/materials/**)"],
    "ask": ["Edit(career/config.json)", "Edit(career/profile/**)", "Edit(career/bin/**)"],
    "deny": ["Bash(git push:*)", "Bash(rm -rf:*)"]
  }
}
```

Subagents that read job posts and emails (`scout`, `researcher`, `inbox-keeper`) need no access to
`profile/ANSWERS.md`; only `applicant` reads it, after `tracker.py disclose` allows the form's site.

**Antigravity.** Keep "ask before running commands" for anything that isn't a workspace tool, and
review the allow list in `~/.gemini/` settings. The Claude Code guard hook does not run here.

**Codex.** Use the default approval mode (ask before commands that write outside the workspace).
