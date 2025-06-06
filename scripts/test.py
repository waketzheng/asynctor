#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

TOOL = ("poetry", "pdm", "")[1]
work_dir = Path(__file__).parent.resolve().parent
if Path.cwd() != work_dir:
    os.chdir(str(work_dir))

RUN = "coverage run -m pytest"
ARGS = ' --doctest-glob="utils.py" -s tests'
COMBINE = "coverage combine .coverage*"
REPORT = 'coverage report --omit="tests/*" -m'
CMD = RUN + ARGS
# PYTHONPATH=examples/fastapi poetry run coverage run --append --source=asynctor -m pytest examples/fastapi
APPEND = "coverage run --append --source=asynctor -m pytest examples/fastapi"


def remove_outdate_files(start_time: float) -> None:
    for file in work_dir.glob(".coverage*"):
        if file.stat().st_mtime < start_time:
            file.unlink()
            print(f"Removed outdate file: {file}")


def run_command(cmd: str, shell=False, tool=TOOL, env=None) -> None:
    prefix = tool + " run "
    if tool and not cmd.startswith(prefix):
        cmd = prefix + cmd
    print("-->", cmd, flush=True)
    if env is not None:
        env = dict(os.environ, **env)
    r = subprocess.run(cmd if shell else shlex.split(cmd), shell=shell, env=None)
    r.returncode and sys.exit(1)


def combine_result_files(shell=COMBINE) -> None:
    to_be_combine = [i.name for i in work_dir.glob(".coverage.*")]
    if to_be_combine:
        if sys.platform == "win32":
            if work_dir.joinpath(".coverage").exists():
                shell = shell.replace("*", " ")
            else:
                shell = shell.replace(".coverage*", "")
            shell += " ".join(to_be_combine)
        run_command(shell, True)


started_at = time.time()
run_command(CMD)
run_command(APPEND, env={"PYTHONPATH": "examples/fastapi"})
remove_outdate_files(started_at)
combine_result_files()
run_command(REPORT)
