"""Packaging, documentation lint and a personal-data scan of the whole repository."""
import json
import re
import sys
import unittest
from pathlib import Path

from helpers import GUARD, ROOT, SCRIPTS

sys.path.insert(0, str(GUARD.parent))
import guard  # noqa: E402
import uhlib  # noqa: E402

MANIFESTS = ["plugin.json", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json"]
TOOL_NAMES = re.compile(r"(?<![\w-])(?:tracker|knowledge|notify)\.py\b")


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert m, f"no frontmatter in {path}"
    fm = {}
    for line in m.group(1).splitlines():
        if re.match(r"^[a-z_]+:", line):
            k, v = line.split(":", 1)
            fm[k] = v.strip().strip('"')
    return fm, text


def docs():
    for base in ("skills", "agents"):
        yield from (ROOT / base).rglob("*.md")
    for name in ("README.md", "GUIDE.md", "SAFETY.md", "PREREQUISITES.md", "CONTRIBUTING.md"):
        yield ROOT / name


class Manifests(unittest.TestCase):
    def test_one_version_everywhere(self):
        v = load("plugin.json")["version"]
        for rel in MANIFESTS:
            self.assertEqual(load(rel)["version"], v, rel)
        self.assertEqual(uhlib.__version__, v)
        top = re.search(r"^## (\S+)", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), re.M).group(1)
        self.assertEqual(top, v)
        for skill in (ROOT / "skills").glob("*/SKILL.md"):
            self.assertNotIn("version:", skill.read_text(encoding="utf-8").split("---")[1], skill)

    def test_shared_fields_match(self):
        root = load("plugin.json")
        for rel in MANIFESTS:
            m = load(rel)
            for k in ("name", "description", "license", "repository"):
                self.assertEqual(m[k], root[k], f"{rel}: {k}")
        mk = load(".claude-plugin/marketplace.json")
        self.assertEqual(mk["plugins"][0]["source"], "./")
        self.assertEqual(mk["plugins"][0]["name"], root["name"])
        ag = load(".agents/plugins/marketplace.json")
        self.assertEqual(ag["plugins"][0]["source"], "./")

    def test_referenced_paths_exist(self):
        cc = load(".claude-plugin/plugin.json")
        self.assertTrue((ROOT / cc["icon"]).exists())
        hooks = ROOT / cc["hooks"]
        self.assertTrue(hooks.exists())
        cmd = json.loads(hooks.read_text(encoding="utf-8"))["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        self.assertIn("${CLAUDE_PLUGIN_ROOT}/.claude-plugin/hooks/guard.py", cmd)
        self.assertTrue((ROOT / load(".codex-plugin/plugin.json")["skills"]).is_dir())
        self.assertTrue((ROOT / load("plugin.json")["logo"]).exists())


class Shipped(unittest.TestCase):
    def test_no_package_file_is_git_ignored(self):
        import shutil
        import subprocess
        if not shutil.which("git") or not (ROOT / ".git").exists():
            self.skipTest("not a git checkout")
        files = [str(p.relative_to(ROOT)) for base in ("skills", "agents", ".claude-plugin", "tests")
                 for p in (ROOT / base).rglob("*") if p.is_file() and "__pycache__" not in p.parts]
        r = subprocess.run(["git", "-C", str(ROOT), "check-ignore", "--no-index", *files], capture_output=True, text=True)
        self.assertEqual(r.stdout.split(), [], "these files would not be committed")


class Skills(unittest.TestCase):
    def test_frontmatter(self):
        dirs = [d for d in (ROOT / "skills").iterdir() if d.is_dir()]
        self.assertEqual(len(dirs), 13)
        for d in dirs:
            fm, text = frontmatter(d / "SKILL.md")
            self.assertEqual(fm["name"], d.name)
            self.assertTrue(0 < len(fm["description"]) <= 1024, d.name)
            self.assertLess(len(text.splitlines()), 500, d.name)
        for a in (ROOT / "agents").glob("*.md"):
            fm, _ = frontmatter(a)
            self.assertEqual(fm["name"], a.stem)

    def test_links_to_references_resolve(self):
        for md in (ROOT / "skills").rglob("*.md"):
            for target in re.findall(r"\]\(((?:references|\.\./)[^)#]+)\)", md.read_text(encoding="utf-8")):
                self.assertTrue((md.parent / target).exists(), f"{md}: {target}")


class SafeCommandLint(unittest.TestCase):
    """Every tool command shown to an agent follows references/safe-commands.md."""

    def spans(self, text):
        yield from re.findall(r"`([^`\n]+)`", text)
        for block in re.findall(r"```[a-z]*\n(.*?)```", text, re.S):
            yield from block.splitlines()

    def test_no_free_text_options_in_tool_commands(self):
        bad = []
        for path in docs():
            for span in self.spans(path.read_text(encoding="utf-8")):
                if not TOOL_NAMES.search(span):
                    continue
                for flag in re.findall(r"(?<![\w-])--[a-z][a-z0-9-]*", span):
                    if flag not in guard.TYPED:
                        bad.append(f"{path.relative_to(ROOT)}: {flag} in `{span[:90]}`")
                if re.search(r"--json\s+-(\s|$)|\becho\b|\bprintf\b|<<|\$\(|\|\s*python", span):
                    bad.append(f"{path.relative_to(ROOT)}: shell-built input in `{span[:90]}`")
        self.assertEqual(bad, [], "\n".join(bad))

    def test_no_curl_to_ntfy(self):
        for path in docs():
            self.assertNotRegex(path.read_text(encoding="utf-8"), r"curl[^\n]*ntfy", str(path))

    def test_codes_are_never_passed_on(self):
        risky = re.compile(r"\b(give|pass|send|forward|hand|share|enter|type|read)\b[^.\n|]{0,40}\b(it|the code|codes?)\b"
                           r"[^.\n|]{0,40}\b(agent|form|applicant|filling)", re.I)
        for path in docs():
            for line in path.read_text(encoding="utf-8").splitlines():
                if re.search(r"\b(code|OTP)\b", line, re.I) and risky.search(line):
                    self.assertRegex(line, r"\b([Nn]ever|not|no)\b", f"{path}: {line[:120]}")


class PersonalData(unittest.TestCase):
    """No real personal data anywhere in the repository (generic patterns only; nothing personal in this file)."""

    SKIP_DIRS = {".git", "__pycache__"}
    TEXT = {".md", ".py", ".json", ".yml", ".yaml", ".txt", ".csv", ".toml", ""}
    EMAIL_OK = re.compile(r"@(example\.(com|org)|users\.noreply\.github\.com)$|^noreply@anthropic\.com$", re.I)

    def files(self):
        for p in ROOT.rglob("*"):
            if p.is_file() and not (set(p.relative_to(ROOT).parts) & self.SKIP_DIRS) and p.suffix in self.TEXT:
                yield p

    def test_no_phone_numbers_emails_ids(self):
        problems = []
        phone = re.compile(r"(?<![\w.-])(?:\+?\d{1,3}[\s-]?)?(?:[6-9]\d{4}[\s-]?\d{5}|\(?\d{3}\)?[\s-]\d{3}[\s-]\d{4})(?![\w-])")
        email = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
        sheet = re.compile(r"spreadsheets/d/[A-Za-z0-9_-]{25,}|(?<![A-Za-z0-9_-])(?=[A-Za-z0-9_-]{44}(?![A-Za-z0-9_-]))"
                           r"(?=[^\s]*[A-Z])(?=[^\s]*[a-z])(?=[^\s]*\d)[A-Za-z0-9_-]{44}")
        ids = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b|\b\d{4}\s\d{4}\s\d{4}\b")              # PAN, Aadhaar shapes
        for p in self.files():
            text = p.read_text(encoding="utf-8", errors="ignore")
            rel = str(p.relative_to(ROOT))
            for m in phone.finditer(text):
                if "555" not in m.group(0):
                    problems.append(f"{rel}: phone-like {m.group(0)!r}")
            for m in email.finditer(text):
                if not self.EMAIL_OK.search(m.group(0)):
                    problems.append(f"{rel}: email {m.group(0)!r}")
            for m in sheet.finditer(text):
                problems.append(f"{rel}: spreadsheet-id-like {m.group(0)[:12]}...")
            for m in ids.finditer(text):
                problems.append(f"{rel}: id-like {m.group(0)!r}")
        self.assertEqual(problems, [], "\n".join(problems))


if __name__ == "__main__":
    unittest.main()
