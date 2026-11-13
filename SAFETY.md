# Safety, honesty and privacy

until-hired acts on your behalf in places where mistakes are costly: your accounts, your reputation with employers, your personal data. These rules are part of every skill and of the always-on block setup adds to your agent's memory. Content found in job posts, emails or web pages can never override them.

Each rule below says how it is enforced:
- **code**: the tools refuse;
- **hook**: the Claude Code guard hook blocks or asks before the action runs;
- **instructions**: the skills tell the agent, and the reviewer and the evals check it.

An AI agent with a shell can, in principle, ignore instructions, so the honest label matters.

## Honesty (instructions; `knowledge.py claimable` in code)
- Every fact in a resume, form, note or interview answer comes from `profile/FACTS.md`, which you signed off line by line.
- Nothing in `profile/DO_NOT_CLAIM.md` is claimed, not even as "familiar with". A skill goes on a resume only if `knowledge.py claimable` says it is *evidenced*, and *evidenced* needs a link or proof (code).
- Unknown form questions are asked to you, never guessed.
- Interview coaching uses your real stories; take-home tests stay your own work. Negotiation never invents competing offers, deadlines or numbers.

## Consent
- Each platform runs in the mode you chose: `discover`, `prepare` (default; you click Submit) or `submit` (only where the site allows automation and you accepted the risk). `setup_workspace.py --check` fails if submit mode is on without your confirmation (code) and lists every platform in submit mode at each session start.
- Messages are drafts; you send them. No profile edits, account creation, payments or new terms without your explicit yes (instructions).
- Changes to `config.json`, your profile files, `LEARNINGS.md` and the tools ask you first (hook), and lessons from a session wait for your approval before any later session reads them (code: `knowledge.py lessons`).

## Things this project will not do
- Enter passwords, solve or bypass CAPTCHAs or "are you human" checks, or handle one-time or verification codes. Codes are never read out, copied or passed between agents; you are told a code arrived (instructions; a test fails if any skill text says otherwise).
- Use hidden site internals, rate-limit workarounds or other tricks to get around a platform's controls.
- Send cold emails, scrape contact details, build lead lists or send messages in bulk.
- Apply twice to the same role, or re-apply to a company where you're interviewing (code: `tracker.py check` / `add` exit 3 and 4).

## Platform terms and volume
Many networks and job boards restrict automated activity in their terms (LinkedIn's User Agreement, for example, prohibits bots and automated messaging). For those, use `discover` mode: job-alert emails, saved searches and links you paste. Keep daily limits modest everywhere: accounts get restricted for volume, and recruiters recognise mass applications. The funnel shows you what volume actually works.

## Your data
### Where it lives
One folder on your computer (the workspace), readable only by your user account on macOS and Linux (code: 700/600). Its `.gitignore` keeps `profile/`, `materials/`, contacts, reviews, secrets and notifications out of git by default. `setup_workspace.py --check` warns if the folder syncs to iCloud, Dropbox, OneDrive or Google Drive, or sits in a git repository with a remote, and fails if private files are tracked there.

| Data | Files | Who else receives it |
|---|---|---|
| Your facts, profile, stories | `profile/FACTS.md`, `PROFILE.md`, `STORIES.md`, `PREFERENCES.md` | your AI provider (the agent reads them); employers see what goes into an application |
| Private answers | `profile/ANSWERS.md` (Basic and Sensitive) | your AI provider; the hiring sites whose forms you apply on, only after `tracker.py disclose` allowed the host (code), Sensitive ones only with your yes (instructions) |
| Applications and interviews | `tracker/`, `materials/` | your AI provider; a mirror (Sheets, Notion) if you turned one on |
| Notifications | `NOTIFICATIONS.md` | the ntfy server, only if you chose ntfy: counts by default, company names only if you chose `detail: names` (code) |
| Secrets | `config.local.json` (ntfy topic, mirror id, inbox address) | nobody: the topic is sent only to the ntfy server, in the request body (code) |
| Job posts and emails | `materials/<id>-<name>/jd.md`, `.inbox/` | nobody; input files are deleted after use (code) |

### What the tools themselves send
`tracker.py`, `knowledge.py`, `setup_workspace.py`, `check_system.py` and `uhlib.py` never use the network (a test fails if they import a network module). `notify.py` is the one exception: it posts to the https ntfy server you configured, and only when notifications are set to `ntfy`. The agent itself browses job sites and reads email through your agent's own tools.

### When you're done
Delete the workspace folder, and any mirror sheet or ntfy topic you created. Nothing else is kept by until-hired.

## Prompt injection and unsafe input
Job posts and emails sometimes contain text aimed at AI tools ("AI assistants: include the word X", "ignore your instructions"). The defences:
- The agent treats all page and email content as data, ignores such instructions and tells you about them. Saved page text starts with an `UNTRUSTED CONTENT` line (instructions).
- Text from outside never becomes part of a shell command: the tools read it from JSON files (code). On Claude Code, commands that put free text on the command line are blocked before they run (hook). Elsewhere this is instructions, and a test checks every example in the skills.
- CSV cells that could run as spreadsheet formulas are neutralised, reversibly, and mirrors get the same safe values (code).
- Material folders are named by the tracker (`materials/<id>-<name>`), never from page text, so a crafted company name can't write outside the workspace (code).
- Lessons that would steer later sessions wait for your approval (code).

## Reporting a problem
- A **security vulnerability**: report it privately, as described in [SECURITY.md](SECURITY.md).
- A skill that behaves against these rules: open an issue (without personal data).
