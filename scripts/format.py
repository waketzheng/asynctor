#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Run `ruff format` to make style and `ruff check --fix` to remove unused imports

Usage:
    ./scripts/format.py

"""

import os
import sys
from enum import IntEnum


class Tools(IntEnum):
    poetry = 0
    pdm = 1
    uv = 2
    none = 3


CMD = "fast lint --skip-mypy"
_tool = Tools.pdm
TOOL = getattr(_tool, "name", str(_tool))
PREFIX = (TOOL + " run ") if TOOL and Tools.none.name != TOOL else ""
_parent = os.path.abspath(os.path.dirname(__file__))
work_dir = os.path.dirname(_parent)
if os.getcwd() != work_dir:
    os.chdir(work_dir)

cmd = PREFIX + CMD
if os.system(cmd) != 0:
    sys.exit(1)
