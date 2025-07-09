# ChangeLog

## 0.8
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
