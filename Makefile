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
	just up

lock:
	just lock

venv:
	just venv

venv39:
	just venv 3.9

deps:
	just deps

start:
	just start

_check:
	just _check
check:
	just check

_lint:
	just _lint
lint:
	just lint

_test:
	just _test
test:
	just test

_style:
	just _style
style:
	just style

_build:
	rm -fR dist/
	just _build
build:
	just build

_bump:
	just _bump
bump:
	just bump

release:
	just release
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
