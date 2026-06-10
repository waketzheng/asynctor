---
icon: lucide/code
---

# Usage Guide

## Async Execution

`gather` is similar to `asyncio.gather`, with an optional `limit` for concurrency control.

```py
from asynctor.aio import gather


async def fetch(item: int) -> int:
    return item * 2


results = await gather(
    fetch(1),
    fetch(2),
    fetch(3),
    limit=2,
)
assert results == (2, 4, 6)
```

`bulk_gather` is useful when you execute a list or generator of coroutines. `batch_size` controls how many tasks run at once, and `wait_last=True` waits for each batch to finish before starting the next one.

```py
from asynctor.aio import bulk_gather

coros = [fetch(i) for i in range(5)]
results = await bulk_gather(coros, batch_size=2, wait_last=True)
```

`run` executes a coroutine or async function from a synchronous entry point.

```py
from asynctor.aio import run


async def main() -> str:
    return "ok"


assert run(main()) == "ok"
```

`run_async` starts a worker thread, runs an async function, and returns the result to synchronous code.

```py
from asynctor import run_async


async def load_user(user_id: int) -> dict[str, int]:
    return {"id": user_id}


user = run_async(load_user, 1)
assert user == {"id": 1}
```

`wait_for` wraps a coroutine with anyio's timeout handling.

```py
from asynctor.aio import wait_for


result = await wait_for(fetch(1), timeout=3)
```

`start_tasks` starts background tasks inside a context and cancels them when the context exits.

```py
import anyio
from asynctor.aio import start_tasks


async def background() -> None:
    while True:
        await anyio.sleep(1)


async with start_tasks(background()):
    ...
```

## Timing

`timeit` can be used as a decorator or as a context manager.

```py
import anyio
from asynctor.timing import timeit


@timeit
async def sleep_test() -> None:
    await anyio.sleep(0.1)


await sleep_test()

with timeit("load data"):
    await anyio.sleep(0.1)
```

Use `Timer` when you want to keep the measured cost without printing it.

```py
from asynctor import Timer


with Timer("job", verbose=False) as timer:
    ...

assert isinstance(timer.cost, float)

beijing_now = Timer.beijing_now()
assert beijing_now.tzinfo is not None
```

## FastAPI Redis

Install the FastAPI extra:

```sh
pip install "asynctor[fastapi]"
```

Register Redis on the application and receive the client through dependency injection.

```py
from asynctor.contrib.fastapi import AioRedisDep, register_aioredis
from fastapi import FastAPI

app = FastAPI()
register_aioredis(app, host="localhost", port=6379)


@app.get("/redis")
async def get_value(redis: AioRedisDep, key: str) -> str:
    value = await redis.get(key)
    return "" if value is None else value.decode()
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

## Async Tests

Install the testing extra:

```sh
pip install "asynctor[testing]"
```

Create pytest fixtures in `conftest.py`:

```py
import pytest
from asynctor.testing import anyio_backend_fixture, async_client_fixture
from httpx import AsyncClient

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
from asynctor.testing import tmp_workdir_fixture

tmp_work_dir = tmp_workdir_fixture()
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
