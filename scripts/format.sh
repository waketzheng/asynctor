#!/bin/sh -e
set -x

[ -f ../pyproject.toml ] && cd ..

poetry run ruff format .
poetry run ruff check --extend-select=I --fix .
