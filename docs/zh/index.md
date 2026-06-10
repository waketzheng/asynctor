---
icon: lucide/book-open
---

# asynctor 概览

asynctor 面向需要在 Python 项目中快速处理异步执行、FastAPI 测试和 Excel 数据读写的开发者。它以 anyio 为基础，保留接近 `asyncio` 的使用方式，同时提供更方便的批量执行、同步入口、测试夹具和集成工具。

## 适用场景

- 需要限制并发数量并收集异步任务结果。
- 需要在同步函数或脚本中调用异步函数。
- 需要给同步或异步代码做简单耗时统计。
- 需要为 FastAPI 应用编写异步测试。
- 需要在 FastAPI 中管理 Redis 客户端生命周期。
- 需要异步读取或写入 Excel 文件。

## Python 版本

asynctor 要求 Python 3.10 或更新版本。

## 常用入口

| 模块 | 常用对象 | 用途 |
| --- | --- | --- |
| `asynctor` | `AsyncRedis`、`Timer`、`run_async` | 最常用的顶层快捷入口 |
| `asynctor.aio` | `gather`、`bulk_gather`、`run`、`map_group`、`start_tasks`、`wait_for` | 异步执行、同步桥接和任务辅助 |
| `asynctor.timing` | `timeit`、`Timer` | 耗时统计 |
| `asynctor.client` | `RedisClient`、`AsyncRedis` | Redis 异步客户端 |
| `asynctor.testing` | `anyio_backend_fixture`、`async_client_fixture`、`tmp_workdir_fixture` | pytest 夹具 |
| `asynctor.contrib.fastapi` | `register_aioredis`、`AioRedisDep`、`ClientIpDep`、`runserver` | FastAPI 集成 |
| `asynctor.xlsx` | `read_excel`、`load_xlsx`、`Excel` | Excel 读写 |
| `asynctor.jsons` | `json_dumps`、`json_dump_bytes`、`json_loads`、`FastJson` | JSON 序列化辅助函数 |
| `asynctor.utils` | `AttrDict`、`AsyncTestClient`、`load_bool`、`ExtendSyspath`、`Shell` | 测试客户端、环境变量和路径辅助工具 |

## 快速示例

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

## 下一步

- 阅读[安装](installation.md)选择基础包或扩展依赖。
- 阅读[使用指南](usage.md)查看异步、FastAPI、测试和 Excel 示例。
