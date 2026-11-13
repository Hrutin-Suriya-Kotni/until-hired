#!/usr/bin/env python3
"""until-hired system check: what this machine can run, and a safe number of parallel browser agents.

Reports OS, CPU, memory, free disk, Python, and whether Chrome/Chromium, Node/npx and git exist.
It does NOT check what the AI agent itself can do (subagents, browser tools, connectors):
the agent-setup skill checks that from the agent's own tool list.
Standard library only. Prints JSON.
"""
import json
import os
import platform
import shutil
import subprocess
import sys


def mem_gb():
    try:
        if sys.platform == "darwin":
            out = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=5).stdout
            return round(int(out.strip()) / 2**30, 1)
        if sys.platform.startswith("linux"):
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal"):
                        return round(int(line.split()[1]) / 2**20, 1)
        if sys.platform == "win32":
            import ctypes

            class MS(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            m = MS(); m.dwLength = ctypes.sizeof(MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return round(m.ullTotalPhys / 2**30, 1)
    except Exception:
        pass
    return None


def find_chrome():
    names = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge"]
    for n in names:
        if shutil.which(n):
            return shutil.which(n)
    mac = ["/Applications/Google Chrome.app", "/Applications/Chromium.app", "/Applications/Microsoft Edge.app"]
    for p in mac:
        if os.path.exists(p):
            return p
    win = [os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
           os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe")]
    for p in win:
        if os.path.exists(p):
            return p
    return None


def main():
    mem = mem_gb()
    cpus = os.cpu_count() or 1
    free_gb = round(shutil.disk_usage(os.path.expanduser("~")).free / 2**30, 1)
    # Each automated browser tab with a modern job site uses roughly 0.5-1 GB.
    if mem is None:
        browsers = 2
    elif mem < 8:
        browsers = 1
    elif mem < 12:
        browsers = 2
    elif mem < 24:
        browsers = 3
    elif mem < 48:
        browsers = 5
    else:
        browsers = 8
    browsers = max(1, min(browsers, cpus // 2 or 1))
    report = {
        "os": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "cpus": cpus,
        "memory_gb": mem,
        "free_disk_gb": free_gb,
        "python": platform.python_version(),
        "python_ok": sys.version_info >= (3, 9),
        "chrome_or_chromium": find_chrome(),
        "node": shutil.which("node"),
        "npx": shutil.which("npx"),
        "git": shutil.which("git"),
        "recommended_parallel_browser_agents": browsers,
        "notes": [
            "One tab per browser agent, closed when the agent finishes. Too many tabs freeze laptops.",
            "Run long sessions while plugged in; a sleeping computer stops every agent.",
        ],
    }
    if free_gb < 5:
        report["notes"].append("Less than 5 GB free: clear space before running browser agents.")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
