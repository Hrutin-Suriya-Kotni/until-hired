---
name: networking
description: "Optional, off by default. Conversation-first networking on professional networks: find the people who hire for a role the candidate wants, read their recent post, and draft a short note that reacts to it, adds one line of real experience and asks one genuine question. Drafts only; the candidate sends them. No cold email, no lead lists, no bulk messaging. Use only when config.networking.enabled is true and the candidate asks for networking, referrals or 'who should I talk to at <company>'."
license: MIT
metadata:
  author: Hrutin Suriya Kotni
---
# Networking (optional, drafts only)

People answer curiosity about their own work. They ignore "can you refer me?" and "open to roles?". This skill writes a few good notes a day for the candidate to send by hand. It never sends anything and never builds lead lists.

## When to use
- `config.networking.enabled` is true, and
- the candidate names a company or role they care about, or a company where they applied and heard nothing for 10+ days.
At most `config.networking.notes_per_day` drafts a day (default 5).

## 1. Choose the person
- The hiring manager for the role, the head of the team, or a senior engineer on it. A recruiter only if no one else is visible. At most 2 people per company, one at a time.
- `tracker.py contact-add --json <path>` first (`{"name", "company", "title", "channel", "url", "hook"}`): exit 3 means already contacted; stop. Never the same person twice in 30 days.
- Skip companies where the candidate is in an active interview process (they already have a channel).
- Finding people: the candidate can look themselves (on LinkedIn: the company page → People → search "hiring", "engineering", the team name), or paste profile links. Don't automate searches or profile visits on networks whose terms forbid it.

## 2. Find a real hook
- Their most recent substantive post (last 30 days), a talk, an interview, a blog post or a release they led. Open it and save the URL, the date and a one-line summary in your own words.
- Nothing real → skip the person. Never invent or stretch what they said.

## 3. Draft the note (connection notes are often limited to about 200 characters)
Three parts, nothing else:
1. **Their point**, specific, in your words.
2. **One line of the candidate's experience** from `FACTS.md` that relates to it.
3. **One genuine question** about their work.
No "would love to connect", no "open to roles?", no praise words, no links. Check the length.

**After they accept** (only if they do): up to ~900 characters: thanks; respond to their answer if any; 2–3 related facts from `FACTS.md`; the specific open role and link if there is one; ask for 15 minutes or a pointer to the hiring manager.

## 4. Hand to the candidate
Show each draft with the hook link. They edit and send it themselves. Then:
`tracker.py contact-update --id N --status sent --next-on <date + 7 days>`; on accept/reply update the status (`accepted`, `replied`, `call`, `referral`, `no-reply`). One follow-up at most.

## 5. Measure
In the weekly review: notes sent, accepted, replied, calls, referrals. If fewer than 1 in 10 replies after 20 notes, change the hooks or stop; the candidate decides.

## Never
- No cold email, no scraped email addresses, no lead lists, no bulk or automated sending.
- No message that repeats across people.
- Nothing about a person that isn't public and relevant to their work.
