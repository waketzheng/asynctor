---
icon: lucide/languages
---

# asynctor 文档

asynctor 是一个 Python 工具包，提供基于 anyio 的异步执行辅助函数、FastAPI 测试工具、Redis 依赖集成以及 Excel 读写工具。

## 选择语言

- [中文文档](zh/)
- [英文文档](en/)

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

- 用 `gather`、`bulk_gather` 和 `run` 管理异步执行。
- 用 `run_async` 从同步上下文运行异步函数。
- 用 `timeit` 和 `Timer` 统计同步或异步代码耗时。
- 为 FastAPI 提供 Redis 依赖、测试客户端和开发服务器辅助函数。
- 用 `load_xlsx`、`read_excel` 和 `Excel` 读写 Excel 文件。
- 用 `json_dumps`、`json_dump_bytes` 和 `FastJson` 处理 JSON。
- 用 `load_bool` 和 `ExtendSyspath` 处理环境变量和导入路径。
