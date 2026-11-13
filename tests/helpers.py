"""Shared helpers for the until-hired tests (standard library only)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "agent-setup" / "scripts"
SETUP = SCRIPTS / "setup_workspace.py"
GUARD = ROOT / ".claude-plugin" / "hooks" / "guard.py"
sys.path.insert(0, str(SCRIPTS))


def run(*args, expect=0, env=None, cwd=None):
    e = dict(os.environ, PYTHONIOENCODING="utf-8", **(env or {}))
    p = subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, encoding="utf-8",
                       env=e, cwd=cwd)
    if expect is not None and p.returncode != expect:
        raise AssertionError(f"exit {p.returncode} (expected {expect}) for {args}\nstdout: {p.stdout}\nstderr: {p.stderr}")
    return p


class Workspace(unittest.TestCase):
    """A fresh workspace for a fictional candidate in a temporary folder."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="uh-test-"))
        self.ws = self.tmp / "career"
        run(SETUP, "--dir", self.ws)
        self.T = self.ws / "bin" / "tracker.py"
        self.K = self.ws / "bin" / "knowledge.py"
        self.N = self.ws / "bin" / "notify.py"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def inp(self, data, agent="test"):
        path = run(self.T, "new-input", "--agent", agent).stdout.strip()
        assert not Path(path).exists()
        Path(path).write_text(json.dumps(data), encoding="utf-8")
        return path

    def t(self, *args, expect=0, **kw):
        return run(self.T, *args, expect=expect, **kw)

    def k(self, *args, expect=0, **kw):
        return run(self.K, *args, expect=expect, **kw)

    def tj(self, data, *args, expect=0):
        return json.loads(self.t(*args, "--json", self.inp(data), expect=expect).stdout)

    def add(self, company, role, expect=0, **extra):
        return self.t("add", "--json", self.inp(dict(company=company, role=role, **extra)), expect=expect)

    def jobs_csv(self):
        return (self.ws / "tracker" / "jobs.csv").read_text(encoding="utf-8")
