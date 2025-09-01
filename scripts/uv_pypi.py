#!/usr/bin/env python
"""Auto change registry of uv.lock to be pypi.org

Usage::
    python3 <me>.py
"""

import os
import sys

cmd = "fast pypi"
args = sys.argv[1:]
if args:
    cmd += " " + " ".join(repr(i) if " " in i else i for i in args)
rc = os.system(cmd)
if rc:
    sys.exit(1)
