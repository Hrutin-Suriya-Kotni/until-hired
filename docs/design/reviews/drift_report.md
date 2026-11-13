# Drift report: design v2 vs. the code

Checked on 2026-11-13. The design was compared with the code at the commit that adds this file. Each row is a place where they differ, and what was done about it.

| # | Design says | Code does | Decision |
|---|---|---|---|
| D1 | §5.3 field table: short text 300, long text 4,000 | Also uses tighter limits for some fields: skill and gap names 120, `track` in `jd` 60, lesson text 300, `platform` 40, `rating` and `severity` 20, `job_id` 10 | Keep the tighter limits; the table gives the defaults |
| D2 | §5.3: lists of text are accepted for list fields | Lists of text are accepted for any key and joined with ", " (commas inside items become spaces) | Keep: harmless for single-value fields, simpler code |
| D3 | Consolidated report M18 first listed "nothing submitted outside submit mode" as an invariant | Not checked: the tracker does not record which mode a submission used | Corrected in the report. LATER: log `mode` on `applied` updates, then audit it |
| D4 | §5.7: `--check` compares config types with the template | `null` in either the template or the config is treated as "any type"; ints and floats are treated as the same type | Keep: the template uses `null` for "not decided yet" |
| D5 | §6 C14: Dependabot | Dependabot covers GitHub Actions only: the tools have no third-party Python dependencies, and CI pins `skills-ref==0.1.1` | Keep |
| D6 | §5.6: scrubbing removes "codes" | 6+ digit runs are removed. Shorter codes (4–5 digits) are not, because they look like other numbers | Keep. Instructions forbid codes in notifications, and `detail: counts` (the default) sends no free text at all |
| D7 | §5.3: the hook covers "a mention that is not inside a read-only command" | Read-only means every segment of the command starts with a known inspection program (`cat`, `grep`, `sed`, `git`, …). A command mixing inspection with execution is checked as an execution | Keep (safer) |
| D8 | §9 S10: live run | Not yet done when this report was written | Tracked in `docs/live-run-2026-11.md` |

No other differences were found:
- Every control in §6 has the code and tests listed.
- The exit codes match §7.1 in every tool.
- The file table in §11 matches the repository.
