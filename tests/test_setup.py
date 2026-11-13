"""setup_workspace.py: create, upgrade, repair and check."""
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from helpers import SETUP, Workspace, run


def check(ws, *extra, expect=None):
    r = run(SETUP, "--dir", ws, "--check", "--format", "json", *extra, expect=expect)
    return {i["check"]: i for i in json.loads(r.stdout)}, r.returncode


class Fresh(Workspace):
    def test_fresh_workspace_is_healthy(self):
        items, code = check(self.ws)
        self.assertEqual(code, 0, items)
        self.assertFalse([i for i in items.values() if i["level"] in ("WARN", "FAIL")], items)
        for f in ["config.json", "config.local.json", "profile/FACTS.md", "profile/ANSWERS.md", ".gitignore",
                  "bin/tracker.py", "bin/uhlib.py", "bin/notify.py", "bin/VERSION", ".until-hired", "tracker/jobs.csv",
                  "knowledge/graph.json", "knowledge/LEARNINGS.md"]:
            self.assertTrue((self.ws / f).exists(), f)
        gi = (self.ws / ".gitignore").read_text(encoding="utf-8")
        for line in ("profile/", "config.local.json", ".inbox/", "materials/"):
            self.assertIn(line, gi)
        if os.name == "posix":
            self.assertEqual(os.stat(self.ws).st_mode & 0o777, 0o700)
            self.assertEqual(os.stat(self.ws / "config.local.json").st_mode & 0o777, 0o600)
            self.assertEqual(os.stat(self.ws / "profile").st_mode & 0o777, 0o700)

    def test_rerun_never_overwrites_the_candidates_files(self):
        (self.ws / "profile" / "FACTS.md").write_text("mine", encoding="utf-8")
        run(SETUP, "--dir", self.ws)
        self.assertEqual((self.ws / "profile" / "FACTS.md").read_text(encoding="utf-8"), "mine")

    def test_outdated_tool_is_reported_then_refreshed(self):
        (self.ws / "bin" / "tracker.py").write_text("# old\n", encoding="utf-8")
        items, _ = check(self.ws)
        self.assertEqual(items["tools"]["level"], "WARN")
        run(SETUP, "--dir", self.ws)
        self.assertEqual(check(self.ws)[0]["tools"]["level"], "PASS")

    def test_submit_without_confirmation_fails(self):
        cfg = json.loads((self.ws / "config.json").read_text(encoding="utf-8"))
        cfg["platforms"] = [{"name": "greenhouse", "enabled": True, "mode": "submit"}]
        (self.ws / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
        items, code = check(self.ws, expect=1)
        self.assertEqual(items["submit"]["level"], "FAIL")
        cfg["submit"]["confirmed_risks"] = True
        (self.ws / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
        self.assertEqual(check(self.ws)[0]["submit"]["level"], "WARN")

    def test_invariants(self):
        (self.ws / "profile" / "ANSWERS.md").write_text(
            "## Basic\n- Phone: 555-0100\n## Sensitive\n- Current pay: 23 LPA fixed\n", encoding="utf-8")
        run(self.T, "add", "--company", "Acme", "--role", "ML", "--status", "applied")               # no evidence
        run(self.T, "update", "--id", "1", "--note", "told them 23 LPA fixed")                      # leaked answer
        items, code = check(self.ws, "--invariants", expect=1)
        self.assertEqual(items["evidence"]["level"], "FAIL")
        self.assertEqual(items["privacy"]["level"], "FAIL")
        self.assertNotIn("23 LPA", json.dumps(items))                                               # never printed


class Upgrade(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="uh-up-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_0_1_0_workspace_is_migrated(self):
        ws = self.tmp / "career"
        (ws / "bin").mkdir(parents=True)
        (ws / "tracker").mkdir()
        (ws / "bin" / "tracker.py").write_text("# 0.1.0\n", encoding="utf-8")
        (ws / "config.json").write_text(json.dumps({
            "version": 1, "setup_done": True,
            "notifications": {"mode": "ntfy", "ntfy_topic": "uh-old-topic-1234567890abc"},
            "tracker": {"backend": "csv", "mirror": "sheets", "mirror_id": "sheet-id-here"},
            "inbox": {"mode": "connector", "address": "candidate@example.com"}}), encoding="utf-8")
        header = "id;added;company;role"
        (ws / "tracker" / "jobs.csv").write_text(f"{header}\n1;2026-11-01;Acme;ML\n", encoding="utf-8")
        run(SETUP, "--dir", ws)
        cfg = json.loads((ws / "config.json").read_text(encoding="utf-8"))
        loc = json.loads((ws / "config.local.json").read_text(encoding="utf-8"))
        self.assertNotIn("ntfy_topic", cfg["notifications"])
        self.assertNotIn("mirror_id", cfg["tracker"])
        self.assertEqual(loc["notifications"]["ntfy_topic"], "uh-old-topic-1234567890abc")
        self.assertEqual(loc["inbox"]["address"], "candidate@example.com")
        self.assertEqual(cfg["notifications"]["mode"], "ntfy")                                      # values kept
        self.assertIn("apply", cfg)                                                                # new keys added
        self.assertTrue((ws / "config.json.bak").exists())
        out = run(ws / "bin" / "tracker.py", "show", "--id", "1").stdout
        self.assertIn("Acme", out)
        self.assertEqual(check(ws)[0]["secrets"]["level"], "PASS")

    def test_refuses_a_folder_that_is_not_a_workspace(self):
        d = self.tmp / "docs"
        d.mkdir()
        (d / "thesis.txt").write_text("x", encoding="utf-8")
        r = run(SETUP, "--dir", d, expect=1)
        self.assertIn("not an until-hired workspace", r.stderr)
        self.assertEqual(sorted(p.name for p in d.iterdir()), ["thesis.txt"])

    def test_secret_in_config_fails_the_check(self):
        ws = self.tmp / "career"
        run(SETUP, "--dir", ws)
        cfg = json.loads((ws / "config.json").read_text(encoding="utf-8"))
        cfg["notifications"]["ntfy_topic"] = "uh-secret-topic-123456789"
        (ws / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
        items, _ = check(ws, expect=1)
        self.assertEqual(items["secrets"]["level"], "FAIL")


if __name__ == "__main__":
    unittest.main()
