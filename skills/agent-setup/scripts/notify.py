#!/usr/bin/env python3
"""until-hired notify: tell the candidate something needs them, without leaking their search.

  path=$(python3 bin/tracker.py new-input --agent notify)
  (write {"kind": "interview", "count": 1, "title": "...", "message": "..."} to that file)
  python3 bin/notify.py send --json <path>
  python3 bin/notify.py test

Settings come from <workspace>/config.json -> notifications:
  mode         none | digest | native | ntfy   (the candidate's choice)
  detail       counts (default: "until-hired: 1 interview update") | names (title and message are sent)
  quiet_hours  ["22:30", "07:30"]: anything but urgent waits for the digest
  ntfy_server  https server, default https://ntfy.sh
The ntfy topic is a secret: it lives only in <workspace>/config.local.json -> notifications.ntfy_topic.
It never appears on a command line; this tool reads it and sends it in the request body.

Every notification is written in full to <workspace>/NOTIFICATIONS.md (on this computer only).
Before anything leaves the machine: control characters are removed, text is shortened, and email
addresses and long digit runs (phone numbers, codes, account numbers) become [removed].

This is the only until-hired tool that uses the network, and only to POST to the configured
https ntfy server. Python 3.9+, standard library only.
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from uhlib import EXIT_INPUT, Cli, Lock, __version__, append_line, fail, load_json_file, md, sanitize  # noqa: E402

PRIORITIES = {"low": 2, "default": 3, "high": 4, "urgent": 5}
MODES = {"none", "native", "ntfy", "digest"}
KINDS = ["interview", "assessment", "offer", "deadline", "blocked", "session", "digest", "other"]
TOPIC = re.compile(r"[A-Za-z0-9_-]{8,64}")


def workspace() -> Path:
    env = os.environ.get("UNTIL_HIRED_HOME")
    if env:
        return Path(env)
    here = Path(__file__).resolve().parent
    return here.parent if here.name == "bin" else Path.cwd() / "career"


def _number(m):
    s = m.group(0)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}(?: \d{1,2}:\d{2})?|\d{1,2}:\d{2}", s.strip()):
        return s                                                          # a date or a time
    return "[removed]" if sum(c.isdigit() for c in s) >= 7 else s


def scrub(value, limit: int) -> str:
    t = sanitize(value or "")
    t = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[removed]", t)          # email addresses
    t = re.sub(r"\+?\d[\d\s().,:-]{5,}\d", _number, t)                  # phone and account numbers (not dates)
    t = re.sub(r"(?<!\d)\d{6,}(?!\d)", "[removed]", t)                    # one-time codes and other long numbers
    return t[:limit]


def in_quiet_hours(qh, now=None):
    try:
        start, end = [dt.datetime.strptime(x, "%H:%M").time() for x in qh]
    except (TypeError, ValueError):
        return False
    t = (now or dt.datetime.now()).time()
    return (start <= t or t < end) if start > end else (start <= t < end)


def local_now(config):
    """Now in the candidate's time zone (config.candidate.timezone), else the computer's."""
    tz = ((config.get("candidate") or {}).get("timezone") or "").strip()
    if tz:
        try:
            from zoneinfo import ZoneInfo
            return dt.datetime.now(ZoneInfo(tz)).replace(tzinfo=None)
        except Exception:                                     # unknown zone or no tz database (some Windows)
            pass
    return dt.datetime.now()


def record(ws: Path, title, message, priority, outcome):
    p = ws / "NOTIFICATIONS.md"
    if not p.exists():
        append_line(p, "# Notifications\n\n> Newest last. Written by notify.py. Stays on this computer.\n")
    append_line(p, f"- {dt.datetime.now():%Y-%m-%d %H:%M} [{priority}] **{md(title)}**: {md(message)} ({outcome})")


def post_ntfy(server, topic, title, message, priority):
    u = urllib.parse.urlparse(server)
    if u.scheme != "https" or not u.netloc:
        fail(f"notifications.ntfy_server must be an https:// URL, got {server!r}")
    body = json.dumps({"topic": topic, "title": title, "message": message,
                       "priority": PRIORITIES[priority]}).encode("utf-8")
    req = urllib.request.Request(server.rstrip("/") + "/", data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:      # noqa: S310 (https enforced above)
        return r.status


def cmd_send(a, test=False):
    ws = a.dir
    cfg = load_json_file(ws / "config.json", {}).get("notifications", {}) or {}
    local = load_json_file(ws / "config.local.json", {}).get("notifications", {}) or {}
    if test:
        kind, count, priority = "other", 1, "default"
        title, message = "until-hired test", "Notifications work."
    else:
        kind, priority = a.kind or "other", (a.priority or "default").lower()
        if priority not in PRIORITIES:
            fail(f"priority must be one of {', '.join(PRIORITIES)}", EXIT_INPUT)
        try:
            count = int(a.count or 1)
        except ValueError:
            fail("count must be a whole number", EXIT_INPUT)
        title = scrub(a.title or "until-hired", 80)
        message = scrub(a.message or f"{count} {kind} update{'s' if count != 1 else ''}", 400)
    mode = cfg.get("mode", "none")
    notify_on = cfg.get("notify_on")
    if mode in ("native", "ntfy") and not test and isinstance(notify_on, list) and kind not in notify_on and kind != "blocked":
        mode = "digest"                                           # the candidate didn't ask to be pinged for this kind
    if mode not in MODES:
        fail(f"notifications.mode must be one of {', '.join(sorted(MODES))}", EXIT_INPUT)
    detail = cfg.get("detail", "counts")
    if detail == "names" or test:
        push_title, push_message = title, message
    else:
        push_title, push_message = "until-hired", f"{count} {kind} update{'s' if count != 1 else ''}. Open your agent for details."
    with Lock(ws, what="notification log"):
        if mode == "none":
            record(ws, title, message, priority, "not sent: notifications off")
            print("recorded (notifications off)")
            return
        if mode in ("native", "ntfy") and priority != "urgent" and not test and \
                in_quiet_hours(cfg.get("quiet_hours"), local_now(load_json_file(ws / "config.json", {}))):
            record(ws, title, message, priority, "held: quiet hours")
            print("recorded (quiet hours)")
            return
        if mode == "digest":
            record(ws, title, message, priority, "digest")
            print("recorded for the digest")
            return
        if mode == "native":
            record(ws, title, message, priority, "native")
            print(json.dumps({"send_with_native_tool": {"title": push_title, "message": push_message}}, ensure_ascii=False))
            return
        topic = local.get("ntfy_topic", "")
        if not topic or not TOPIC.fullmatch(topic):
            fail("ntfy mode needs notifications.ntfy_topic in config.local.json (8-64 letters, digits, - or _; "
                 "use 20+ random characters). Re-run setup_workspace.py to move it there from config.json.")
        try:
            status = post_ntfy(cfg.get("ntfy_server", "https://ntfy.sh"), topic, push_title, push_message, priority)
            record(ws, title, message, priority, f"sent ({status})")
            print("sent")
        except Exception as e:                                   # network errors must not stop a session
            record(ws, title, message, priority, f"push failed: {type(e).__name__}")
            print(f"push failed ({type(e).__name__}); recorded in NOTIFICATIONS.md", file=sys.stderr)


def build():
    c = Cli("notify.py", __doc__, workspace(), "notify")
    x = c.cmd("send", lambda a: cmd_send(a), "send (or record) one notification")
    x.add_argument("--kind", choices=KINDS); x.add_argument("--count")
    x.add_argument("--priority", help="low | default | high | urgent")
    x.add_argument("--title"); x.add_argument("--message")
    c.cmd("test", lambda a: cmd_send(a, test=True), "send a test notification")
    return c


def main(argv=None):
    build().run(argv)


if __name__ == "__main__":
    main()
