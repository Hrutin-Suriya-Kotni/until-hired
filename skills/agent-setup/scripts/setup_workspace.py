#!/usr/bin/env python3
"""Create, upgrade, repair or check an until-hired workspace (the folder that holds one candidate's search).

  python3 setup_workspace.py --dir ./career            create / upgrade / repair (safe to re-run)
  python3 setup_workspace.py --dir ./career --check    read-only health report (exit 1 if anything FAILs)
  python3 setup_workspace.py --dir ./career --check --invariants   also audit the data after a session

Setup never overwrites the candidate's files. It copies missing template files, refreshes the tools
in <dir>/bin, moves secrets from config.json into config.local.json (keeping config.json.bak), adds new
config keys, repairs CSV headers (keeping .bak copies), tightens permissions on folders it owns, and
ends with --check. Python 3.9+, standard library only, no network access.
"""
import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tracker as T  # noqa: E402
from uhlib import __version__, atomic_write, setup_process  # noqa: E402

TEMPLATE = HERE.parent / "assets" / "workspace"
TOOLS = ["uhlib.py", "tracker.py", "knowledge.py", "notify.py", "check_system.py"]
FOLDERS = ["bin", "profile", "materials", "materials/_base", "tracker", "knowledge", "knowledge/reviews",
           "proposals", ".inbox"]
PRIVATE_DIRS = ["profile", ".inbox", "materials", "knowledge/reviews"]
PRIVATE_FILES = ["config.local.json", "profile/ANSWERS.md"]
MARKER = ".until-hired"
SECRET_KEYS = [("notifications", "ntfy_topic"), ("tracker", "mirror_id"), ("inbox", "address")]
MODES = {"discover", "prepare", "submit"}
NOTIFY_MODES = {"none", "digest", "native", "ntfy"}
SYNC_HINTS = ["Library/Mobile Documents", "iCloud Drive", "/Dropbox", "/OneDrive", "/Google Drive", "GoogleDrive",
              "/Box/", "/pCloud"]
SENSITIVE_TRACKED = ["profile/", "materials/", "config.local.json", "tracker/contacts.csv", "knowledge/reviews/", "NOTIFICATIONS.md"]
POSIX = os.name == "posix"


def sha(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def load(p: Path):
    try:
        data = json.loads(p.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def gitignore_lines():
    return [x.strip() for x in (TEMPLATE / "_gitignore").read_text(encoding="utf-8").splitlines()
            if x.strip() and not x.startswith("#")]


# ------------------------------------------------------------------ setup
def is_workspace(root: Path):
    return (root / MARKER).exists() or ((root / "bin" / "tracker.py").exists() and (root / "config.json").exists())


def merge_missing(dst, src):
    """Add keys from the template that the candidate's config does not have yet (never changes values)."""
    added = []
    for k, v in src.items():
        if k.startswith("_"):
            continue
        if k not in dst:
            dst[k] = v
            added.append(k)
        elif isinstance(v, dict) and isinstance(dst[k], dict):
            added += [f"{k}.{x}" for x in merge_missing(dst[k], v)]
    return added


def migrate_config(root: Path, log):
    cfg_p, loc_p = root / "config.json", root / "config.local.json"
    cfg, loc = load(cfg_p), load(loc_p)
    if cfg is None:
        log.append("config.json could not be read: left as is (fix it, then re-run setup)")
        return
    if loc is None:
        loc = json.loads((TEMPLATE / "config.local.json").read_text(encoding="utf-8"))
    moved = []
    for section, key in SECRET_KEYS:
        sec = cfg.get(section)
        if isinstance(sec, dict) and key in sec:
            val = sec.pop(key)
            if val:
                loc.setdefault(section, {})[key] = val
                moved.append(f"{section}.{key}")
    added = merge_missing(cfg, json.loads((TEMPLATE / "config.json").read_text(encoding="utf-8")))
    if moved or added:
        atomic_write(cfg_p, json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")     # keeps config.json.bak
        if moved:
            log.append(f"moved secrets to config.local.json: {', '.join(moved)} (old config kept as config.json.bak)")
            bak = root / "config.json.bak"
            if bak.exists() and POSIX:
                os.chmod(bak, 0o600)
        if added:
            log.append(f"added new config keys: {', '.join(added)}")
    if moved or not loc_p.exists():
        atomic_write(loc_p, json.dumps(loc, indent=2, ensure_ascii=False) + "\n")


def repair_csvs(root: Path, log):
    d = root / "tracker"
    for name, fields in T.CSV_FILES.items():
        p = d / name
        if not p.exists():
            continue
        try:
            raw = p.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            raw = p.read_text(encoding="cp1252")
            log.append(f"{name}: converted from a non-UTF-8 encoding")
        first = raw.splitlines()[0] if raw else ""
        delim = ";" if first.count(";") > first.count(",") else ","
        rows = list(csv.reader(io.StringIO(raw, newline=""), delimiter=delim))
        if not rows:
            continue
        header = [h.strip().lstrip("﻿") for h in rows[0]]
        if header == fields and delim == "," and not raw.startswith("﻿"):
            continue
        unknown = [h for h in header if h and h not in fields]
        if unknown:
            log.append(f"FAIL {name}: unknown columns {unknown}; not changed. Restore {name}.bak or fix the header.")
            continue
        out = []
        for values in rows[1:]:
            if not any(v.strip() for v in values):
                continue
            rec = dict(zip(header, values))
            out.append({k: rec.get(k, "") for k in fields})
        shutil.copyfile(p, p.with_name(name + ".pre-repair.bak"))
        atomic_write(p, T_csv(fields, out))
        log.append(f"{name}: header repaired ({'; separator, ' if delim == ';' else ''}{len(out)} rows kept; "
                   f"original in {name}.pre-repair.bak)")


def T_csv(fields, rows):
    from uhlib import cell_decode, csv_text
    return csv_text(fields, [{k: cell_decode(v) for k, v in r.items()} for r in rows])


def setup(root: Path, adopt: bool):
    log = []
    created_root = not root.exists()
    if root.exists() and any(root.iterdir()) and not is_workspace(root) and not adopt:
        sys.exit(f"{root} already has files and is not an until-hired workspace. Choose a new or empty folder "
                 "(or pass --adopt if you really want to use this one).")
    for bad in (Path.home().resolve(), Path(root.anchor)):
        if root == bad:
            sys.exit(f"refusing to use {root} as a workspace: choose a dedicated folder such as ~/career")
    root.mkdir(parents=True, exist_ok=True)
    first_time = not (root / MARKER).exists()
    for f in FOLDERS:
        (root / f).mkdir(parents=True, exist_ok=True)
    for src in sorted(TEMPLATE.rglob("*")):
        if src.is_dir():
            continue
        rel = str(src.relative_to(TEMPLATE)).replace("_gitignore", ".gitignore")
        dst = root / rel
        if dst.exists():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if rel == "config.local.json":
            fd = os.open(str(dst), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(src.read_text(encoding="utf-8"))
        else:
            shutil.copyfile(src, dst)
        log.append(f"created {rel}")
    gi = root / ".gitignore"
    have = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
    missing = [x for x in gitignore_lines() if x not in [h.strip() for h in have]]
    if missing:
        with open(gi, "a", encoding="utf-8") as f:
            f.write(("\n" if have and have[-1] else "") + "\n".join(missing) + "\n")
        log.append(f".gitignore: added {', '.join(missing)}")
    for t in TOOLS:
        dst = root / "bin" / t
        if sha(dst) != sha(HERE / t):
            shutil.copyfile(HERE / t, dst)
            log.append(f"bin/{t} updated")
    (root / "bin" / "VERSION").write_text(__version__ + "\n", encoding="utf-8")
    migrate_config(root, log)
    repair_csvs(root, log)
    if POSIX:
        if created_root or first_time or (root / MARKER).exists():
            os.chmod(root, 0o700)
        for d in PRIVATE_DIRS:
            os.chmod(root / d, 0o700)
        for f in PRIVATE_FILES:
            if (root / f).exists():
                os.chmod(root / f, 0o600)
    (root / MARKER).write_text(json.dumps({"until_hired": __version__, "updated": str(dt.date.today())}) + "\n",
                               encoding="utf-8")
    py = sys.executable or "python3"
    for tool, folder in (("tracker.py", "tracker"), ("knowledge.py", "knowledge")):
        r = subprocess.run([py, str(root / "bin" / tool), "--dir", str(root / folder), "init"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            log.append(f"FAIL {tool} init: {r.stderr.strip()}")
    print(f"workspace ready: {root} (until-hired {__version__})")
    for line in log:
        print(f"  - {line}")
    return 1 if any(x.startswith("FAIL") for x in log) else 0


# ------------------------------------------------------------------ check
class Report:
    def __init__(self):
        self.items = []

    def add(self, level, name, detail):
        self.items.append({"level": level, "check": name, "detail": detail})

    def ok(self, n, d=""):
        self.add("PASS", n, d)

    def warn(self, n, d):
        self.add("WARN", n, d)

    def fail(self, n, d):
        self.add("FAIL", n, d)


def mode_of(p: Path):
    return stat.S_IMODE(p.stat().st_mode)


def git_root(root: Path):
    for p in [root] + list(root.parents):
        if (p / ".git").exists():
            return p
    return None


def check(root: Path, invariants: bool):
    r = Report()
    if not root.exists() or not is_workspace(root):
        r.fail("workspace", f"{root} is not an until-hired workspace. Run setup_workspace.py --dir {root}")
        return r
    # structure
    missing = [f for f in FOLDERS if not (root / f).is_dir()]
    missing += [str(p.relative_to(TEMPLATE)).replace("_gitignore", ".gitignore") for p in TEMPLATE.rglob("*")
                if p.is_file() and not (root / str(p.relative_to(TEMPLATE)).replace("_gitignore", ".gitignore")).exists()]
    r.fail("structure", f"missing: {', '.join(missing)} (re-run setup)") if missing else r.ok("structure")
    # tools
    stale = [t for t in TOOLS if sha(root / "bin" / t) != sha(HERE / t)]
    r.warn("tools", f"outdated or changed in bin/: {', '.join(stale)}. Re-run setup to refresh them.") if stale \
        else r.ok("tools", f"match until-hired {__version__}")
    # config
    cfg = load(root / "config.json")
    tmpl = json.loads((TEMPLATE / "config.json").read_text(encoding="utf-8"))
    if cfg is None:
        r.fail("config", "config.json is missing or not valid JSON")
        cfg = {}
    else:
        absent = [k for k in tmpl if k not in cfg]
        wrong = [k for k in tmpl if k in cfg and tmpl[k] is not None and cfg[k] is not None
                 and type(tmpl[k]) is not type(cfg[k]) and not (isinstance(tmpl[k], (int, float)) and isinstance(cfg[k], (int, float)))]
        if absent or wrong:
            r.warn("config", f"missing keys {absent} / wrong types {wrong} (re-run setup adds missing keys)")
        else:
            r.ok("config")
        leaked = [f"{s}.{k}" for s, k in SECRET_KEYS if isinstance(cfg.get(s), dict) and cfg[s].get(k)]
        r.fail("secrets", f"secret values in config.json: {leaked}. Re-run setup to move them to config.local.json.") \
            if leaked else r.ok("secrets", "none in config.json")
        submit = cfg.get("submit", {}) or {}
        plats = cfg.get("platforms", []) or []
        bad_modes = [p.get("name") for p in plats if isinstance(p, dict) and p.get("mode") not in MODES]
        if submit.get("default_mode", "prepare") not in MODES or bad_modes:
            r.fail("modes", f"unknown modes (allowed: discover, prepare, submit): default={submit.get('default_mode')} platforms={bad_modes}")
        on = [p.get("name") for p in plats if isinstance(p, dict) and p.get("mode") == "submit"]
        if submit.get("default_mode") == "submit":
            on.append("(default)")
        if on and submit.get("confirmed_risks") is not True:
            r.fail("submit", f"submit mode is on for {on} but submit.confirmed_risks is not true. Only the candidate turns it on.")
        elif on:
            r.warn("submit", f"submit mode is ON for {on}: the agent may press Submit on its own. Confirm with the candidate.")
        else:
            r.ok("submit", "no platform in submit mode")
        n = (cfg.get("notifications") or {})
        if n.get("mode", "none") not in NOTIFY_MODES:
            r.fail("notifications", f"notifications.mode must be one of {sorted(NOTIFY_MODES)}")
        loc = load(root / "config.local.json") or {}
        topic = ((loc.get("notifications") or {}).get("ntfy_topic") or "")
        if n.get("mode") == "ntfy":
            if len(topic) < 20:
                r.warn("ntfy topic", "the topic is short or empty; anyone who guesses it can read your notifications. "
                       "Use 20+ random characters (or a self-hosted server with an access token).")
            else:
                hits = []
                for hf in [Path.home() / ".claude" / "settings.json", Path.home() / ".gemini" / "config" / "hooks.json",
                           root.parent / ".claude" / "settings.json", root.parent / ".claude" / "settings.local.json",
                           root.parent / ".agents" / "hooks.json"]:
                    try:
                        if hf.exists() and topic in hf.read_text(encoding="utf-8", errors="ignore"):
                            hits.append(str(hf))
                    except OSError:
                        pass
                r.warn("ntfy topic", f"the topic appears in {hits}; call bin/notify.py from hooks instead") if hits \
                    else r.ok("ntfy topic", "only in config.local.json")
    # permissions
    if POSIX:
        loose = []
        if mode_of(root) & 0o077:
            loose.append(f"{root.name}/ is {oct(mode_of(root))}")
        for d in PRIVATE_DIRS:
            if (root / d).exists() and mode_of(root / d) & 0o077:
                loose.append(f"{d}/ is {oct(mode_of(root / d))}")
        for f in PRIVATE_FILES:
            if (root / f).exists() and mode_of(root / f) & 0o077:
                loose.append(f"{f} is {oct(mode_of(root / f))}")
        r.warn("permissions", "; ".join(loose) + " (re-run setup to make them private)") if loose \
            else r.ok("permissions", "private (700/600)")
    else:
        r.add("SKIP", "permissions", "Windows: keep the workspace inside your own user folder")
    # .gitignore
    gi = root / ".gitignore"
    have = [x.strip() for x in gi.read_text(encoding="utf-8").splitlines()] if gi.exists() else []
    miss = [x for x in gitignore_lines() if x not in have]
    r.warn(".gitignore", f"missing {miss} (re-run setup adds them)") if miss else r.ok(".gitignore")
    # sync folders
    path = str(root.resolve())
    syncy = [h.strip("/") for h in SYNC_HINTS if h in path]
    if sys.platform == "darwin" and any(path.startswith(str(Path.home() / x)) for x in ("Desktop", "Documents")):
        syncy.append("Desktop/Documents (synced if iCloud 'Desktop & Documents' is on)")
    r.warn("sync", f"workspace may sync to the cloud ({', '.join(syncy)}); your private answers would go with it") if syncy \
        else r.ok("sync", "not in a known cloud-sync folder")
    # git
    g = git_root(root)
    if g and shutil.which("git"):
        remotes = subprocess.run(["git", "-C", str(g), "remote"], capture_output=True, text=True).stdout.split()
        tracked = subprocess.run(["git", "-C", str(root), "ls-files", "--", *SENSITIVE_TRACKED],
                                 capture_output=True, text=True).stdout.split()
        if tracked and remotes:
            r.fail("git", f"private files are tracked in a repo with a remote ({', '.join(remotes)}): {tracked[:5]}")
        elif remotes:
            r.warn("git", f"the workspace is inside a git repo with a remote ({', '.join(remotes)}); keep it private")
        else:
            r.ok("git", "local repo, no remote")
    else:
        r.ok("git", "not in a git repo")
    # CSV headers
    bad = []
    for name, fields in T.CSV_FILES.items():
        p = root / "tracker" / name
        if p.exists():
            with open(p, encoding="utf-8-sig", errors="replace", newline="") as fh:
                head = next(csv.reader(fh), [])
            if head != fields:
                bad.append(name)
    r.fail("csv", f"unexpected columns in {bad}: re-run setup to repair (backups kept)") if bad else r.ok("csv")
    # leftovers
    old = [p.name for p in (root / ".inbox").glob("*") if p.is_file() and time.time() - p.stat().st_mtime > 86400] \
        if (root / ".inbox").exists() else []
    r.warn("inbox", f"{len(old)} input file(s) older than a day in .inbox/ (copied page text): delete them") if old \
        else r.ok("inbox")
    tmps = [str(p.relative_to(root)) for p in root.rglob("*.tmp")]
    r.warn("temp files", f"left over: {tmps[:5]}") if tmps else r.ok("temp files")
    lp = root / "knowledge" / "lessons.pending.jsonl"
    n = len([x for x in lp.read_text(encoding="utf-8").splitlines() if x.strip()]) if lp.exists() else 0
    if n:
        r.add("INFO", "lessons", f"{n} lesson(s) wait for the candidate: knowledge.py lessons")
    ans = root / "profile" / "ANSWERS.md"
    if ans.exists() and "## Sensitive" not in ans.read_text(encoding="utf-8", errors="ignore"):
        r.warn("answers", "profile/ANSWERS.md has no '## Sensitive' section; move pay, visa and date of birth under it "
               "so they need your yes per job")
    if invariants:
        audit(root, r)
    return r


def answer_values(root: Path, sensitive_only=True):
    p = root / "profile" / "ANSWERS.md"
    if not p.exists():
        return []
    vals, on = [], not sensitive_only
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("## "):
            on = (not sensitive_only) or line.lower().startswith("## sensitive")
            continue
        m = re.match(r"\s*[-*]\s*[^:]{1,80}:\s*(.+)$", line)
        if on and m:
            v = m.group(1).strip()
            if len(v) >= 6 and not v.startswith("(") and v.lower() not in {"prefer not to say", "not applicable"}:
                vals.append(v)
    return vals


def audit(root: Path, r: Report):
    """Invariants that must hold after any session (used by the live run and the evals)."""
    d = root / "tracker"
    try:
        jobs = T.read_csv(d / "jobs.csv", T.JOB_FIELDS)
        ints = T.read_csv(d / "interviews.csv", T.INTERVIEW_FIELDS)
    except SystemExit:
        r.fail("audit", "tracker files could not be read")
        return
    with_interviews = {i["job_id"] for i in ints}
    no_ev = [j["id"] for j in jobs if j["status"] in (T.IN_PROCESS | {"accepted"})
             and not j["evidence"] and j["id"] not in with_interviews]
    r.fail("evidence", f"jobs marked applied or later without evidence: {no_ev}") if no_ev \
        else r.ok("evidence", "every applied job has evidence")
    seen, dups = {}, []
    for j in jobs:
        k = (T.norm_company(j["company"]), T.norm_role(j["role"]))
        if k in seen:
            dups.append((seen[k], j["id"]))
        seen.setdefault(k, j["id"])
    r.warn("duplicates", f"same company and role: {dups}") if dups else r.ok("duplicates")
    vals = answer_values(root)
    places = []
    scan = [p for p in list(d.glob("*")) + list((root / "knowledge").rglob("*")) +
            [root / "SESSION_LOG.md", root / "NOTIFICATIONS.md"] + list((root / "proposals").rglob("*"))
            if p.is_file() and p.suffix in (".csv", ".json", ".jsonl", ".md", ".txt")]
    for p in scan:
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if any(v in content for v in vals):
            places.append(str(p.relative_to(root)))
    r.fail("privacy", f"a Sensitive answer from ANSWERS.md appears in: {places} (values not shown)") if places \
        else r.ok("privacy", f"no Sensitive answer outside profile/ ({len(vals)} checked)")
    events = []
    for line in (d / "events.jsonl").read_text(encoding="utf-8").splitlines() if (d / "events.jsonl").exists() else []:
        try:
            events.append(json.loads(line))
        except ValueError:
            pass
    blocked = [e for e in events if e.get("type") == "disclosure" and not e.get("allowed")]
    if blocked:
        r.add("INFO", "disclosures", f"{len(blocked)} form(s) on hosts that were not allowed (nothing should have been typed there)")


def print_report(r: Report, fmt):
    if fmt == "json":
        print(json.dumps(r.items, indent=2))
    else:
        for i in r.items:
            print(f"{i['level']:<4} {i['check']}" + (f": {i['detail']}" if i["detail"] else ""))
        c = {k: sum(1 for i in r.items if i["level"] == k) for k in ("PASS", "WARN", "FAIL")}
        print(f"summary: {c['PASS']} pass, {c['WARN']} warn, {c['FAIL']} fail")
    return 1 if any(i["level"] == "FAIL" for i in r.items) else 0


def main(argv=None):
    setup_process()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], allow_abbrev=False)
    ap.add_argument("--version", action="version", version=f"until-hired setup {__version__}")
    ap.add_argument("--dir", type=Path, default=Path.cwd() / "career")
    ap.add_argument("--check", action="store_true", help="read-only health report")
    ap.add_argument("--invariants", action="store_true", help="with --check: audit the data after a session")
    ap.add_argument("--adopt", action="store_true", help="use a non-empty folder that is not a workspace yet")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    a = ap.parse_args(argv)
    root = a.dir.expanduser().resolve()
    if a.check:
        sys.exit(print_report(check(root, a.invariants), a.format))
    code = setup(root, a.adopt)
    print()
    code = max(code, print_report(check(root, False), a.format))
    sys.exit(code)


if __name__ == "__main__":
    main()
