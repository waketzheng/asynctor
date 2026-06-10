---
icon: lucide/book-open
---

# asynctor Overview

asynctor is a Python toolkit for async execution helpers, FastAPI testing, Redis integration, and Excel data handling. It is built on anyio, keeps a familiar `asyncio`-style workflow, and adds practical helpers for concurrency limits, sync entry points, testing fixtures, and integrations.

## When To Use It

- You need to limit concurrency and collect async task results.
- You need to call async functions from synchronous code.
- You need lightweight timing for sync or async code.
- You need async tests for a FastAPI application.
- You need Redis lifecycle management in FastAPI.
- You need async-friendly Excel read/write helpers.

## Python Version

asynctor requires Python 3.10 or newer.

## Common Entry Points

| Module | Objects | Purpose |
| --- | --- | --- |
| `asynctor` | `AsyncRedis`, `Timer`, `run_async` | Most common top-level shortcut imports |
| `asynctor.aio` | `gather`, `bulk_gather`, `run`, `map_group`, `start_tasks`, `wait_for` | Async execution, sync bridging, and task helpers |
| `asynctor.timing` | `timeit`, `Timer` | Timing helpers |
| `asynctor.client` | `RedisClient`, `AsyncRedis` | Async Redis clients |
| `asynctor.testing` | `anyio_backend_fixture`, `async_client_fixture`, `tmp_workdir_fixture` | pytest fixtures |
| `asynctor.contrib.fastapi` | `register_aioredis`, `AioRedisDep`, `ClientIpDep`, `runserver` | FastAPI integration |
| `asynctor.xlsx` | `read_excel`, `load_xlsx`, `Excel` | Excel read/write helpers |
| `asynctor.jsons` | `json_dumps`, `json_dump_bytes`, `json_loads`, `FastJson` | JSON serialization helpers |
| `asynctor.utils` | `AttrDict`, `AsyncTestClient`, `load_bool`, `ExtendSyspath`, `Shell` | Test clients, environment flags, and path utilities |

## Quick Example

```py
from anyio import sleep
from asynctor import Timer, run_async


async def main() -> Timer:
    with Timer('do sth', verbose=False) as t:
        await sleep(0.11)
    return t


result = run_async(main)
result2 = run_async(main())

assert str(result) == str(result2) == 'do sth Cost: 0.1 seconds'
assert result.cost == result2.cost == 0.1

print(Timer.beijing_now())
# 2026-06-10 18:01:49.383679+08:00
```

## Next Steps

- Read [Installation](installation.md) to choose the base package or extras.
- Read the [Usage Guide](usage.md) for async, FastAPI, testing, and Excel examples.
