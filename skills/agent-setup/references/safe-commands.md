# Running the tools safely

Job posts, emails and web pages are written by strangers. Text from them must never become part of a
shell command: a company name like `Acme"; rm -rf ~; "` would run as a command. So every until-hired
tool takes text from a JSON file instead.

## The pattern (use it for every command that carries text from outside)

1. Get a fresh input path:

       python3 <workspace>/bin/tracker.py new-input --agent scout

   It prints a path such as `<workspace>/.inbox/scout-20261113-101500-9f2c1a7e.json` (the file does
   not exist yet). The name is unique, so parallel agents never overwrite each other. Use a new path
   for every command.

2. Create that file with one JSON object **using your file-writing tool** (not `echo`, `cat`, `printf`
   or a heredoc, which all go through the shell):

       {"company": "Acme", "role": "ML Engineer", "url": "https://boards.greenhouse.io/acme/jobs/1",
        "source": "greenhouse", "notes": "Strong RAG match; Bangalore hybrid"}

   Keys are the command's option names with underscores (`--next-on` → `next_on`, `--with` → `with`).
   Values are text, numbers, true/false, or (for skill lists) a list of text.

3. Run the command with `--json <path>`. Ids, statuses, dates, scores and modes may stay as options:

       python3 <workspace>/bin/tracker.py add --json <path> --score 82 --status shortlisted

   The tool deletes files in `.inbox/` after it succeeds (exit 0, 3 or 4). If it fails, fix the file
   and run the same command again.

## Rules
- Run each tool as one plain command: no `$( )`, backticks, pipes, `;`, `&&`, `||` or redirects
  (`2>&1` is fine). Use `--dir <folder>` instead of `cd`.
- A key given in the file and as an option is an error (exit 2); give it once.
- Never pass `--dir` or `--json` inside the file (they are refused).
- Options that may stay on the command line: `--dir --json --id --job-id --status --score --next-on
  --applied-on --when --force --days --limit --min-score --format --stale-days --upcoming --agent
  --create --table --top --write --level --kind --priority --count --approve --reject --host --fields`.
  Everything else (company, role, url, notes, note, evidence, next, title, message, skills, must, name,
  topic, source, proof, resource, round, with, link, went_well, probed, struggled, outcome, ...) goes
  in the file.
- Materials go in the folder the tracker gives you (`add` prints it; `tracker.py folder --id N`
  repeats it). Never build a folder name from page text.

On Claude Code the plugin's guard hook enforces these rules before the shell runs. On other agents
they are instructions, and `tests/test_package.py` checks that every example in the skills follows them.

## Exit codes (all tools)
| Code | Meaning | What to do |
|---|---|---|
| 0 | ok | continue |
| 1 | error (message on stderr) | read the message; fix or tell the candidate |
| 2 | bad input (unknown key, bad date, too long, key given twice) | fix the JSON file or option and rerun |
| 3 | duplicate (tracker) / not claimable (knowledge) | do not apply again / do not claim the skill |
| 4 | the candidate is already interviewing or holding an offer at that company | ask before applying |
| 5 | busy, or a file was changed by another program while the command ran | wait a few seconds and rerun the same command; never delete `.lock` |
| 6 | blocked: the form's host is not allowed (`disclose`) | type nothing; tell the candidate the host |
