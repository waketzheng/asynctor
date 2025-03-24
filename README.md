# asynctor
![Python Versions](https://img.shields.io/pypi/pyversions/asynctor)
[![LatestVersionInPypi](https://img.shields.io/pypi/v/asynctor.svg?style=flat)](https://pypi.python.org/pypi/asynctor)
[![GithubActionResult](https://github.com/waketzheng/asynctor/workflows/ci/badge.svg)](https://github.com/waketzheng/asynctor/actions?query=workflow:ci)
[![Coverage Status](https://coveralls.io/repos/github/waketzheng/asynctor/badge.svg?branch=main)](https://coveralls.io/github/waketzheng/asynctor?branch=main)
![Mypy coverage](https://img.shields.io/badge/mypy-100%25-green.svg)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Some async functions that using anyio, and toolkit for excel read.

## Installation

<div class="termy">

```console
$ pip install asynctor
---> 100%
Successfully installed asynctor
```
Or use poetry:
```console
poetry add asynctor
```

## Usage

- Async function that compare asyncio but use anyio: `bulk_gather/gather/run`
```py
>>> import asynctor
>>> async def foo():
...     return 1
...
>>> await asynctor.bulk_gather([foo(), foo()], limit=200)
(1, 1)
>>> await asynctor.gather(foo(), foo())
(1, 1)
>>> asynctor.run(gather(foo(), foo()))
(1, 1)
```
- timeit
```py
>>> import time
>>> import anyio
>>> from asynctor import timeit
>>> @timeit
... async def sleep_test():
...     await anyio.sleep(3)
...
>>> await sleep()
sleep_test Cost: 3.0 seconds

>>> @timeit
... def sleep_test2():
...     time.sleep(3.1)
...
>>> sleep_test2()
sleep_test2 Cost: 3.1 seconds
```
- AioRedis
```py
from asynctor.contrib.fastapi import AioRedis, register_aioredis
from fastapi import FastAPI, Request

app = FastAPI()
register_aioredis(app)

@app.get('/')
async def root(redis: AioRedis) -> list[str]:
    return await redis.keys()

@app.get('/redis')
async def get_value_from_redis_by_key(redis: AioRedis, key: str) -> str:
    value = await redis.get(key)
    if not value:
        return ''
    return value.decode()
```
- AsyncTestClient
```py
import pytest
from asynctor import AsyncTestClient, AsyncClientGenerator
from httpx import AsyncClient

from main import app

@pytest.fixture(scope='session')
async def client() -> AsyncClientGenerator:
    async with AsyncTestClient(app) as c:
        yield c

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.mark.anyio
async def test_api(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
```

- Read Excel File(need to install with xls extra: `pip install "asynctor[xls]"`)
```py
>>> from asynctor.xls import load_xls
>>> await load_xls('tests/demo.xlsx')
[{'Column1': 'row1-\\t%c', 'Column2\nMultiLines': 0, 'Column 3': 1, 4: ''}, {'Column1': 'r2c1\n00', 'Column2\nMultiLines': 'r2 c2', 'Column 3': 2, 4: ''}]
```
