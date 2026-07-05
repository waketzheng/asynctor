---
icon: lucide/list-checks
---

# API 速查

本页按模块列出常用 API。类型签名只保留最常用的参数，完整行为以源码和类型提示为准。

## `asynctor`

顶层章节只列最常用的快捷导入。更细的 API 按来源模块放在后续章节中。

| API | 来源模块 | 说明 |
| --- | --- | --- |
| `AsyncRedis(app=None, check_connection=True, **kwargs)` | `asynctor.client` | Redis 异步客户端，可作为 FastAPI 状态管理器，也可直接使用 |
| `Timer(message, decimal_places=1, verbose=True)` | `asynctor.timing` | 同步或异步代码耗时统计，可作为上下文管理器或装饰器 |
| `run_async(async_func, *args)` | `asynctor.aio` | 从同步代码启动工作线程运行异步函数或协程，并返回结果 |

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

异步执行和同步桥接工具。`run_async` 作为常用顶层入口在 `asynctor` 章节展开。

### `run`

```py
run(func, *args, backend="asyncio", backend_options=None)
```

运行协程对象或异步函数，并返回结果。适合作为脚本、CLI 或同步入口的异步执行封装。

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

并发执行多个协程，返回按输入顺序排列的元组。`limit` 为 `None` 或 `0` 时不限制并发。

### `bulk_gather`

```py
await bulk_gather(coros, batch_size=0, wait_last=False, raises=True)
```

批量执行协程列表或生成器。

| 参数 | 说明 |
| --- | --- |
| `coros` | 协程序列或生成器 |
| `batch_size` | 同时运行的任务数量，`0` 表示不限制 |
| `wait_last` | 是否等待上一批全部完成后再启动下一批 |
| `raises` | 任务失败时是否抛出异常；为 `False` 时失败结果返回 `None` |

### 任务和同步桥接

| API | 说明 |
| --- | --- |
| `map_group(func, todos, results=None)` | 用 anyio task group 批量启动任务，可按传入列表收集结果 |
| `start_tasks(coro, *more)` | 在 anyio task group 中启动一个或多个后台任务，退出上下文时取消这些任务 |
| `wait_for(coro, timeout)` | 为协程设置超时时间，内部使用 anyio 的取消机制 |
| `create_task(coro, task_group, name=None)` | 在已有 anyio task group 中启动单个任务 |
| `async_to_sync(func)` | 把异步函数包装成同步函数 |
| `run_until_complete(async_func)` | 在运行中的 loop 或工作线程中执行异步函数或协程 |

```py
from asynctor.aio import start_tasks, wait_for


async with start_tasks(background()):
    result = await wait_for(fetch(1), timeout=3)
```

## `asynctor.timing`

`timeit` 和 `Timer` 用于统计同步或异步代码耗时。`Timer` 也可从顶层 `asynctor` 导入。

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

`Timer.current_time()` 返回当前 Unix 时间戳，单位为毫秒。

```py
timestamp_ms = Timer.current_time()
assert isinstance(timestamp_ms, int)
```

`Timer.beijing_now()` 返回 `Asia/Shanghai` 时区的 timezone-aware `datetime`。

```py
now = Timer.beijing_now()
assert now.tzinfo is not None
```

## `asynctor.testing`

需要安装：

```sh
pip install "asynctor[testing]"
```

| API | 说明 |
| --- | --- |
| `anyio_backend_fixture()` | 创建名为 `anyio_backend` 的 session 级 pytest fixture，固定使用 `asyncio` 后端 |
| `async_client_fixture(app, mount_lifespan=True)` | 创建名为 `client` 的 session 级异步 HTTP 客户端 fixture |
| `tmp_workdir_fixture()` | 创建名为 `tmp_work_dir` 的 fixture，测试期间切换到 `tmp_path` |
| `chdir_tmp_fixture` | `tmp_workdir_fixture` 的兼容别名 |

## `asynctor.contrib.fastapi`

需要安装：

```sh
pip install "asynctor[fastapi]"
```

| API | 说明 |
| --- | --- |
| `register_aioredis(app, check_connection=True, **kwargs)` | 在 FastAPI lifespan 中创建 Redis 客户端并挂到 `app.state.redis` |
| `AioRedisDep` | FastAPI 依赖类型，从当前请求获取 Redis 客户端 |
| `get_client_ip(request)` | 从代理头或 socket 信息解析客户端 IP |
| `ClientIpDep` | FastAPI 依赖类型，返回真实客户端 IP 字符串 |
| `runserver(app, ...)` | 启动 FastAPI 开发服务，支持 `addrport`、`reload`、`prod` 等参数 |

## `asynctor.client`

需要安装：

```sh
pip install "asynctor[redis]"
```

| API | 说明 |
| --- | --- |
| `RedisClient(**kwargs)` | `redis.asyncio.Redis` 的扩展版本；未传 `host` 时读取 `REDIS_HOST` |
| `AsyncRedis(app=None, check_connection=True, **kwargs)` | 可作为 FastAPI 状态管理器，也可直接作为异步 Redis 客户端使用；常用时可从顶层 `asynctor` 导入 |

## `asynctor.xlsx`

需要安装：

```sh
pip install "asynctor[xlsx]"
```

| API | 返回值 | 说明 |
| --- | --- | --- |
| `read_excel(file, as_str=False, **kwargs)` | `pandas.DataFrame` | 异步读取本地路径、`anyio.Path`、上传文件、bytes 或 `BytesIO` |
| `load_xlsx(file, as_str=False, **kwargs)` | `list[dict]` | 读取 Excel 并转换为字典列表 |
| `pd_read_excel(file, as_str=False, **kwargs)` | `pandas.DataFrame` | 同步封装 `pandas.read_excel` |
| `df_to_datas(df)` | `list[dict]` | 将 DataFrame 转为字典列表 |
| `Excel(filename)` | `Excel` | 文件级读写封装，提供 `read`、`aread`、`write`、`awrite` |

`asynctor.xls` 保留兼容别名，其中 `load_xls` 对应 `load_xlsx`。

## `asynctor.jsons`

`accel` extra 会安装 `orjson`，未安装时回退到标准库 `json`。

```sh
pip install "asynctor[accel]"
```

| API | 说明 |
| --- | --- |
| `json_dumps(obj, default=None, pretty=False)` | 序列化为字符串 |
| `json_dump_bytes(obj, default=None, pretty=False)` | 序列化为 bytes |
| `json_loads(obj)` | 反序列化 JSON |
| `FastJson.dumps(obj, output="bytes", pretty=False)` | 输出 bytes、字符串，或写入 `Path` |
| `FastJson.loads(obj)` | `json_loads` 的静态方法别名 |

## `asynctor.utils`

| API | 说明 |
| --- | --- |
| `client_manager(app, base_url="http://test", mount_lifespan=True, **kwargs)` | FastAPI/ASGI 异步测试客户端 context manager |
| `AsyncTestClient(app, mount_lifespan=True, base_url="http://test", **kwargs)` | FastAPI 异步测试客户端封装 |
| `AsyncClientGenerator` | `AsyncClient` 异步生成器类型别名 |
| `AttrDict(data)` | 让字典中的字符串键支持属性访问，嵌套字典会递归转换 |
| `local_dict(data, *keys)` | 从已有字典中按 key 取值组成新字典 |
| `get_machine_ip()` | 获取当前机器 IP，失败时返回 `127.0.0.1` |
| `cache_attr(func)` | 把类方法结果缓存到类属性 |
| `Shell(command)` | 基于 `subprocess` 的命令执行封装 |
| `load_bool(key)` | 读取环境变量，并把常见的 false-like 值解析为 `False` |
| `ExtendSyspath(path, insert=0)` | 在 context manager 中临时把目录加入 `sys.path` |

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

| API | 说明 |
| --- | --- |
| `ThreadGroup(max_workers=0, timeout=None)` | 管理一组线程或线程池任务，并在退出上下文时收集结果 |

```py
from asynctor.tasks import ThreadGroup


def double(value: int) -> int:
    return value * 2


with ThreadGroup(max_workers=2) as tg:
    for value in range(3):
        tg.soonify(double)(value)

assert tg.results == [0, 2, 4]
```
