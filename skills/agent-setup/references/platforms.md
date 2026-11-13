# Platforms and sources

Ask which of these the candidate uses; never assume. Record each in `config.json → platforms`.

## Modes and site rules
- Read each site's terms before choosing a mode. Several large networks forbid bots and automated activity; for example, LinkedIn's User Agreement prohibits using bots or other automated methods to access the service or send messages. Use `discover` mode there: job-alert emails (read by `inbox-sync`), saved searches the candidate opens, links they paste.
- Even where automation is allowed, keep daily caps modest. Accounts get restricted for volume, and recruiters notice copy-paste applications.
- The candidate signs in to every site themselves. You never type a password.

## Usually safe to automate: company career pages and their public job APIs
Many companies post jobs through an applicant-tracking system with a public, documented job-board API. Reading these needs no account:
- Greenhouse: `https://boards-api.greenhouse.io/v1/boards/<company>/jobs?content=true`
- Lever: `https://api.lever.co/v0/postings/<company>?mode=json`
- Ashby: `https://api.ashbyhq.com/posting-api/job-board/<company>`
Other common systems: Workable, SmartRecruiters, Workday, Zoho Recruit, iCIMS, Teamtailor. Their application forms are usually fine in `prepare` mode.

## Common sources by type (pick with the candidate)
| Type | Examples | Typical mode |
|---|---|---|
| Professional networks | LinkedIn | discover (alerts, pasted links) |
| Big job boards | Indeed, Glassdoor, Naukri, Monster, Seek, StepStone, Reed | discover or prepare, per the site's terms |
| Startup boards | Wellfound, Y Combinator's Work at a Startup, startup.jobs | prepare |
| Tech-specific boards | hirist, Instahyre, Dice, Hacker News "Who is hiring" | prepare / discover |
| Remote boards | We Work Remotely, Remote OK, Remotive | prepare |
| Company career pages | target companies' own sites (ATS above) | prepare or submit |
| Research and academia | lab pages, university job portals, fellowship programmes | discover + materials |
| Government / public sector | national portals | discover |

## What to record per platform
```json
{"name": "greenhouse-boards", "enabled": true, "mode": "prepare", "daily_cap": 10,
 "signed_in_by_candidate": false, "notes": "target list in PREFERENCES.md"}
```
Platform quirks discovered while working (form fields, waits, limits such as "one application per company every 60 days") go to `knowledge/LEARNINGS.md` through `self-improve`.
