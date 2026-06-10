---
icon: lucide/download
---

# 安装

## 基础安装

=== "pip"

    ```sh
    pip install asynctor
    ```

=== "uv"

    ```sh
    uv add asynctor
    ```

=== "pdm"

    ```sh
    pdm add asynctor
    ```

## 扩展依赖

按需安装 extras，避免给项目引入暂时用不到的依赖。

| extra | 安装命令 | 用途 |
| --- | --- | --- |
| `xlsx` | `pip install "asynctor[xlsx]"` | Excel 读写，安装 `pandas` 和 `openpyxl` |
| `xls` | `pip install "asynctor[xls]"` | `xlsx` 的兼容别名 |
| `redis` | `pip install "asynctor[redis]"` | Redis 异步客户端集成 |
| `testing` | `pip install "asynctor[testing]"` | FastAPI/httpx 异步测试辅助 |
| `fastapi` | `pip install "asynctor[fastapi]"` | FastAPI 集成，包含 redis 和 testing |
| `toml` | `pip install "asynctor[toml]"` | Python 3.10 的 TOML 读取支持 |
| `accel` | `pip install "asynctor[accel]"` | 安装 `orjson` 加速 JSON 处理 |
| `all` | `pip install "asynctor[all]"` | 安装全部可选功能 |

也可以一次安装多个扩展：

```sh
pip install "asynctor[xlsx,redis,fastapi]"
```

## 从 GitHub 安装

```sh
uv pip install "asynctor @ git+https://github.com/waketzheng/asynctor"
```

使用 SSH：

```sh
uv pip install "asynctor[redis] @ git+ssh://git@github.com/waketzheng/asynctor.git"
```

## 文档站本地预览

本仓库使用 Zensical 生成文档站。安装或使用 `uvx` 后，在仓库根目录运行：

文档配置文件放在 `mkdocs.yml`，Zensical 可以直接读取。

```sh
uvx zensical serve
```

只构建静态站点：

```sh
uvx zensical build
```
