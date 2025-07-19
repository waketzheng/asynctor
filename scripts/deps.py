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
from pathlib import Path

__version__ = "0.1.0"
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


def not_distribution() -> bool:
    if (toml := Path(__file__).parent / "pyproject.toml").exists() or (
        (toml := toml.parent.parent / toml.name).exists()
    ):
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            try:
                import tomli as tomllib
            except ImportError:
                return False
        doc = tomllib.loads(toml.read_text("utf8"))
        try:
            return not doc["tool"]["pdm"]["distribution"]
        except KeyError:
            ...
    return False


def main() -> int | None:
    args = sys.argv[1:]
    if len(args) == 1 and args[0] in ("-v", "--version"):
        print(__version__)
        return 0
    if prefer_pdm():
        return int(run_and_echo("pdm install --frozen -G :all" + sys_args()))
    shell = SHELL.strip()
    try:
        index = args.index("--no-dev")
    except IndexError:
        ...
    else:
        args.pop(index)
        shell = shell.replace(" --group dev", "")
    if args:
        extras = " ".join(i if i.startswith("-") else repr(i) for i in args)
        if extras.startswith("-"):
            shell += " " + extras
        else:
            shell += extras  # e.g.: '[xls,fastapi]'
    elif not_distribution():
        shell = shell.replace(" -e .", "")
    cmds = shell.splitlines()
    r = subprocess.run(shlex.split("pdm run python -m pip --version"), capture_output=True)
    if r.returncode == 0:
        cmds = cmds[1:]
    for cmd in cmds:
        if run_and_echo(cmd.strip()):
            return 1
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
