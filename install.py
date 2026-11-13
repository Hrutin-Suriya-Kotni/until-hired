#!/usr/bin/env python3
"""Install the until-hired skills and subagents into a folder for your agent (no plugin manager needed).

  python3 install.py --agent antigravity --target ~/my-job-search
  python3 install.py --agent claude-code --target ~/my-job-search     # project-level, without the guard hook
  python3 install.py --agent codex       --target ~/my-job-search     # experimental
  python3 install.py --agent generic     --target ~/my-job-search     # plain skills/ and agents/ folders

Prefer the plugin install where your agent has one (README, "Install"): on Claude Code it also adds
the guard hook. This script never deletes a folder it did not install: an existing skill folder
without its `.until-hired-installed` marker is left alone unless you pass --force.
Python 3.9+, standard library only.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LAYOUT = {
    "antigravity": (".agents/skills", ".agents/agents"),
    "claude-code": (".claude/skills", ".claude/agents"),
    "codex": (".agents/skills", None),
    "generic": ("skills", "agents"),
}
MARK = ".until-hired-installed"


def version():
    return json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))["version"]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--agent", choices=sorted(LAYOUT), required=True)
    ap.add_argument("--target", type=Path, required=True, help="the folder you will open your agent in")
    ap.add_argument("--force", action="store_true", help="replace same-named folders that this script did not install")
    a = ap.parse_args(argv)
    target = a.target.expanduser().resolve()
    if target == Path.home().resolve() or target == Path(target.anchor):
        sys.exit("choose a project folder, not your home folder or a drive root")
    skills_dir = target / LAYOUT[a.agent][0]
    agents_dir = target / LAYOUT[a.agent][1] if LAYOUT[a.agent][1] else None
    v = version()
    skipped = []
    skills_dir.mkdir(parents=True, exist_ok=True)
    for skill in sorted((ROOT / "skills").iterdir()):
        if not skill.is_dir():
            continue
        dst = skills_dir / skill.name
        if dst.exists():
            if not (dst / MARK).exists() and not a.force:
                skipped.append(str(dst))
                continue
            shutil.rmtree(dst)
        shutil.copytree(skill, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        (dst / MARK).write_text(json.dumps({"until_hired": v}) + "\n", encoding="utf-8")
        print(f"skill  {skill.name} -> {dst}")
    if agents_dir:
        agents_dir.mkdir(parents=True, exist_ok=True)
        for agent in sorted((ROOT / "agents").glob("*.md")):
            dst = agents_dir / agent.name
            if dst.exists() and dst.read_bytes() != agent.read_bytes() and not a.force \
                    and "until-hired subagent" not in dst.read_text(encoding="utf-8", errors="ignore"):
                skipped.append(str(dst))
                continue
            shutil.copyfile(agent, dst)
            print(f"agent  {agent.stem} -> {dst}")
    if skipped:
        print("\nNot replaced (not installed by until-hired; use --force if you are sure):\n  " + "\n  ".join(skipped))
    print(f"\nuntil-hired {v} installed. Open your agent in {target} and say: start my job search")
    return 1 if skipped else 0


if __name__ == "__main__":
    sys.exit(main())
