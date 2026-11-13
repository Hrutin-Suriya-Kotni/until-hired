# Notifications

The candidate is often away from the screen. Notify them when something needs them, and stay quiet otherwise.
Every notification goes through `bin/notify.py`, which keeps a full copy in `NOTIFICATIONS.md` on this
computer and decides what may leave it.

## What to send
| Priority | Kind | When | Example (what the candidate's phone shows with `detail: counts`) |
|---|---|---|---|
| urgent | blocked | a login, CAPTCHA or code is blocking a platform the candidate asked you to run | "until-hired: 1 blocked update" |
| high | interview / assessment / offer / deadline | an invite, a deadline, an offer, a prep sheet, a decision needed today | "until-hired: 1 interview update" |
| default | session | end of a session (`count` = items that need the candidate) | "until-hired: 3 session updates" |
| low | other | a platform reached its daily limit | "until-hired: 1 other update" |

## How to send
1. `python3 <workspace>/bin/tracker.py new-input --agent notify` → a path.
2. Write to it with your file tool: `{"kind": "interview", "count": 1, "priority": "high", "title": "Interview: Acme", "message": "Tue 10:00, prep sheet ready"}`.
3. `python3 <workspace>/bin/notify.py send --json <path>`.

What leaves the computer depends on `config.notifications.detail`:
- `counts` [default]: only "until-hired: <count> <kind> update(s)". Nothing about companies shows on a lock screen.
- `names`: the title and message too, after `notify.py` removes email addresses, phone numbers and other long digit runs.
Never put pay, codes, ANSWERS.md values, email bodies or contacts' full names in a notification, whatever the mode.
Quiet hours (`config.notifications.quiet_hours`, in `config.candidate.timezone`) hold pushes except urgent ones. Kinds not in `config.notifications.notify_on` are recorded but not pushed (`blocked` always is).

## Modes (`config.notifications.mode`)
### native
`notify.py send` records the notification and prints `{"send_with_native_tool": {...}}`: send exactly that text with the product's own notification tool.

### ntfy (free phone push, any agent)
1. The candidate installs the ntfy app (iOS/Android) and subscribes to a **long random topic** (20+ characters, e.g. made by a password manager). Anyone who knows the topic can read the messages: treat it like a password. For more privacy, use a self-hosted ntfy server with an access token, and set the phone to hide notification content on the lock screen.
2. Save the topic only in `<workspace>/config.local.json → notifications.ntfy_topic` (git-ignored, readable only by the candidate). `notify.py` reads it from there and sends it in the request body, so it never appears in a command, a log or this conversation again.
3. Test: `python3 <workspace>/bin/notify.py test`.

### Hooks (agents that support them)
Claude Code and Antigravity can run a command on events such as "waiting for input" or "stopped". Point the hook at `python3 <workspace>/bin/notify.py send --kind blocked --count 1 --priority high`. Never paste the topic or a `curl` command with the topic into a hook file; `setup_workspace.py --check` warns if it finds the topic in one. Hook formats differ by product and version: test with one event before relying on it.

### digest
`notify.py` only writes `NOTIFICATIONS.md`; show it at the start of the next session. Good for agents without any push channel.
