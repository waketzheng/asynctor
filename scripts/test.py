#!/usr/bin/env python
# -*- coding:utf-8 -*-
import functools
import os
import shlex
import subprocess
import sys
import time
from enum import IntEnum


class Tools(IntEnum):
    poetry = 0
    pdm = 1
    uv = 2
    none = 3


_tool = Tools.uv
TOOL = getattr(_tool, "name", str(_tool))
PREFIX = (
    (TOOL + " run " + "--no-sync " * (Tools.uv.name == TOOL))
    if TOOL and Tools.none.name != TOOL
    else ""
)
_parent = os.path.abspath(os.path.dirname(__file__))
work_dir = os.path.dirname(_parent)
if os.getcwd() != work_dir:
    os.chdir(work_dir)

RUN = "coverage run -m pytest"
ARGS = ' --doctest-glob="utils.py" -s tests'
COMBINE = "coverage combine .coverage*"
REPORT = 'coverage report --omit="tests/*" -m'
CMD = RUN + ARGS
# PYTHONPATH=examples/fastapi poetry run coverage run --append --source=asynctor -m pytest examples/fastapi
APPEND = "coverage run --append --source=asynctor -m pytest examples/fastapi"


def remove_outdate_files(start_time):
    # type: (float) -> None
    for file in os.listdir(work_dir):
        if not file.startswith(".coverage"):
            continue
        if os.path.getmtime(file) < start_time:
            os.remove(file)
            print("Removed outdate file: {file}".format(file=file))


def run_command(cmd, shell=False, prefix=PREFIX, env=None):
    # type: (str, bool, str, None) -> None
    if prefix and not cmd.startswith(prefix):
        cmd = prefix + cmd
    print("--> {}".format(cmd))
    sys.stdout.flush()
    command = cmd if shell else shlex.split(cmd)
    run = subprocess.Popen
    if env:
        run = functools.partial(run, env=dict(os.environ, **env))
    r = run(command, shell=shell)
    r.wait()
    if r.returncode != 0:
        sys.exit(1)


def combine_result_files(shell=COMBINE):
    # type: (str) -> None
    to_be_combine = [i for i in os.listdir(work_dir) if i.startswith(".coverage.")]
    if not to_be_combine:
        return
    if sys.platform == "win32":
        if os.path.exists(os.path.join(work_dir, ".coverage")):
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
