"""The Claude Code guard hook (.claude-plugin/hooks/guard.py)."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import GUARD


def decide(payload):
    p = subprocess.run([sys.executable, str(GUARD)], input=json.dumps(payload) if not isinstance(payload, str) else payload,
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout)["hookSpecificOutput"]["permissionDecision"] if p.stdout.strip() else "allow"


def bash(cmd):
    return decide({"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": "/tmp"})


class BashCommands(unittest.TestCase):
    def test_decisions(self):
        cases = {
            'python3 career/bin/tracker.py add --company "Acme" --role "ML"': "deny",
            'python3 career/bin/tracker.py add --json /w/.inbox/scout-1.json --score 80 --status shortlisted': "allow",
            'python3 career/bin/tracker.py update --id 3 --status applied --json /w/.inbox/a.json 2>&1': "allow",
            'python3 "/Users/x/Job Search/career/bin/tracker.py" due --format json': "allow",
            'python3 career/bin/tracker.py interview-add --job-id 2 --when "2026-11-20 10:00" --json /w/.inbox/i.json': "allow",
            'cd career && python3 bin/tracker.py due': "deny",
            'echo "{}" | python3 bin/tracker.py add --json -': "deny",
            'python3 bin/tracker.py add --json "$(mktemp)"': "deny",
            'python3 bin/tracker.py add --json `x`': "deny",
            "python3 bin/tracker.py add --json f <<EOF\n{}\nEOF": "deny",
            'python3 bin/tracker.py check --company=Acme': "deny",
            'python3 bin/knowledge.py claimable --skills "python, rust"': "deny",
            'python3 bin/knowledge.py lessons --approve 1,2': "ask",
            'python3 bin/knowledge.py lessons': "allow",
            'python3 bin/notify.py send --title "hi"': "deny",
            'python3 bin/notify.py send --kind interview --count 1 --json /w/.inbox/n.json': "allow",
            'python3 skills/agent-setup/scripts/setup_workspace.py --dir career --check': "allow",
            'python3 bin/tracker.py list --status applied > out.txt': "deny",
            'grep -n "--company" skills/agent-setup/scripts/tracker.py | head': "allow",
            'cat career/bin/tracker.py': "allow",
            'git commit -m "update tracker.py --company handling"': "allow",
            'ls -la': "allow",
            'bash -c "python3 bin/tracker.py add --company x"': "deny",
            '/usr/bin/python3 career/bin/tracker.py add --notes hi': "deny",
            'UNTIL_HIRED_LOCK_TIMEOUT=5 python3 bin/tracker.py due': "allow",
            'python3 -I career/bin/knowledge.py gaps --write': "allow",
            'python3 -m unittest tests/test_tracker.py': "allow",
            'sed -n 1,20p skills/agent-setup/scripts/tracker.py': "allow",
        }
        for cmd, want in cases.items():
            with self.subTest(cmd=cmd):
                self.assertEqual(bash(cmd), want)

    def test_bad_input_fails_open(self):
        self.assertEqual(decide("not json"), "allow")
        self.assertEqual(decide({"tool_name": "Bash"}), "allow")


class Edits(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="uh-hook-"))
        self.ws = self.tmp / "career"
        (self.ws / "profile").mkdir(parents=True)
        (self.ws / ".until-hired").write_text("{}", encoding="utf-8")
        self.other = self.tmp / "project"
        self.other.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def edit(self, path, tool="Write"):
        return decide({"tool_name": tool, "tool_input": {"file_path": str(path)}, "cwd": str(self.tmp)})

    def test_protected_files_ask(self):
        for rel in ["config.json", "config.local.json", "profile/ANSWERS.md", "profile/FACTS.md", "profile/DO_NOT_CLAIM.md",
                    "knowledge/LEARNINGS.md", "bin/tracker.py", ".gitignore", "tracker/jobs.csv", "knowledge/graph.json"]:
            with self.subTest(rel=rel):
                self.assertEqual(self.edit(self.ws / rel), "ask")
        self.assertEqual(self.edit(self.ws / "profile" / "FACTS.md", tool="Edit"), "ask")

    def test_normal_files_and_other_projects_are_untouched(self):
        for p in [self.ws / ".inbox" / "scout-1.json", self.ws / "materials" / "1-acme" / "resume.md",
                  self.ws / "SESSION_LOG.md", self.other / "config.json", self.other / "bin" / "tool.py"]:
            with self.subTest(p=str(p)):
                self.assertEqual(self.edit(p), "allow")
        self.assertEqual(decide({"tool_name": "Write", "tool_input": {"file_path": "career/config.json"},
                                 "cwd": str(self.tmp)}), "ask")                              # relative paths too


if __name__ == "__main__":
    unittest.main()
