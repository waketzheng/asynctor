---
icon: lucide/code
---

# 使用指南

## 异步执行

`gather` 接近 `asyncio.gather`，并支持通过 `limit` 控制并发数量。

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

`bulk_gather` 适合从列表或生成器批量执行协程。`batch_size` 控制同时运行的任务数量，`wait_last=True` 表示每批完成后再启动下一批。

```py
from asynctor.aio import bulk_gather

coros = [fetch(i) for i in range(5)]
results = await bulk_gather(coros, batch_size=2, wait_last=True)
```

`run` 可在同步入口中运行协程或异步函数。

```py
from asynctor.aio import run


async def main() -> str:
    return "ok"


assert run(main()) == "ok"
```

`run_async` 可在已有同步代码中启动一个工作线程运行异步函数，并返回结果。

```py
from asynctor import run_async


async def load_user(user_id: int) -> dict[str, int]:
    return {"id": user_id}


user = run_async(load_user, 1)
assert user == {"id": 1}
```

`wait_for` 用 anyio 的超时机制包装协程。

```py
from asynctor.aio import wait_for


result = await wait_for(fetch(1), timeout=3)
```

`start_tasks` 适合在 lifespan 或上下文中启动后台任务，退出上下文时自动取消。

```py
import anyio
from asynctor.aio import start_tasks


async def background() -> None:
    while True:
        await anyio.sleep(1)


async with start_tasks(background()):
    ...
```

## 耗时统计

`timeit` 可作为装饰器或上下文管理器使用。

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

如果需要保留耗时值，使用 `Timer` 并关闭输出。

```py
from asynctor import Timer


with Timer("job", verbose=False) as timer:
    ...

assert isinstance(timer.cost, float)

beijing_now = Timer.beijing_now()
assert beijing_now.tzinfo is not None
```

## FastAPI Redis

安装 FastAPI 扩展：

```sh
pip install "asynctor[fastapi]"
```

注册 Redis 后，可通过依赖注入获取客户端。

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

获取真实客户端 IP：

```py
from asynctor.contrib.fastapi import ClientIpDep


@app.get("/ip")
async def ip(client_ip: ClientIpDep) -> str:
    return client_ip
```

开发环境启动 FastAPI：

```py
from asynctor.contrib.fastapi import runserver
from fastapi import FastAPI

app = FastAPI()


if __name__ == "__main__":
    runserver(app, reload=True)
```

## 异步测试

安装测试扩展：

```sh
pip install "asynctor[testing]"
```

在 `conftest.py` 中创建 pytest 夹具：

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

需要临时工作目录时：

```py
from asynctor.testing import tmp_workdir_fixture

tmp_work_dir = tmp_workdir_fixture()
```

## Excel 读写

安装 Excel 扩展：

```sh
pip install "asynctor[xlsx]"
```

读取 Excel 为字典列表：

```py
from asynctor.xlsx import load_xlsx

rows = await load_xlsx("tests/demo.xlsx")
assert isinstance(rows, list)
```

读取为 DataFrame：

```py
from asynctor.xlsx import read_excel

df = await read_excel("tests/demo.xlsx")
```

使用 `Excel` 类写入和读取：

```py
from asynctor.xlsx import Excel

excel = Excel("demo.xlsx")
await excel.awrite([{"name": "Alice", "score": 100}])
df = await excel.aread()
```

## JSON 辅助函数

`asynctor.jsons` 会在安装了 `orjson` 时自动使用它，否则回退到标准库
`json`。

```py
from asynctor.jsons import json_dump_bytes

assert json_dump_bytes({"a": 1}) == b'{"a":1}'
assert json_dump_bytes({"a": 1}, pretty=True) == b'{\n  "a": 1\n}'
```

## 实用工具

`AttrDict` 支持通过属性访问字典中的字符串键。

```py
from asynctor.utils import AttrDict

data = AttrDict({"user": {"name": "Alice"}})
assert data.user.name == "Alice"
```

`load_bool` 读取环境变量，并把常见的 false-like 值解析为 `False`。

```py
import os

from asynctor.utils import load_bool

assert load_bool("NOT_EXIST") is False

os.environ["MY_ENV"] = "0"
assert load_bool("MY_ENV") is False

os.environ["MY_ENV"] = "1"
assert load_bool("MY_ENV") is True
```

`ExtendSyspath` 可临时把目录加入 `sys.path`。

```py
from pathlib import Path

from asynctor.utils import ExtendSyspath

with ExtendSyspath("tests"):
    import conftest

assert Path(conftest.__file__).relative_to(Path.cwd()).as_posix() == "tests/conftest.py"
```
