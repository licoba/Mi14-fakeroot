from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def print_cmd(args: list[str]) -> None:
    print("> " + " ".join(quote_arg(arg) for arg in args))


def quote_arg(arg: str) -> str:
    if not arg:
        return '""'
    if any(ch.isspace() for ch in arg):
        return '"' + arg.replace('"', '\\"') + '"'
    return arg


def run(args: list[str], execute: bool) -> int:
    print_cmd(args)
    if not execute:
        print("(dry-run)")
        return 0
    return subprocess.run(args, check=False).returncode


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        print(f"[缺失] PATH 里找不到 {name}", file=sys.stderr)
        raise SystemExit(1)
    return path


def adb_shell(command: str, execute: bool = True) -> int:
    return run(["adb", "shell", command], execute)
