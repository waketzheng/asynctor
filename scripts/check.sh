#!/usr/bin/env bash

set -e
set -x

[ -f pyproject.toml ] || ([ -f ../pyproject.toml ] && cd ..)

poetry run fast check
poetry run bandit -r asynctor
