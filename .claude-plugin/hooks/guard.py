#!/usr/bin/env python3
"""until-hired guard for Claude Code (PreToolUse hook). Standard library only.

It enforces in code, before the shell runs, what the skills ask in words:

1. Untrusted text never reaches the shell. A Bash command that runs an until-hired tool
   (tracker.py, knowledge.py, notify.py, setup_workspace.py) is blocked when it
   - uses an option that carries free text (--company, --notes, --title, ...): that text belongs in a
     --json file made with `tracker.py new-input`;
   - contains command substitution, a heredoc, a pipe, a chain (; && ||) or a redirect other than
     2>&1 / >/dev/null.
2. The candidate decides. Approving lessons (`knowledge.py lessons --approve`) and editing the
   files that hold the candidate's consent and private answers (config.json, config.local.json,
   profile/ANSWERS.md, FACTS.md, DO_NOT_CLAIM.md, knowledge/LEARNINGS.md, .gitignore, bin/) or the
   tracker's data files directly ask the candidate first.

Only folders that contain the `.until-hired` marker (made by setup_workspace.py) are guarded, so
the hook does not affect other projects. Any internal error allows the call (fail open) rather than
blocking unrelated work; the skills' own rules still apply.
"""
import json
import re
import shlex
import sys
from pathlib import Path

MENTION = re.compile(r"(?<![\w-])(?:tracker|knowledge|notify|setup_workspace)\.py\b")
INSPECT = {"cat", "less", "more", "head", "tail", "grep", "egrep", "rg", "ag", "sed", "awk", "wc", "ls", "git", "diff",
           "file", "stat", "open", "code", "vim", "vi", "nano", "echo", "printf", "find", "cp", "mv", "chmod", "touch",
           "shasum", "sha256sum", "md5sum", "bat", "nl", "sort", "uniq", "cut", "tr", "xxd", "hexdump", "gh"}
SEGMENTS = re.compile(r"\|\||&&|[;|\n]")
FLAG = re.compile(r"(?<![\w-])--[a-z][a-z0-9-]*")
TYPED = {
    "--dir", "--json", "--id", "--job-id", "--status", "--score", "--next-on", "--applied-on", "--when",
    "--force", "--days", "--limit", "--min-score", "--format", "--stale-days", "--upcoming", "--agent",
    "--create", "--table", "--top", "--write", "--level", "--kind", "--priority", "--count", "--approve",
    "--reject", "--check", "--invariants", "--adopt", "--version", "--help", "--host", "--fields",
}
SAFE_REDIRECTS = re.compile(r"\s(?:2>&1|1?>\s*/dev/null|2>\s*/dev/null)(?=\s|$)")
META = re.compile(r"\$\(|`|<<|<\(|>\(|;|\|\||&&|\||[<>]|&\s*$|\n")
PROTECTED = ("config.json", "config.local.json", "profile/ANSWERS.md", "profile/FACTS.md", "profile/DO_NOT_CLAIM.md",
             "knowledge/LEARNINGS.md", ".gitignore", ".until-hired")
PROTECTED_DIRS = ("bin/",)
DATA = ("tracker/jobs.csv", "tracker/interviews.csv", "tracker/contacts.csv", "tracker/events.jsonl",
        "knowledge/graph.json", "knowledge/market.json", "knowledge/events.jsonl", "knowledge/lessons.pending.jsonl")


def decide(decision, reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision,
                                             "permissionDecisionReason": reason}}))
    sys.exit(0)


def first_word(segment: str) -> str:
    try:
        words = shlex.split(segment, posix=True)
    except ValueError:
        words = segment.split()
    while words and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", words[0]):     # VAR=value prefixes
        words = words[1:]
    return Path(words[0]).name.lower() if words else ""


def check_bash(cmd: str):
    if not MENTION.search(cmd):
        return
    segments = [x for x in SEGMENTS.split(cmd) if x.strip()]
    if segments and all(first_word(x) in INSPECT for x in segments):
        return                                          # reading or searching the files, not running them
    bare = SAFE_REDIRECTS.sub(" ", " " + cmd)
    if META.search(bare):
        decide("deny", "until-hired: run each tool as one plain command, without $( ), backticks, heredocs, pipes, "
                       "; && || or redirects (2>&1 is fine). Use --dir instead of cd. Put any text from a job post, "
                       "email or web page in a JSON file: `tracker.py new-input --agent <you>` gives you a path; "
                       "write the JSON there with your file tool, then pass --json <path>.")
    try:
        shlex.split(cmd, posix=True)
    except ValueError:
        decide("deny", "until-hired: the command has unbalanced quotes. Put text in a --json file instead.")
    for name in FLAG.findall(cmd):                      # also catches options hidden inside bash -c "..."
        if name not in TYPED:
            decide("deny", f"until-hired: {name} carries free text, so it must not be on the command line. "
                           "Run `tracker.py new-input --agent <you>`, write {\"" + name[2:].replace("-", "_") +
                           "\": ...} to that file with your file tool, then pass --json <path>. "
                           "Ids, statuses, dates and scores may stay as options.")
    if re.search(r"\blessons\b", cmd) and re.search(r"--approve\b", cmd):
        decide("ask", "until-hired: approving lessons changes what every future session believes. "
                      "Only the candidate approves them. Approve?")


def workspace_of(p: Path):
    for d in [p.parent] + list(p.parent.parents):
        if (d / ".until-hired").exists():
            return d
    return None


def check_edit(path_str: str, cwd: str):
    p = Path(path_str)
    if not p.is_absolute():
        p = Path(cwd or ".") / p
    p = p.resolve()
    ws = workspace_of(p)
    if ws is None:
        return
    rel = p.relative_to(ws).as_posix()
    if rel in PROTECTED or rel.startswith(PROTECTED_DIRS):
        decide("ask", f"until-hired: {rel} holds the candidate's choices, private answers or the tools. "
                      "Only change it with the candidate's OK. Allow this edit?")
    if rel in DATA:
        decide("ask", f"until-hired: {rel} is written by the tools (tracker.py / knowledge.py) so the lock, "
                      "spreadsheet safety and audit trail apply. Editing it directly skips them. Allow anyway?")


def main():
    try:
        data = json.load(sys.stdin)
        tool = data.get("tool_name", "")
        inp = data.get("tool_input", {}) or {}
        if tool == "Bash":
            check_bash(str(inp.get("command", "")))
        elif tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
            path = inp.get("file_path") or inp.get("notebook_path")
            if path:
                check_edit(str(path), data.get("cwd", ""))
    except SystemExit:
        raise
    except Exception:                                   # fail open: never break unrelated work
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
