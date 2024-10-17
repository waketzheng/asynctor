#!/bin/sh -e
set -x

[ -f pyproject.toml ] || ([ -f ../pyproject.toml ] && cd ..)

SKIP_MYPY=1 poetry run fast lint
