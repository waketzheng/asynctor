---
icon: lucide/code
---

# Usage Guide

## Async Execution

`gather` is similar to `asyncio.gather`, with an optional `limit` for concurrency control.

```py
import time
import anyio
from asynctor.aio import gather


async def fetch(item: int) -> int:
    await anyio.sleep(0.1)
    return item * 2


# Without `limit`, it behaves like `asyncio.gather`.
start = time.time()
assert (await gather(*[fetch(i) for i in range(3)])) == (0, 2, 4)
assert 0.1 <= time.time() - start <= 0.2

# With `limit=1`, only one async task runs at a time.
start = time.time()
results = await gather(
    fetch(1),
    fetch(2),
    fetch(3),
    limit=1,
)
assert results == (2, 4, 6)
assert 0.3 <= time.time() - start <= 0.4
```

`bulk_gather` extends `gather` and is useful when you execute a list or generator of coroutines. `batch_size` controls how many tasks run at once, and `wait_last=True` waits for each batch to finish before starting the next one.

```py
from asynctor.aio import bulk_gather

coros = [fetch(i) for i in range(5)]
results = await bulk_gather(coros, batch_size=2, wait_last=True)
```

`run` combines `asyncio.run` and `anyio.run`: it accepts either a coroutine or an async function.

```py
import asynctor


async def main() -> str:
    return "ok"


assert asynctor.run(main()) == "ok"
assert asynctor.run(main) == "ok"
```

`run_async` starts a worker thread, runs an async function, and returns the result to synchronous code.

```py
from asynctor import run_async


async def load_user(user_id: int) -> dict[str, int]:
    return {"id": user_id}


user = run_async(load_user, 1)
assert user == {"id": 1}
```

## Timing

`timeit` is a convenient timing helper for development and can be used as a decorator or as a context manager.

*Note: it keeps one decimal place.*

```py
import anyio
from asynctor import run_async, timeit


@timeit
async def sleep_test() -> None:
    await anyio.sleep(0.11)


run_async(sleep_test)
# sleep_test Cost: 0.1 seconds


async def main() -> None:
    with timeit("load data"):
        await anyio.sleep(0.11)

run_async(main)
# load data Cost: 0.1 seconds
```

Use the more capable `Timer` in production code.

```py
import anyio
from asynctor import Timer


async def my_func() -> None:
    with Timer("job", decimal_places=3, verbose=False) as timer:
        await anyio.sleep(0.11)

    print(timer)
    # job Cost: 0.111 seconds

    assert isinstance(timer.cost, float)


utc_now = Timer.now()  # UTC time with timezone information
beijing_now = Timer.beijing_now()  # Beijing time with timezone information
assert beijing_now.tzinfo is not None
assert beijing_now.tzinfo.zone == "Asia/Shanghai"
```

## FastAPI Redis

Install the FastAPI extra:

```sh
pip install "asynctor[fastapi]"
```

Register Redis on the application and receive the client through dependency injection.

```py
from asynctor import AsyncRedis
from asynctor.contrib.fastapi import AioRedisDep, register_aioredis
from fastapi import FastAPI

app = FastAPI()
register_aioredis(app, host="localhost", port=6379, db=0)


@app.get("/redis")
async def get_value(redis: AioRedisDep, key: str) -> str:
    value = await redis.get(key)
    return "" if value is None else value.decode()


@app.get("/redis-keys")
async def get_keys(redis: AioRedisDep, pattern: str | None = None) -> list[str]:
    keys = await _get_redis_keys(redis, pattern)
    return [item.decode() if isinstance(item, bytes) else item for item in keys]


async def _get_redis_keys(redis: AsyncRedis, pattern: str | None) -> list[bytes | str]:
    if pattern:
        keys = await redis.keys(pattern)
    else:
        keys = await redis.keys()
    return keys
```

Use `AsyncRedis` directly when only the Redis extra is installed:

```sh
pip install "asynctor[redis]"
```

```py
from asynctor import AsyncRedis

redis = AsyncRedis()
await redis.__aenter__()  # Verify that the Redis server responds to ping.

await redis.keys()
await redis.get("a")
expire = 30  # Seconds
await redis.set("key", "value", expire)

await redis.aclose()  # Close the Redis connection.
```

Resolve the real client IP:

```py
from asynctor.contrib.fastapi import ClientIpDep


@app.get("/ip")
async def ip(client_ip: ClientIpDep) -> str:
    return client_ip
```

Start FastAPI in development:

```py
from asynctor.contrib.fastapi import runserver
from fastapi import FastAPI

app = FastAPI()


if __name__ == "__main__":
    runserver(app, reload=True)
```

Other common FastAPI configuration helpers:

```py
from asynctor.contrib.fastapi import add_timing_middleware, config_access_log
from fastapi import FastAPI

app = FastAPI()
add_timing_middleware(app)  # Add execution time to response headers.
config_access_log()  # Include request time and source IP in access logs.
```

## Async Tests

Install the testing extra:

```sh
pip install "asynctor[testing]"
```

Create pytest fixtures in `conftest.py`:

```py
import pytest
from asynctor.testing import AsyncClient, anyio_backend_fixture, async_client_fixture

from main import app

anyio_backend = anyio_backend_fixture()
client = async_client_fixture(app)


@pytest.mark.anyio
async def test_api(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
```

For a temporary working directory:

```py
from pathlib import Path

from asynctor.testing import tmp_workdir_fixture

tmp_workdir = tmp_workdir_fixture()


def test_xxx(tmp_workdir: Path) -> None:
    # A dedicated temporary directory is created and selected as cwd for this test.
    # It is removed automatically after the test finishes.
    assert Path.cwd() == tmp_workdir
    assert tmp_workdir != Path(__file__).parent
    assert list(tmp_workdir.glob("*")) == []
```

## Excel Read/Write

Install the Excel extra:

```sh
pip install "asynctor[xlsx]"
```

Read Excel data into a list of dictionaries:

```py
from asynctor.xlsx import load_xlsx

rows = await load_xlsx("tests/demo.xlsx")
assert isinstance(rows, list)
```

Read into a DataFrame:

```py
from asynctor.xlsx import read_excel

df = await read_excel("tests/demo.xlsx")
```

Use the `Excel` class for writing and reading:

```py
from asynctor.xlsx import Excel

excel = Excel("demo.xlsx")
await excel.awrite([{"name": "Alice", "score": 100}])
df = await excel.aread()
```

## JSON Helpers

`asynctor.jsons` uses `orjson` automatically when it is installed and falls back
to the standard-library `json` module otherwise.

```py
from asynctor.jsons import json_dump_bytes

assert json_dump_bytes({"a": 1}) == b'{"a":1}'
assert json_dump_bytes({"a": 1}, pretty=True) == b'{\n  "a": 1\n}'
```

## Utilities

`AttrDict` supports attribute access for string keys in dictionaries.

```py
from asynctor.utils import AttrDict

data = AttrDict({"user": {"name": "Alice"}})
assert data.user.name == "Alice"
```

`load_bool` reads an environment variable and treats common false-like values as
false.

```py
import os

from asynctor.utils import load_bool

assert load_bool("NOT_EXIST") is False

os.environ["MY_ENV"] = "0"
assert load_bool("MY_ENV") is False

os.environ["MY_ENV"] = "1"
assert load_bool("MY_ENV") is True
```

`ExtendSyspath` temporarily prepends a directory to `sys.path`.

```py
from pathlib import Path

from asynctor.utils import ExtendSyspath

with ExtendSyspath("tests"):
    import conftest

assert Path(conftest.__file__).relative_to(Path.cwd()).as_posix() == "tests/conftest.py"
```

Without `ExtendSyspath`, code often becomes less direct:

1. Importing twice is more verbose.

```py
import sys

try:
    import conftest
except ImportError:
    sys.path.append("tests")

    import conftest
```

2. Adding imports after executable code is flagged by tools such as Ruff.

```py
import sys

sys.path.append("tests")
import conftest
```
