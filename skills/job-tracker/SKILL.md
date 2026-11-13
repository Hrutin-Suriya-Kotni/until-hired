---
name: job-tracker
description: "The tracker is the heart of until-hired: one record per job (found to offer), per interview round and per contact, with evidence for every status change, follow-ups due, duplicate checks and a funnel that shows which sources, tracks and scores lead to interviews. Use whenever a job is found, prepared, applied to, or changes status; when an email or interview arrives; when the candidate asks 'show my tracker', 'what's due', 'how is my search going'; and at the end of every session."
license: MIT
metadata:
  author: Hrutin Suriya Kotni
---
# Job tracker

If it isn't in the tracker, it didn't happen. Every other skill writes here, and the weekly review learns from here.

All commands: `python3 <workspace>/bin/tracker.py <command>` (add `-h` for options). Data: `<workspace>/tracker/` (CSV files the candidate can open in any spreadsheet app, plus `events.jsonl`, the audit trail).

## Job statuses
`found → shortlisted → preparing → ready → applied → assessment → interview → offer → accepted`
Endings: `rejected`, `withdrawn`, `closed` (no response / posting removed), `skipped` (didn't fit).

## Passing text to the tracker
Company, role, URL, notes, evidence and every other piece of text from outside go in a JSON file, never on the command line (agent-setup `references/safe-commands.md`):
1. `tracker.py new-input --agent <your name>` prints a fresh path in `<workspace>/.inbox/`.
2. Write the JSON object there with your file-writing tool.
3. Run the command with `--json <path>`; ids, statuses, dates and scores may stay as options. The tool deletes the file after it succeeds.

## Rules
1. **Check before work.** File `{"company": "...", "role": "...", "url": "..."}`, then `tracker.py check --json <path>` before preparing or applying.
   - exit 3 = duplicate: don't apply again;
   - exit 4 = the candidate is already interviewing or holding an offer there: don't apply again without asking them;
   - the JSON answer also shows how many applications went to that company in the last 30 days (`config.limits.per_company_per_30_days`).
2. **Record every job you score**, including skips. File `{"company", "role", "url", "source", "track", "notes": "<one-line reason>"}`, then `tracker.py add --json <path> --score <n> --status <found|shortlisted|skipped>`. It prints `{"id", "folder", "status"}`: use that `folder` (`materials/<id>-<name>`) for everything you write about the job. Skips teach the market picture too.
3. **Status changes need evidence.** File `{"evidence": "<confirmation text | email subject + date | candidate said so>"}`, then `tracker.py update --id N --status applied --json <path>`. Without evidence, keep the old status and add a note instead.
4. **Always set the next step** when something is open: `"next": "<action>"` in the file plus `--next-on YYYY-MM-DD` (follow up, prep, deadline, decision).
5. **Interviews:** file `{"round": "...", "with": "<names/roles>", "link": "<meeting link>"}`, then `tracker.py interview-add --json <path> --job-id N --when "YYYY-MM-DD HH:MM"`. After the round: file `{"went_well", "probed", "struggled", "outcome"}`, then `tracker.py debrief --json <path> --id <interview id>` (the self rating goes in the file as `"rating": "7/10"`).
6. **Applications the candidate made themselves** (found in email or told to you) get a row too, with `"source": "self"` and the real date as `--applied-on`.
7. **Contacts** (only when networking is on): `tracker.py contact-add --json <path>` checks duplicates by name + company; never contact the same person twice in 30 days.
8. **Use the tools, not hand edits**, so the lock, the spreadsheet safety and the event log apply. The candidate may edit the CSV files in a spreadsheet app when no session is running; save as **CSV UTF-8**. If a tool then says the columns look wrong, run `setup_workspace.py --dir <workspace>` (it repairs and keeps a backup).

## Follow-ups and staleness
`tracker.py due` lists, most urgent first: interviews in the next 48 hours, past interviews without a debrief, next steps due today, prepared applications waiting to be submitted, contacts to follow up, and applications with no news for 10+ days.
For a stale application: at most **one** polite follow-up where there is a real channel (recruiter email, portal message), written for that job. After 21 days with no reply, mark it `closed` with the note "no response". Ghosting is normal; it's not a verdict on the candidate.

## Reports
- `tracker.py list --status applied,interview` / `--min-score 75` / `--format json`; to filter by company, put `{"company": "..."}` in a file and add `--json <path>`
- `tracker.py interviews --upcoming`
- `tracker.py funnel` (or `--format json`): applied → response → positive (assessment or later) → interview → offer, by **source**, **track** and **score band**, plus the median days to the first response. This is the evidence the weekly review uses to move effort to what works.
- `tracker.py dashboard` writes `tracker/DASHBOARD.md` (needs attention, active processes, upcoming interviews, funnel, pipeline). Run it at the end of every session.

## Mirrors (optional)
If `config.tracker.mirror` names a connector (spreadsheet or notes app), copy the active rows there at the end of the session from `tracker.py export --table jobs` (a JSON array, header first, values already safe for spreadsheets). Write them as **raw values** (for Google Sheets: `RAW`, not `USER_ENTERED`) so nothing can turn into a formula. The mirror's id lives in `config.local.json`. The CSV files stay the source of truth; never read state back from the mirror.

## Never
- Never log an application as `applied` because a button was clicked: confirm the result first.
- Never delete rows. Wrong row → `--status closed` with a note. (The tracker has no delete command on purpose.)
- Never write personal data from `ANSWERS.md`, verification codes or email bodies into notes.
- Never put text from outside on a command line, and never delete `.lock` (exit 5 means: wait and rerun).
