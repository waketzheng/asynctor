#!/usr/bin/env bash

set -e
[ -f ../pyproject.toml ] && cd ..

poetry run coverage run -m pytest -s --doctest-glob="utils.py" tests/
PYTHONPATH=examples/fastapi poetry run coverage run --append --source=asynctor -m pytest examples/fastapi
poetry run coverage report --omit="tests/*" -m
