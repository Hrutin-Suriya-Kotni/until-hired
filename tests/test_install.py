"""install.py: copies skills and agents, never replaces folders it did not install."""
import shutil
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT, run


class Install(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="uh-inst-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_layouts(self):
        for agent, skills, agents in [("antigravity", ".agents/skills", ".agents/agents"),
                                      ("claude-code", ".claude/skills", ".claude/agents"),
                                      ("codex", ".agents/skills", None), ("generic", "skills", "agents")]:
            with self.subTest(agent=agent):
                t = self.tmp / agent
                run(ROOT / "install.py", "--agent", agent, "--target", t)
                self.assertTrue((t / skills / "until-hired" / "SKILL.md").exists())
                self.assertTrue((t / skills / "agent-setup" / "scripts" / "uhlib.py").exists())
                if agents:
                    self.assertTrue((t / agents / "scout.md").exists())
                run(ROOT / "install.py", "--agent", agent, "--target", t)                # re-install is fine

    def test_foreign_folder_is_kept(self):
        t = self.tmp / "proj"
        mine = t / ".agents" / "skills" / "job-tracker"
        mine.mkdir(parents=True)
        (mine / "SKILL.md").write_text("my own skill", encoding="utf-8")
        run(ROOT / "install.py", "--agent", "antigravity", "--target", t, expect=1)
        self.assertEqual((mine / "SKILL.md").read_text(encoding="utf-8"), "my own skill")
        run(ROOT / "install.py", "--agent", "antigravity", "--target", t, "--force")
        self.assertNotEqual((mine / "SKILL.md").read_text(encoding="utf-8"), "my own skill")

    def test_home_is_refused(self):
        run(ROOT / "install.py", "--agent", "generic", "--target", Path.home(), expect=1)


if __name__ == "__main__":
    unittest.main()
