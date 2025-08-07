# ChangeLog

## 0.8

### [0.8.6]**(Unreleased)

#### Added
- Add `StrEnum` to `asynctor.compat`

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
