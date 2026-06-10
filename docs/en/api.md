---
icon: lucide/list-checks
---

# API Reference

This page lists commonly used APIs by module. Signatures are shortened to the most relevant parameters; use the source and type hints for complete details.

## `asynctor`

The top-level section only lists the most common shortcut imports. More detailed APIs are grouped by their source modules below.

| API | Source Module | Description |
| --- | --- | --- |
| `AsyncRedis(app=None, check_connection=True, **kwargs)` | `asynctor.client` | Async Redis client, usable as a FastAPI state manager or directly |
| `Timer(message, decimal_places=1, verbose=True)` | `asynctor.timing` | Measure sync or async code as a context manager or decorator |
| `run_async(async_func, *args)` | `asynctor.aio` | Run an async function or coroutine in a worker thread from synchronous code and return the result |

```py
from asynctor import Timer, run_async


async def load_user(user_id: int) -> dict[str, int]:
    return {"id": user_id}


with Timer("load user", verbose=False) as timer:
    user = run_async(load_user, 1)

assert user == {"id": 1}
assert timer.cost >= 0
```

```py
from asynctor import AsyncRedis


async def ping_redis() -> bool:
    async with AsyncRedis("localhost", check_connection=False) as redis:
        return await redis.ping()
```

## `asynctor.aio`

Async execution and sync bridging helpers. `run_async` is expanded in the top-level `asynctor` section because it is a common shortcut import.

### `run`

```py
run(func, *args, backend="asyncio", backend_options=None)
```

Run a coroutine object or async function and return its result. Use it from scripts, CLIs, or other synchronous entry points.

```py
from asynctor.aio import run


async def main() -> int:
    return 1


assert run(main()) == 1
```

### `gather`

```py
await gather(*coros, limit=None)
```

Run coroutines concurrently and return a tuple in input order. `limit=None` or `limit=0` means unlimited concurrency.

### `bulk_gather`

```py
await bulk_gather(coros, batch_size=0, wait_last=False, raises=True)
```

Run a sequence or generator of coroutines.

| Parameter | Description |
| --- | --- |
| `coros` | Coroutine sequence or generator |
| `batch_size` | Number of tasks running at once; `0` means unlimited |
| `wait_last` | Wait for the current batch to finish before starting the next batch |
| `raises` | Raise task errors when true; return `None` for failed tasks when false |

### Tasks And Sync Bridges

| API | Description |
| --- | --- |
| `map_group(func, todos, results=None)` | Start many tasks with an anyio task group, optionally collecting results into a provided list |
| `start_tasks(coro, *more)` | Start one or more background tasks in an anyio task group and cancel them when the context exits |
| `wait_for(coro, timeout)` | Run a coroutine with a timeout using anyio cancellation |
| `create_task(coro, task_group, name=None)` | Start one task in an existing anyio task group |
| `async_to_sync(func)` | Wrap an async function as a sync function |
| `run_until_complete(async_func)` | Run an async function or coroutine in a running loop or worker thread |

```py
from asynctor.aio import start_tasks, wait_for


async with start_tasks(background()):
    result = await wait_for(fetch(1), timeout=3)
```

## `asynctor.timing`

`timeit` and `Timer` measure sync or async code. `Timer` can also be imported from top-level `asynctor`.

```py
from asynctor import Timer
from asynctor.timing import timeit


@timeit
async def job() -> None:
    ...


with Timer("load", verbose=False) as timer:
    ...

print(timer.cost)
```

`Timer.current_time()` returns the current Unix timestamp in milliseconds.

```py
timestamp_ms = Timer.current_time()
assert isinstance(timestamp_ms, int)
```

`Timer.beijing_now()` returns a timezone-aware `datetime` for `Asia/Shanghai`.

```py
now = Timer.beijing_now()
assert now.tzinfo is not None
```

## `asynctor.testing`

Required extra:

```sh
pip install "asynctor[testing]"
```

| API | Description |
| --- | --- |
| `anyio_backend_fixture()` | Create a session-scoped pytest fixture named `anyio_backend`, fixed to the `asyncio` backend |
| `async_client_fixture(app, mount_lifespan=True)` | Create a session-scoped async HTTP client fixture named `client` |
| `tmp_workdir_fixture()` | Create a `tmp_work_dir` fixture that switches to `tmp_path` during a test |
| `chdir_tmp_fixture` | Compatibility alias for `tmp_workdir_fixture` |

## `asynctor.contrib.fastapi`

Required extra:

```sh
pip install "asynctor[fastapi]"
```

| API | Description |
| --- | --- |
| `register_aioredis(app, check_connection=True, **kwargs)` | Create a Redis client in FastAPI lifespan and mount it at `app.state.redis` |
| `AioRedisDep` | FastAPI dependency type for retrieving the Redis client from the current request |
| `get_client_ip(request)` | Resolve the client IP from proxy headers or socket information |
| `ClientIpDep` | FastAPI dependency type that returns the real client IP as a string |
| `runserver(app, ...)` | Start a FastAPI development server with `addrport`, `reload`, `prod`, and related options |

## `asynctor.client`

Required extra:

```sh
pip install "asynctor[redis]"
```

| API | Description |
| --- | --- |
| `RedisClient(**kwargs)` | Extension of `redis.asyncio.Redis`; reads `REDIS_HOST` when `host` is not provided |
| `AsyncRedis(app=None, check_connection=True, **kwargs)` | FastAPI state manager or standalone async Redis client; commonly imported from top-level `asynctor` |

## `asynctor.xlsx`

Required extra:

```sh
pip install "asynctor[xlsx]"
```

| API | Return Value | Description |
| --- | --- | --- |
| `read_excel(file, as_str=False, **kwargs)` | `pandas.DataFrame` | Async read from local paths, `anyio.Path`, upload files, bytes, or `BytesIO` |
| `load_xlsx(file, as_str=False, **kwargs)` | `list[dict]` | Read Excel and convert it to a list of dictionaries |
| `pd_read_excel(file, as_str=False, **kwargs)` | `pandas.DataFrame` | Synchronous wrapper around `pandas.read_excel` |
| `df_to_datas(df)` | `list[dict]` | Convert a DataFrame to a list of dictionaries |
| `Excel(filename)` | `Excel` | File-level wrapper with `read`, `aread`, `write`, and `awrite` |

`asynctor.xls` keeps compatibility aliases, where `load_xls` maps to `load_xlsx`.

## `asynctor.jsons`

The `accel` extra installs `orjson`. Without it, asynctor falls back to the standard-library `json` module.

```sh
pip install "asynctor[accel]"
```

| API | Description |
| --- | --- |
| `json_dumps(obj, default=None, pretty=False)` | Serialize to string |
| `json_dump_bytes(obj, default=None, pretty=False)` | Serialize to bytes |
| `json_loads(obj)` | Deserialize JSON |
| `FastJson.dumps(obj, output="bytes", pretty=False)` | Output bytes, string, or write to a `Path` |
| `FastJson.loads(obj)` | Static method alias for `json_loads` |

## `asynctor.utils`

| API | Description |
| --- | --- |
| `client_manager(app, base_url="http://test", mount_lifespan=True, **kwargs)` | Async test client context manager for FastAPI/ASGI apps |
| `AsyncTestClient(app, mount_lifespan=True, base_url="http://test", **kwargs)` | Async test client wrapper for FastAPI apps |
| `AsyncClientGenerator` | Async generator type alias for `httpx.AsyncClient` |
| `AttrDict(data)` | Allow attribute access for string keys in dictionaries; nested dictionaries are converted recursively |
| `local_dict(data, *keys)` | Build a new dictionary by selecting keys from an existing dictionary |
| `get_machine_ip()` | Get the current machine IP, returning `127.0.0.1` on failure |
| `cache_attr(func)` | Cache a class method result on the class object |
| `Shell(command)` | Small `subprocess` wrapper for running commands |
| `load_bool(key)` | Read an environment variable and parse common false-like values as `False` |
| `ExtendSyspath(path, insert=0)` | Temporarily add a directory to `sys.path` inside a context manager |

```py
from asynctor.utils import AttrDict

data = AttrDict({"user": {"name": "Alice"}})
assert data.user.name == "Alice"
```

```py
import os

from asynctor.utils import load_bool

os.environ["MY_ENV"] = "1"
assert load_bool("MY_ENV") is True
```

```py
from asynctor.utils import ExtendSyspath

with ExtendSyspath("tests"):
    import conftest
```

## `asynctor.tasks`

| API | Description |
| --- | --- |
| `ThreadGroup(max_workers=0, timeout=None)` | Manage a group of thread or thread-pool tasks and collect results when the context exits |

```py
from asynctor.tasks import ThreadGroup


def double(value: int) -> int:
    return value * 2


with ThreadGroup(max_workers=2) as tg:
    for value in range(3):
        tg.soonify(double)(value)

assert tg.results == [0, 2, 4]
```
