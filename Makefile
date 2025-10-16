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
	uv sync --frozen --inexact
	python scripts/uv_pypi.py --quiet

lock:
	uv lock --upgrade
	python scripts/uv_pypi.py --quiet

venv:
	pdm venv create $(options) $(version)

venv39:
	$(MAKE) venv version=3.9

deps:
	uv sync --all-extras --all-groups --inexact $(options)
	uv run --no-sync fast pypi --quiet

start:
	pre-commit install
	$(MAKE) deps

_check:
	./scripts/check.py
check: deps _build _check

_lint:
	fast lint $(options)
lint: deps _build _lint

_test:
	./scripts/test.py
test: deps _test

_style:
	./scripts/format.py
style: deps _style

_build:
	rm -fR dist/
	uv build
build: deps _build

bump_part = patch

_bump:
	fast bump $(bump_part) $(bump_opts)
bump: deps _bump

release: deps _build
	# fast upload -- Use github action instead
	$(MAKE) _bump bump_opts=--commit
	$(MAKE) deps
	fast tag

ci: check _test

_verify: up lock
	$(MAKE) venv options=--force
	$(MAKE) venv39 options=--force
	$(MAKE) venv version=3.12 options=--force
	$(MAKE) start
	$(MAKE) deps
	$(MAKE) check
	$(MAKE) _check
	$(MAKE) lint
	$(MAKE) _lint
	$(MAKE) test
	$(MAKE) _test
	$(MAKE) style
	$(MAKE) _style
	$(MAKE) build
	$(MAKE) _build
	$(MAKE) ci
