---
icon: lucide/code
---

# 使用指南

## 异步执行

`gather` 接近 `asyncio.gather`，并支持通过 `limit` 控制并发数量。

```py
import time
import anyio
from asynctor.aio import gather


async def fetch(item: int) -> int:
    await anyio.sleep(0.1)
    return item * 2

# 不加limit参数的话，等同于asyncio.gather
start = time.time()
assert (await gather(*[fetch(i) for i in range(3)]))  == (0, 1, 4)
assert 0.1 <= time.time() - start <= 0.2

# 加上limit=1，同一个时间内只会执行一个异步任务
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

`bulk_gather`是gather的扩展版，适合从列表或生成器批量执行协程。`batch_size` 控制同时运行的任务数量，`wait_last=True` 表示每批完成后再启动下一批。

```py
from asynctor.aio import bulk_gather

coros = [fetch(i) for i in range(5)]
results = await bulk_gather(coros, batch_size=2, wait_last=True)
```

`run` 揉合了asyncio.run和anyio.run, 即可传Coroutine，也可传AsyncFunction。

```py
import asynctor


async def main() -> str:
    return "ok"


assert asynctor.run(main()) == "ok"
assert asynctor.run(main) == "ok"
```

`run_async` 可在已有同步代码中启动一个工作线程运行异步函数，并返回结果。

```py
from asynctor import run_async


async def load_user(user_id: int) -> dict[str, int]:
    return {"id": user_id}


user = run_async(load_user, 1)
assert user == {"id": 1}
```

## 耗时统计

`timeit` 开发环境用的便捷耗时统计, 可作为装饰器或上下文管理器使用。

*注：只会保留一位小数*

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

生产环境可用功能更强大的`Timer`。

```py
import anyio
from asynctor import Timer
from loguru import logger


async def my_func() -> None:
    with Timer("job", decimal_places=3, verbose=False) as t:
        await anyio.sleep(0.11)

    logger.debug(t)
    # job Cost: 0.111 seconds

    assert isinstance(t.cost, float) and t.cost == 0.111


utc_now = Timer.now()  # 带时区信息的UTC时间
beijing_now = Timer.beijing_now()  # 带时区信息的北京时间
assert beijing_now.tzinfo is not None
assert beijing_now.tzinfo.zone == 'Asia/Shanghai'
```

## FastAPI Redis

安装 FastAPI 扩展：

```sh
pip install "asynctor[fastapi]"
```

注册 Redis 后，可通过依赖注入获取客户端。

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
async def get_value(redis: AioRedisDep, pattern: str | None = None) -> list[str]:
    keys = await _get_redis_keys(redis, pattern)
    return [i.decode() if isinstance(i, bytes) else i for i in keys]


async def _get_redis_keys(redis: AsyncRedis, pattern: str | None) -> list[bytes | str]:
    if pattern:
        keys = await redis.keys(pattern)
    else:
        keys = await redis.keys()
    return keys
```
单独使用AsyncRedis(需要安装redis可选依赖：`pip install "asynctor[redis]"`)
```
from asynctor import AsyncClient

redis = AsyncRedis()
await redis.__aenter__()  # 检查redis server是否能ping通

await redis.keys()
await redis.get('a')
expire = 30  # Seconds
await redis.set('key', 'value', expire)

await redis.aclose()  # 关闭redis连接
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
其他fastapi的常用配置
```py
from asynctor.contrib.fastapi import add_timing_middleware, config_access_log
from fastapi import FastAPI

app = FastAPI()
add_timing_middleware(app)  # Response的Headers中带上函数执行时间
config_access_log()  # 日志里显示接口的请求时间和来源IP
```

## 异步测试

安装测试扩展：

```sh
pip install "asynctor[testing]"
```

在 `conftest.py` 中创建 pytest fixture：

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

需要临时工作目录时：

```py
from asynctor.testing import tmp_workdir_fixture

tmp_workdir = tmp_workdir_fixture()

def test_xxx(tmp_workdir):
    # 已经为这个测试函数，单独创建临时目录，并cd到这个目录下
    # 测试完成会自动删除这个临时目录
    assert Path.cwd() != Path(__file__).parent
    assert list(Path.glob('*')) == []
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
没用ExtendSyspath的话，一般会这样写：

1. import了两次，不够简洁
```
import sys

try:
    import conftest
except ImportError:
    sys.path.append('tests')

    import conftest
```
2. import没置顶，代码检查工具如ruff会报错
```
import sys

sys.path.append('tests')
import conftest
```
