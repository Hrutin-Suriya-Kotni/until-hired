"""until-hired shared core: safe input, safe storage and one lock for every tool.

Used by tracker.py, knowledge.py, notify.py and setup_workspace.py. Python 3.9+, standard library only.

What this module guarantees (each one is covered by tests/):
  * Input: every command accepts --json FILE. Keys are the option names with underscores
    ({"company": "...", "next_on": "2026-11-20"}). Values are handed to argparse as --key=value,
    so a value can never become an option. Files in <workspace>/.inbox/ are deleted after a
    successful run (exit 0, 3 or 4). Stdin is not accepted on purpose.
  * Text: NFC, no control / bidi / zero-width characters, one line, length-checked (exit 2).
  * Spreadsheets: reversible cell encoding against formula injection (see cell_encode).
  * Files: written to a temporary file, fsynced, then atomically renamed, with a .bak copy.
    A file that changed on disk while a command ran is never overwritten (exit 5).
  * Concurrency: one operating-system lock per data folder; released by the OS if a process dies.
"""
import argparse
import csv
import datetime as dt
import io
import json
import os
import re
import shutil
import sys
import time
import unicodedata
from pathlib import Path

__version__ = "1.0.0"

EXIT_OK, EXIT_ERROR, EXIT_INPUT, EXIT_DUP, EXIT_ACTIVE, EXIT_BUSY, EXIT_BLOCKED = 0, 1, 2, 3, 4, 5, 6
EXIT_TABLE = (
    "Exit codes: 0 ok · 1 error (message on stderr) · 2 bad input · 3 duplicate / not claimable · "
    "4 company already in an active process · 5 busy or file changed by another program (retry) · "
    "6 blocked by a limit or a host that is not allowed"
)

MAX_INPUT_BYTES = 256 * 1024
SHORT, URL, LONG, STORED_MAX = 300, 2000, 4000, 30000
RESERVED_KEYS = {"dir", "json", "version", "help", "h"}


def fail(msg, code=EXIT_ERROR):
    print(msg, file=sys.stderr)
    sys.exit(code)


def setup_process():
    """Files created by any tool are private to the user (600 / 700)."""
    try:
        os.umask(0o077)
    except (AttributeError, OSError):
        pass


# ---------------------------------------------------------------- text
_STRIP = re.compile(
    "[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f"     # C0 (except tab, LF, CR) and C1 controls, DEL
    "​-‏"                            # zero-width and direction marks
    "‪-‮⁦-⁩"               # bidirectional overrides and isolates
    "⁠-⁤﻿]"                     # word joiners, invisible operators, byte-order mark
)
_NEWLINES = re.compile(r"[ \t]*(?:\r\n|[\r\n  \x85])+[ \t]*")


def sanitize(value) -> str:
    """One clean line of text: NFC, no hidden or control characters, newlines become ' / '."""
    s = unicodedata.normalize("NFC", str(value))
    s = _NEWLINES.sub(" / ", s)
    s = _STRIP.sub("", s.replace("\t", " "))
    return s.strip()


def text(value, field, limit=SHORT):
    """Sanitised text for one input field, or None. Too long is an error, never a silent cut."""
    if value is None:
        return None
    s = sanitize(value)
    if len(s) > limit:
        fail(f"{field}: {len(s)} characters is over the limit of {limit}. Shorten it and retry.", EXIT_INPUT)
    return s


def append_capped(old: str, new: str, field: str, sep=" | ") -> str:
    """Append to an accumulating field (notes, evidence); keep the newest text under STORED_MAX."""
    s = (old + sep if old else "") + new
    if len(s) > STORED_MAX:
        s = "…" + s[-(STORED_MAX - 1):]
        print(f"note: {field} reached {STORED_MAX} characters; the oldest text was dropped "
              f"(the .bak file and events.jsonl keep history)", file=sys.stderr)
    return s


def md(value) -> str:
    """Text safe inside generated Markdown (tables, lists): no links, images, HTML or emphasis."""
    t = sanitize(value)
    for ch in "\\|[]()!<>`*_#~":
        t = t.replace(ch, "\\" + ch)
    return t


def slug(value, limit=40) -> str:
    s = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:limit].strip("-")
    return s or "item"


# ---------------------------------------------------------------- spreadsheet cells
CELL_TRIGGERS = ("=", "+", "-", "@", "\t", "\r", "'")


def cell_encode(s: str) -> str:
    """Neutralise formula injection: a cell that starts with = + - @ tab CR or ' gets one leading '.

    Spreadsheet apps show the ' as a text marker, so nothing runs. cell_decode reverses it exactly,
    so the agent and the tools always see the real value.
    """
    s = "" if s is None else str(s)
    return "'" + s if s.startswith(CELL_TRIGGERS) else s


def cell_decode(s: str) -> str:
    s = "" if s is None else str(s)
    return s[1:] if len(s) > 1 and s[0] == "'" and s[1] in CELL_TRIGGERS else s


# ---------------------------------------------------------------- dates
def check_date(field, v):
    """A date like 2026-11-20, or "" to clear the field."""
    if v in (None, ""):
        return v
    try:
        dt.date.fromisoformat(v)
    except ValueError:
        fail(f"{field}: expected a date like 2026-11-20 (or \"\" to clear), got {v!r}", EXIT_INPUT)
    return v


def check_when(field, v):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", v or ""):
        fail(f"{field}: expected 'YYYY-MM-DD HH:MM', got {v!r}", EXIT_INPUT)
    try:
        dt.datetime.strptime(v, "%Y-%m-%d %H:%M")
    except ValueError:
        fail(f"{field}: not a real date and time: {v!r}", EXIT_INPUT)
    return v


def now():
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M")


def today():
    return dt.date.today()


# ---------------------------------------------------------------- lock
class Lock:
    """Exclusive operating-system lock on <folder>/.lock (fcntl.flock / msvcrt.locking).

    The lock belongs to the open file handle, so the OS releases it when the process exits,
    even after a crash or kill: there is no stale lock to clean up and nothing to take over.
    Never delete the .lock file by hand.
    """

    def __init__(self, folder: Path, timeout=None, what="tracker"):
        if timeout is None:
            timeout = float(os.environ.get("UNTIL_HIRED_LOCK_TIMEOUT", "20"))
        self.path, self.timeout, self.what, self.fh = Path(folder) / ".lock", timeout, what, None

    def _try(self):
        if os.name == "nt":
            import msvcrt
            self.fh.seek(0)
            msvcrt.locking(self.fh.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(self.fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fh = open(self.path, "a+", encoding="utf-8")
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                self._try()
                return self
            except OSError:
                if time.monotonic() > deadline:
                    self.fh.close()
                    fail(f"busy: another until-hired process is writing the {self.what}. "
                         "Wait a few seconds and run the same command again (do not delete .lock).", EXIT_BUSY)
                time.sleep(0.05)

    def __exit__(self, *exc):
        try:
            if os.name == "nt":
                import msvcrt
                self.fh.seek(0)
                msvcrt.locking(self.fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.fh.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        finally:
            self.fh.close()
        return False


# ---------------------------------------------------------------- files
_STAMPS = {}


def stamp(path: Path):
    """Remember a file's state when it was read, so a later write can detect outside changes."""
    try:
        st = path.stat()
        _STAMPS[str(path)] = (st.st_mtime_ns, st.st_size)
    except FileNotFoundError:
        _STAMPS[str(path)] = None


def _changed(path: Path) -> bool:
    key = str(path)
    if key not in _STAMPS:
        return False
    try:
        st = path.stat()
        cur = (st.st_mtime_ns, st.st_size)
    except FileNotFoundError:
        cur = None
    return cur != _STAMPS[key]


def atomic_write(path: Path, data: str):
    """Write text safely: temp file + fsync + rename, keeping the previous version as <name>.bak."""
    path = Path(path)
    if _changed(path):
        fail(f"{path.name} was changed by another program while this command ran; nothing was written. "
             "Close it in your spreadsheet app or editor, then run the same command again.", EXIT_BUSY)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{os.urandom(3).hex()}.tmp")
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    if path.exists():
        try:
            shutil.copyfile(path, path.with_name(path.name + ".bak"))
        except OSError:
            pass
    for _ in range(25):                       # a spreadsheet app on Windows can hold the file open
        try:
            os.replace(tmp, path)
            stamp(path)
            return
        except PermissionError:
            time.sleep(0.2)
    try:
        tmp.unlink()
    except OSError:
        pass
    fail(f"cannot write {path.name}: another program has it open. Close it (for example in your "
         "spreadsheet app) and run the same command again.", EXIT_BUSY)


def read_csv(path: Path, fields):
    """Rows of a tracker CSV. The header must match exactly, or nothing is read or written."""
    stamp(path)
    if not path.exists():
        return []
    try:
        with open(path, encoding="utf-8-sig", newline="") as f:
            raw = f.read()
    except UnicodeDecodeError:
        fail(f"{path.name} is not UTF-8 text (a spreadsheet app may have re-saved it). Save it as "
             "'CSV UTF-8', or run setup_workspace.py to repair it. Nothing was changed.")
    reader = csv.reader(io.StringIO(raw, newline=""))
    header = next(reader, None)
    if header is None:
        return []
    if header != list(fields):
        hint = " It looks separated by ';' (a regional spreadsheet setting)." if len(header) == 1 and ";" in header[0] else ""
        fail(f"{path.name} has unexpected columns, so it was not read and nothing was written.{hint} "
             f"Run setup_workspace.py --dir <workspace> to repair it (a backup is kept), or restore {path.name}.bak.")
    rows = []
    for values in reader:
        if not values:
            continue
        values = (values + [""] * len(fields))[:len(fields)]
        rows.append({k: cell_decode(v) for k, v in zip(fields, values)})
    return rows


def csv_text(fields, rows) -> str:
    buf = io.StringIO(newline="")
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow(fields)
    for r in rows:
        w.writerow([cell_encode(r.get(k, "") or "") for k in fields])
    return buf.getvalue()


def write_csv(path: Path, fields, rows):
    atomic_write(path, csv_text(fields, rows))


def load_json_file(path: Path, default, label=None):
    """A JSON object from disk. A damaged file stops the tool; it is never silently reset."""
    if not path.exists():
        return default
    stamp(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            raise ValueError("not a JSON object")
        return data
    except (ValueError, UnicodeDecodeError) as e:
        bak = path.with_name(path.name + ".bak")
        extra = f" The previous good copy is {bak.name}; copy it over {path.name} to restore." if bak.exists() else ""
        fail(f"{label or path.name} could not be read ({e}). Nothing was changed.{extra}")


def append_line(path: Path, line: str):
    with open(path, "a", encoding="utf-8") as f:
        f.write(line.rstrip("\n") + "\n")
        f.flush()
        os.fsync(f.fileno())


# ---------------------------------------------------------------- --json input for every command
JSON_HELP = ("read options from a JSON object in FILE. Keys are the option names with underscores, "
             "e.g. {\"company\": \"Acme\", \"next_on\": \"2026-11-20\"}. Use it for ANY text copied from "
             "a job post, email or web page; get a fresh FILE with `tracker.py new-input --agent <name>`.")


def _take_json(argv):
    """Remove --json FILE (or --json=FILE) from argv; return (argv, FILE or None)."""
    out, src, i = [], None, 0
    while i < len(argv):
        tok = argv[i]
        if tok == "--json" and src is None:
            if i + 1 >= len(argv):
                fail("--json needs a FILE", EXIT_INPUT)
            src = argv[i + 1]
            i += 2
            continue
        if tok.startswith("--json=") and src is None:
            src = tok.split("=", 1)[1]
            i += 1
            continue
        out.append(tok)
        i += 1
    return out, src


def _json_to_argv(data, argv):
    extra = []
    for key, v in data.items():
        if not isinstance(key, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,40}", key) or key in RESERVED_KEYS:
            fail(f"--json: key {key!r} is not allowed", EXIT_INPUT)
        opt = "--" + key.replace("_", "-")
        if any(t == opt or t.startswith(opt + "=") for t in argv):
            fail(f"{key} is given both as {opt} and in the --json file; give it once", EXIT_INPUT)
        if v is None or v is False:
            continue
        if v is True:
            extra.append(opt)
        elif isinstance(v, (int, float)):
            extra.append(f"{opt}={v}")
        elif isinstance(v, str):
            extra.append(f"{opt}={v}")
        elif isinstance(v, list) and all(isinstance(x, str) for x in v):
            extra.append(f"{opt}={', '.join(x.replace(',', ' ') for x in v)}")
        else:
            fail(f"--json: {key} must be text, a number, true/false or a list of text", EXIT_INPUT)
    return extra


def _read_input(src: str):
    p = Path(src).expanduser()
    try:
        if p.stat().st_size > MAX_INPUT_BYTES:
            fail(f"--json: {src} is larger than {MAX_INPUT_BYTES // 1024} KB", EXIT_INPUT)
        data = json.loads(p.read_text(encoding="utf-8-sig"))
    except OSError as e:
        fail(f"--json: cannot read {src}: {e.strerror or e}", EXIT_INPUT)
    except (ValueError, UnicodeDecodeError) as e:
        fail(f"--json: {src} is not valid UTF-8 JSON: {e}", EXIT_INPUT)
    if not isinstance(data, dict):
        fail("--json: the file must contain one JSON object, like {\"company\": \"Acme\"}", EXIT_INPUT)
    return p, data


def is_inbox_file(p: Path) -> bool:
    return p.parent.name == ".inbox"


class Cli:
    """argparse with --json FILE on every command, --dir before or after the command, no abbreviations."""

    def __init__(self, prog, doc, default_dir, version_name):
        first = doc.strip().split("\n")[0]
        self.ap = argparse.ArgumentParser(prog=prog, description=first, allow_abbrev=False,
                                          epilog=EXIT_TABLE, formatter_class=argparse.RawDescriptionHelpFormatter)
        self.ap.add_argument("--version", action="version", version=f"until-hired {version_name} {__version__}")
        self.ap.add_argument("--dir", type=Path, default=default_dir, help=f"{version_name} folder")
        self.sp = self.ap.add_subparsers(dest="cmd", required=True, metavar="command")

    def cmd(self, name, fn, help=None):
        x = self.sp.add_parser(name, help=help, description=help, allow_abbrev=False, epilog=EXIT_TABLE)
        x.add_argument("--dir", type=Path, default=argparse.SUPPRESS, help=argparse.SUPPRESS)
        x.add_argument("--json", metavar="FILE", help=JSON_HELP)
        x.set_defaults(fn=fn)
        return x

    def run(self, argv=None):
        setup_process()
        argv = list(sys.argv[1:] if argv is None else argv)
        argv, src = _take_json(argv)
        inbox = None
        if src is not None:
            p, data = _read_input(src)
            argv = argv + _json_to_argv(data, argv)
            inbox = p if is_inbox_file(p) else None
        a = self.ap.parse_args(argv)
        a.json = src
        code = 0
        try:
            a.fn(a)
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
            raise
        finally:
            if inbox is not None and code in (EXIT_OK, EXIT_DUP, EXIT_ACTIVE):
                try:
                    inbox.unlink()
                except OSError:
                    pass
