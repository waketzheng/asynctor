#!/usr/bin/env python
"""
Install deps by `pdm install -G :all --frozen`
if value of `pdm config use_uv` is True,
otherwise by the following shells:
```bash
pdm run python -m ensurepip
pdm run python -m pip install --upgrade pip
pdm run python -m pip install --group dev -e .
```

Usage::
    pdm run python scripts/deps.py
"""

from __future__ import annotations

import os
import platform
import shlex
import subprocess
import sys

SHELL = """
pdm run python -m ensurepip
pdm run python -m pip install --upgrade pip
pdm run python -m pip install --group dev -e .
"""


def sys_args() -> str:
    if not (args := sys.argv[1:]):
        return ""
    return " ".join(repr(i) for i in args)


def run_and_echo(cmd: str) -> bool:
    print("-->", cmd)
    return os.system(cmd.strip()) != 0


def capture_output(cmd: str) -> str:
    r = subprocess.run(shlex.split(cmd), capture_output=True, text=True, encoding="utf-8")
    return r.stdout.strip()


def is_using_uv() -> bool:
    return capture_output("pdm config use_uv").lower() == "true"


def prefer_pdm() -> bool:
    if (s := "--pip") in sys.argv:
        sys.argv.pop(sys.argv.index(s))
        return False
    return platform.system() != "Windows" or is_using_uv()


def main() -> int | None:
    if prefer_pdm():
        return int(run_and_echo("pdm install --frozen -G :all" + sys_args()))
    shell = SHELL.strip()
    args = sys.argv[1:]
    if args:
        shell += " ".join(i if i.startswith("-") else repr(i) for i in args)
    cmds = shell.splitlines()
    for cmd in cmds:
        if run_and_echo(cmd.strip()):
            return 1
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
