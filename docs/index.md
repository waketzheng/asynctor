---
icon: lucide/languages
---

# asynctor 文档

asynctor 是一个 Python 工具包，主要是提供一些异步工具类和函数，以及少量的后端开发常用的简单的同步函数。包含类基于 anyio 的常见asyncio异步函数、Timer类用于计时和简化时区转换、FastAPI 测试工具、Redis异步依赖集成以及 Excel 读写工具等。

## 选择语言

- [中文文档](zh/)
- [English](en/)

## 快速安装

=== "pip"

    ```sh
    pip install asynctor
    ```

=== "uv"

    ```sh
    uv add asynctor
    ```

=== "扩展依赖"

    ```sh
    pip install "asynctor[xlsx,redis,fastapi,testing]"
    ```

## 核心能力

- 用 `gather`、`run_async` 和 `run` 管理异步执行。
- 用 `timeit` 和 `Timer` 统计同步或异步代码耗时。
- 为 FastAPI 提供 AioRedisDep/ClientIpDep 等依赖、`register_aioredis`/`runserver`/`config_access_log`/`add_timing_middleware`等常用函数。
- 用 `load_xlsx`、`read_excel` 和 `Excel` 读写 Excel 文件。
- 用 `json_dumps`、`json_dump_bytes` 和 `FastJson` 处理 JSON。
- 用 `load_bool` 和 `ExtendSyspath` 处理环境变量和导入路径。
