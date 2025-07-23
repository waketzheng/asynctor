help:
	@echo  "Asynctor development makefile"
	@echo
	@echo  "Usage: make <target>"
	@echo  "Targets:"
	@echo  "    up      Updates dev/test dependencies"
	@echo  "    deps    Ensure dev/test dependencies are installed"
	@echo  "    check   Checks that build is sane"
	@echo  "    test    Runs all tests"
	@echo  "    style   Auto-formats the code"
	@echo  "    lint    Auto-formats the code and check type hints"
	@echo  "    build   Build wheel file and tar file from source to dist/"

up:
	uv lock --upgrade
	uv sync --frozen
	pdm run fast upgrade
	pdm run python scripts/uv_pypi.py --verbose

lock:
	uv lock --upgrade
	pdm run python scripts/uv_pypi.py
	pdm lock --group :all $(options)

venv:
	pdm venv create $(version)

venv39:
	$(MAKE) venv version=3.9

deps:
	uv sync --all-extras --all-groups
	pdm install --group :all --frozen $(options)

start:
	pre-commit install
	$(MAKE) deps

_check:
	./scripts/check.py
check: deps _build _check

_lint:
	pdm run fast lint $(options)
lint: deps _build _lint

_test:
	./scripts/test.py
test: deps _test

_style:
	./scripts/format.py
style: deps _style

_build:
	pdm build
build: deps _build

publish: deps _build
	pdm run fast upload

ci: check _test
