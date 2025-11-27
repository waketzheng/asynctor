# ChangeLog

## 0.11

### [0.11.2]*(Unrelease)*

#### Added
- feat: add `Timer.get_cost` function
- feat: add `Shell.run_and_echo`

### [0.11.1](../../releases/tag/v0.11.1) - 2025-11-26

#### Added
- feat: echo docs url when runserver

### [0.11.0](../../releases/tag/v0.11.0) - 2025-11-24

#### Added
- feat: runserver function for fastapi project (#28)

#### Changed
- Migrate from Makefile to justfile (#27)

## 0.10

### [0.10.3](../../releases/tag/v0.10.3) - 2025-11-09

#### Added
- Add `config_access_log_to_show_time` for fastapi
- refactor: add property `zone` to ZoneInfo for pytz-compatible

### [0.10.2](../../releases/tag/v0.10.2) - 2025-11-04

#### Added
- Add `asynctor.jsons.FastJson`
- Add some type alias for asynctor.jsons

#### Changed
- Remove 'ParamSpec' from asynctor.compat as it can be imported from typing

### [0.10.1](../../releases/tag/v0.10.1) - 2025-10-29

#### Added
- Add `asynctor.testing` module
- Add `testing` extra

#### Changed
- refactor: use async func for ClientIpDep
- refactor: export Timer to support `from asynctor import Timer`

### [0.10.0](../../releases/tag/v0.10.0) - 2025-10-16

#### Changed
- refactor: drop support for Python3.9

## 0.9

### [0.9.1](../../releases/tag/v0.9.1) - 2025-10-16

#### Added
- Add `be_awaitable` decorator to the aio module

#### Changed
- refactor: simplify `run_async`

### [0.9.0](../../releases/tag/v0.9.0) - 2025-09-22

#### Changed
- refactor: rename `asynctor.xls` to `asynctor.xlsx`

## 0.8

### [0.8.8](../../releases/tag/v0.8.8) - 2025-09-07

#### Added
- Add `asynctor.xls.Excel`
- Add `asynctor.jsons`

### [0.8.7](../../releases/tag/v0.8.7) - 2025-08-15

#### Added
- Add `asynctor.xls.pd_read_excel`
- Add `NotRequired` and `ParamSpec` to asynctor.compat

#### Changed
- refactor: use `ZoneInfo("Asia/Shanghai")` instead `timedelta(hours=8)` for `Timer.beijing_now`
- `asynctor.util.Shell.run` support `**kw`
- `asynctor.xls.read_excel` accept UploadFile as parameter

### [0.8.6](../../releases/tag/v0.8.6) - 2025-08-07

#### Added
- Add `StrEnum` to `asynctor.compat`
- Add `Self` to `asynctor.compat`
- Add `load_toml` to `asynctor.compat`
- feat: support `from asynctor import Shell`

### [0.8.5](../../releases/tag/v0.8.5) - 2025-08-07

#### Added
- Add `async_to_sync` and `run_until_complete` to aio
- Add `chdir` to new module `asynctor.compat`

### [0.8.4](../../releases/tag/v0.8.4) - 2025-07-19

#### Added
- Support `limit` for `asynctor.gather()`
- Add `ClientIpDep` to fastapi contrib

#### Changed
- Use `AioRedisDep` instead of `AioRedis`

### [0.8.3](../../releases/tag/v0.8.3) - 2025-07-09

#### Fixes
- Fix mypy complaint for `asynctor.aio.bulk_gather`

### [0.8.2](../../releases/tag/v0.8.2) - 2025-07-09

#### Changed
- Run `anyio.lowlevel.checkpoint` when pass empty list to `bulk_gather`

#### Fixes
- Only append None to results when argument is generator for `bulk_gather`

### [0.8.1](../../releases/tag/v0.8.1) - 2025-07-05

#### Added
- Support `Timer.now()` and `Timer.beijing_now()`
- Add `run_until_complete` to `asynctor.aio`

#### Changed
- Use `TypeAlias` to improve type hints
- Migrate manage tool from poetry to pdm
