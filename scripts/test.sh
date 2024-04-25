#!/usr/bin/env bash

set -e
poetry run coverage run -m pytest -s
poetry run coverage report --omit="tests/*" -m
