"""Security properties of the tools: input handling, spreadsheet safety, paths, locking, files, network."""
import ast
import json
import os
import re
import subprocess
import sys
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from helpers import SCRIPTS, Workspace, run

import uhlib  # noqa: E402  (helpers puts the scripts folder on sys.path)


class Codec(unittest.TestCase):
    def test_cell_round_trip(self):
        for v in ["", "plain", "=1+1", "+44", "-x", "@SUM(A1)", "\tlead", "\rcr", "'", "''", "'=x", "'quoted", "a=b"]:
            enc = uhlib.cell_encode(v)
            self.assertFalse(enc.startswith(("=", "+", "-", "@", "\t", "\r")), (v, enc))
            self.assertEqual(uhlib.cell_decode(enc), v)

    def test_sanitize_removes_hidden_characters(self):
        s = uhlib.sanitize("a‮b​c\x00d\x1b[31me﻿f⁦g\r\nh\ti")
        self.assertEqual(s, "abcd[31mef g / h i".replace("ef g", "efg"))

    def test_markdown_escaping(self):
        self.assertEqual(uhlib.md("[x](http://e) | <img> *b*"), r"\[x\]\(http://e\) \| \<img\> \*b\*")

    def test_slug(self):
        for bad in ["../../.claude/agents", "/etc/passwd", "CON", "․․/x", "..\\..\\x", "   ", "😀"]:
            s = uhlib.slug(bad)
            self.assertRegex(s, r"^[a-z0-9]+(-[a-z0-9]+)*$", bad)


class Input(Workspace):
    def test_inbox_file_is_unique_private_and_deleted_after_use(self):
        a, b = self.inp({"company": "A", "role": "R"}), self.inp({"company": "A", "role": "R"})
        self.assertNotEqual(a, b)
        self.assertEqual(Path(a).parent.resolve(), (self.ws / ".inbox").resolve())
        if os.name == "posix":
            self.assertEqual(os.stat(a).st_mode & 0o777, 0o600)
        self.t("add", "--json", a)
        self.assertFalse(Path(a).exists())
        self.t("add", "--json", b, expect=3)                     # duplicates also consume the file
        self.assertFalse(Path(b).exists())

    def test_failed_input_is_kept_and_outside_files_never_deleted(self):
        bad = self.inp({"company": "A"})                        # role missing
        self.t("add", "--json", bad, expect=2)
        self.assertTrue(Path(bad).exists())
        outside = self.tmp / "mine.json"
        outside.write_text(json.dumps({"company": "B", "role": "R"}), encoding="utf-8")
        self.t("add", "--json", outside)
        self.assertTrue(outside.exists())

    def test_rejected_inputs(self):
        cases = [
            ({"company": "A", "role": "R", "dir": "/tmp"}, 2),          # reserved key
            ({"company": "A", "role": "R", "json": "x"}, 2),
            ({"company": "A", "role": "R", "bogus": 1}, 2),             # unknown option
            ({"company": "A", "role": "R", "notes": {"x": 1}}, 2),      # nested object
            ({"company": "A", "role": "R", "score": "high"}, 2),
            ({"company": "A", "role": "R", "next_on": "tomorrow"}, 2),
            ({"company": "x" * 301, "role": "R"}, 2),                   # too long: rejected, not cut
            ({"Company": "A", "role": "R"}, 2),                         # keys are lower case option names
        ]
        for data, code in cases:
            with self.subTest(data=str(data)[:60]):
                self.t("add", "--json", self.inp(data), expect=code)
        self.t("add", "--json", self.inp({"company": "A", "role": "R"}), "--company", "B", expect=2)  # given twice
        p = self.inp({})
        Path(p).write_text("[1, 2]", encoding="utf-8")
        self.t("add", "--json", p, expect=2)
        Path(p).write_text("x" * (uhlib.MAX_INPUT_BYTES + 1), encoding="utf-8")
        self.t("add", "--json", p, expect=2)
        self.assertNotIn("A,R", self.jobs_csv())

    def test_values_cannot_become_options(self):
        out = json.loads(self.add("--status=offer", "--force").stdout)
        row = json.loads(self.t("show", "--id", out["id"]).stdout)["job"]
        self.assertEqual((row["company"], row["role"], row["status"]), ("--status=offer", "--force", "found"))

    def test_shell_text_is_only_data(self):
        sentinel = self.tmp / "pwned"
        evil = f'"; touch {sentinel}; echo "$(touch {sentinel})`touch {sentinel}`'
        self.add(evil, "ML")
        self.t("add", "--company", evil, "--role", "Other")      # options passed as a list: still data
        self.assertFalse(sentinel.exists())
        self.assertIn("touch", self.t("list").stdout)

    def test_spreadsheet_formulas_are_neutralised_on_disk_and_real_in_output(self):
        self.add('=HYPERLINK("http://x","y")', "@risk", notes="+1 boost")
        csv_text = self.jobs_csv()
        self.assertIn("'=HYPERLINK", csv_text)
        self.assertIn("'@risk", csv_text)
        job = json.loads(self.t("show", "--id", "1").stdout)["job"]
        self.assertEqual(job["company"], '=HYPERLINK("http://x","y")')
        exported = json.loads(self.t("export").stdout)
        self.assertTrue(exported[1][2].startswith("'="))

    def test_hidden_characters_and_newlines_are_cleaned(self):
        self.add("Acme‮", "ML\nEngineer\x00", notes="line1\r\nline2")
        job = json.loads(self.t("show", "--id", "1").stdout)["job"]
        self.assertEqual(job["company"], "Acme")
        self.assertEqual(job["role"], "ML / Engineer")
        self.assertTrue(job["notes"].endswith("line1 / line2"))

    def test_folders_never_leave_materials(self):
        for i, name in enumerate(["../../.claude/agents", "/etc/passwd", "CON", "..\\..\\x", "․․/up"], 1):
            out = json.loads(self.add(name, f"Role {i}").stdout)
            self.assertRegex(out["folder"], r"^materials/\d+-[a-z0-9-]+$")
            self.t("folder", "--id", out["id"], "--create")
        made = [p for p in (self.ws / "materials").iterdir() if p.name != "_base"]
        self.assertEqual(len(made), 5)
        self.assertTrue(all(p.parent == self.ws / "materials" for p in made))

    def test_accumulated_notes_keep_the_newest_text(self):
        self.add("Acme", "ML")
        for i in range(9):
            self.t("update", "--id", "1", "--json", self.inp({"note": f"note {i} " + "x" * 3900}))
        notes = json.loads(self.t("show", "--id", "1").stdout)["job"]["notes"]
        self.assertLessEqual(len(notes), uhlib.STORED_MAX)
        self.assertIn("note 8", notes)
        self.assertNotIn("note 0", notes)

    def test_disclose(self):
        self.add("Acme", "ML")
        ok = self.t("disclose", "--id", "1", "--host", "boards.greenhouse.io", "--fields", "name,email,phone")
        self.assertTrue(json.loads(ok.stdout)["allowed"])
        self.t("disclose", "--id", "1", "--host", "https://docs.google.com/forms/d/x", "--fields", "phone", expect=6)
        self.t("disclose", "--id", "1", "--host", "evil-greenhouse.io", "--fields", "phone", expect=6)
        self.t("disclose", "--id", "1", "--host", "a b", "--fields", "phone", expect=2)
        cfg = json.loads((self.ws / "config.json").read_text(encoding="utf-8"))
        cfg["apply"]["allowed_hosts"] = ["careers.example.com"]
        (self.ws / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
        self.t("disclose", "--id", "1", "--host", "careers.example.com", "--fields", "phone")
        events = (self.ws / "tracker" / "events.jsonl").read_text(encoding="utf-8")
        self.assertIn('"type": "disclosure"', events)
        self.assertNotIn("98", events)


class Files(Workspace):
    def test_excel_style_files(self):
        self.add("Acme", "ML")
        p = self.ws / "tracker" / "jobs.csv"
        p.write_text("﻿" + p.read_text(encoding="utf-8"), encoding="utf-8")       # byte-order mark: fine
        self.add("Beta", "ML")
        semi = p.read_text(encoding="utf-8-sig").replace(",", ";")
        p.write_text(semi, encoding="utf-8")
        r = self.add("Gamma", "ML", expect=1)
        self.assertIn("';'", r.stderr)
        self.assertEqual(p.read_text(encoding="utf-8"), semi)                            # untouched
        run(self.ws.parent.parent / "x" if False else Path(__file__).resolve().parent.parent / "skills" / "agent-setup" /
            "scripts" / "setup_workspace.py", "--dir", self.ws)
        self.add("Gamma", "ML")
        self.assertIn("Beta", self.t("list").stdout)
        self.assertTrue((self.ws / "tracker" / "jobs.csv.pre-repair.bak").exists())

    def test_backup_and_private_modes(self):
        self.add("Acme", "ML")
        self.add("Beta", "ML")
        self.assertTrue((self.ws / "tracker" / "jobs.csv.bak").exists())
        if os.name == "posix":
            self.assertEqual(os.stat(self.ws / "tracker" / "jobs.csv").st_mode & 0o077, 0)

    def test_corrupt_graph_is_never_reset(self):
        g = self.ws / "knowledge" / "graph.json"
        g.write_text("{broken", encoding="utf-8")
        r = self.k("skill", "--level", "claimed", "--json", self.inp({"name": "go"}), expect=1)
        self.assertIn("Nothing was changed", r.stderr)
        self.assertEqual(g.read_text(encoding="utf-8"), "{broken")


class Concurrency(Workspace):
    def test_parallel_writers_lose_nothing(self):
        def worker(w):
            for i in range(25):
                r = run(self.T, "add", "--company", f"Co{w}-{i}", "--role", "R", expect=None,
                        env={"UNTIL_HIRED_LOCK_TIMEOUT": "60"})
                assert r.returncode == 0, r.stderr
        with ThreadPoolExecutor(8) as ex:
            list(ex.map(worker, range(8)))
        rows = self.jobs_csv().strip().splitlines()[1:]
        ids = [r.split(",")[0] for r in rows]
        self.assertEqual(len(rows), 200)
        self.assertEqual(sorted(map(int, ids)), list(range(1, 201)))
        events = (self.ws / "tracker" / "events.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(sum('"job_added"' in e for e in events), 200)

    def test_parallel_knowledge_writers(self):
        def worker(w):
            for i in range(8):
                r = run(self.K, "jd", "--company", f"C{w}", "--role", f"R{i}", "--skills", "python, sql", expect=None,
                        env={"UNTIL_HIRED_LOCK_TIMEOUT": "60"})
                assert r.returncode == 0, r.stderr
        with ThreadPoolExecutor(4) as ex:
            list(ex.map(worker, range(4)))
        market = json.loads((self.ws / "knowledge" / "market.json").read_text(encoding="utf-8"))
        self.assertEqual(market["jds"], 32)
        self.assertEqual(market["skills"]["python"]["count"], 32)

    def _holder(self):
        code = ("import sys,time; sys.path.insert(0, sys.argv[1]); from uhlib import Lock; "
                "from pathlib import Path; l = Lock(Path(sys.argv[2])); l.__enter__(); print('locked', flush=True); time.sleep(120)")
        p = subprocess.Popen([sys.executable, "-c", code, str(SCRIPTS), str(self.ws / "tracker")],
                             stdout=subprocess.PIPE, text=True)
        self.assertEqual(p.stdout.readline().strip(), "locked")
        return p

    def test_busy_gives_exit_5_and_a_killed_holder_releases_the_lock(self):
        p = self._holder()
        try:
            r = run(self.T, "add", "--company", "A", "--role", "R", expect=5, env={"UNTIL_HIRED_LOCK_TIMEOUT": "0.5"})
            self.assertIn("do not delete .lock", r.stderr)
        finally:
            p.kill()
            p.wait()
            p.stdout.close()
        start = time.monotonic()
        run(self.T, "add", "--company", "A", "--role", "R", env={"UNTIL_HIRED_LOCK_TIMEOUT": "10"})
        self.assertLess(time.monotonic() - start, 8)


class Network(unittest.TestCase):
    NET = {"socket", "ssl", "http", "urllib.request", "http.client", "ftplib", "smtplib", "requests", "urllib3", "asyncio"}

    def imports(self, path):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names |= {a.name for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module)
            elif isinstance(node, ast.Call) and getattr(node.func, "id", "") == "__import__":
                names.add("__import__")
        return names

    def test_only_notify_uses_the_network(self):
        for f in SCRIPTS.glob("*.py"):
            names = self.imports(f)
            net = {n for n in names if n in self.NET or n.split(".")[0] in {"socket", "ssl", "http", "requests"}}
            if f.name == "notify.py":
                self.assertEqual(net, {"urllib.request"}, f.name)
            else:
                self.assertEqual(net, set(), f.name)
            self.assertNotIn("__import__", names, f.name)

    def test_data_tools_never_start_processes(self):
        for name in ("uhlib.py", "tracker.py", "knowledge.py", "notify.py"):
            names = self.imports(SCRIPTS / name)
            self.assertFalse({"subprocess", "os.system", "pty"} & names, name)
            self.assertNotRegex((SCRIPTS / name).read_text(encoding="utf-8"), r"os\.(system|popen|exec)", name)

    def test_notify_scrubs_and_sends_counts_only_by_default(self):
        sys.path.insert(0, str(SCRIPTS))
        import notify
        self.assertEqual(notify.scrub("call +1 555 010 0199 or someone@example.com now", 400), "call [removed] or [removed] now")
        self.assertEqual(notify.scrub("code 482913", 400), "code [removed]")


class NotifyModes(Workspace):
    def test_counts_only_and_topic_never_printed(self):
        cfg = json.loads((self.ws / "config.json").read_text(encoding="utf-8"))
        cfg["notifications"]["mode"] = "native"
        cfg["notifications"]["quiet_hours"] = []
        (self.ws / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
        r = run(self.N, "send", "--kind", "interview", "--count", "1",
                "--json", self.inp({"title": "Interview: Acme", "message": "Tue 10:00"}))
        sent = json.loads(r.stdout)["send_with_native_tool"]
        self.assertNotIn("Acme", json.dumps(sent))
        self.assertIn("1 interview update", sent["message"])
        self.assertIn("Acme", (self.ws / "NOTIFICATIONS.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
