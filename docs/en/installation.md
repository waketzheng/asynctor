---
icon: lucide/download
---

# Installation

## Base Package

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

## Optional Extras

Install extras only when you need the related feature.

| extra | Command | Purpose |
| --- | --- | --- |
| `xlsx` | `pip install "asynctor[xlsx]"` | Excel read/write support with `pandas` and `openpyxl` |
| `xls` | `pip install "asynctor[xls]"` | Compatibility alias for `xlsx` |
| `redis` | `pip install "asynctor[redis]"` | Async Redis client integration |
| `testing` | `pip install "asynctor[testing]"` | FastAPI/httpx async testing helpers |
| `fastapi` | `pip install "asynctor[fastapi]"` | FastAPI integration, including redis and testing extras |
| `toml` | `pip install "asynctor[toml]"` | TOML support for Python 3.10 |
| `accel` | `pip install "asynctor[accel]"` | `orjson` acceleration for JSON handling |
| `all` | `pip install "asynctor[all]"` | All optional features |

You can install multiple extras at once:

```sh
pip install "asynctor[xlsx,redis,fastapi]"
```

## Install From GitHub

```sh
uv pip install "asynctor @ git+https://github.com/waketzheng/asynctor"
```

With SSH:

```sh
uv pip install "asynctor[redis] @ git+ssh://git@github.com/waketzheng/asynctor.git"
```

## Preview This Documentation

This repository uses Zensical to build the documentation site. The configuration
is stored in `mkdocs.yml`, which Zensical can read directly. After installing
Zensical or using `uvx`, run this from the repository root:

```sh
uvx zensical serve
```

To build the static site:

```sh
uvx zensical build
```
