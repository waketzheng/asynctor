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
	pdm run fast upgrade

lock:
	pdm lock --group :all --strategy inherit_metadata

deps:
	pdm install --verbose --group :all --without=ci --frozen

_check:
	./scripts/check.py
check: deps _build _check

_lint:
	pdm run fast lint
lint: deps _build _lint

_test:
	./scripts/test.py
test: deps _test

_style:
	./scripts/format.py
style: deps _style

_build:
	rm -fR dist/
	pdm build
build: deps _build

publish: deps _build
	pdm run fast upload

ci: check _test
