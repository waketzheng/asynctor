from __future__ import annotations

import functools
import logging
import os
import platform
import re
import sys
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any, TypeAlias

import uvicorn
from fastapi import Depends, FastAPI, Request
from fastapi.routing import _merge_lifespan_context

from ..client import AsyncRedis
from ..utils import Shell, load_bool


def register_aioredis(
    app: FastAPI,
    check_connection: bool = True,
    **kwargs: Annotated[Any, "Kwargs that will pass to `redis.asyncio.Redis.__init__`"],
) -> None:
    """
    Register redis to fastapi application

    :param app: the fastapi application instance
    :param check_connection: whether check redis server pingable
    :param kwargs: such like: host, port, etc.
    """

    @asynccontextmanager
    async def redis_lifespan(app_instance: FastAPI) -> AsyncGenerator[None]:
        async with AsyncRedis(app_instance, **kwargs):
            yield

    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = _merge_lifespan_context(redis_lifespan, original_lifespan)


async def get_redis_client(request: Request) -> AsyncRedis:
    return AsyncRedis(request)


AioRedis = Annotated[AsyncRedis, Depends(get_redis_client)]
AioRedisDep = AioRedis
AioRedisDep.__doc__ = """Get register redis cli from application.

Example::

    from asynctor.contrib.fastapi import AioRedisDep, register_aioredis
    from fastapi import FastAPI

    app = FastAPI()
    register_aioredis(app)

    @app.get('/')
    async def get_redis_keys(redis: AioRedisDep) -> list[str]:
        keys = await redis.keys()
        return keys

"""


def get_client_ip(request: Request) -> str:
    if x_forwarded_for := request.headers.get("x_forwarded_for"):
        # X-Forwarded-For may includes many IP address, the first one is origin IP
        return x_forwarded_for.split(",")[0]
    elif x_real_ip := request.headers.get("x_real_ip"):
        return x_real_ip
    elif forwarded := request.headers.get("forwarded"):
        # Forwarded: for=192.0.2.60;proto=http;by=203.0.113.43
        parts = forwarded.split(";")
        for part in parts:
            if part.startswith("for="):
                return part[4:]
    if request.client is None:  # pragma: no cover
        # request.client is not None if server started by uvicorn
        # put it here to improve type hints
        return ""
    return request.client.host


async def get_client_host(request: Request) -> str:
    # If the function is non-async and you use it as a dependency, it will run in a thread.
    # https://github.com/kludex/fastapi-tips?tab=readme-ov-file#9-your-dependencies-may-be-running-on-threads
    return get_client_ip(request)


ClientIpDep = Annotated[str, Depends(get_client_host)]
ClientIpDep.__doc__ = """Get real ip of request client.

Usage::
    >>> @app.get('/')
    >>> def index(client_ip: ClientIpDep):
    ...     assert isinstance(client_ip, str)
"""


def config_access_log_to_show_time(log: str = "uvicorn.access") -> None:
    """Config access logging format for uvicorn

    Usage::
        >>> from asynctor.contrib.fastapi import config_access_log_to_show_time
        >>> app = FastAPI()
        >>> config_access_log_to_show_time()
    """
    fmt = "%(asctime)s - %(levelname)s - %(message)s"
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(fmt))
    logging.getLogger(log).addHandler(handler)


PreStartFunc: TypeAlias = Callable[
    [
        Annotated[str, "host"],
        Annotated[int | None, "port"],
        Annotated[bool, "reload"],
        Annotated[dict[str, str] | None, "docs_params"],
    ],
    Any,
]


class RunServer:
    @staticmethod
    def uvicorn_run(app: FastAPI, host: str, port: int | None, reload: bool, **kw) -> None:
        asgi = "__main__:app" if reload else app
        run = functools.partial(uvicorn.run, asgi, host=host, reload=reload, **kw)
        if port:
            run(port=port)
        else:
            run()

    @staticmethod
    def parse_host_port(
        addrport: str | int, verbose: bool, echo: Callable
    ) -> tuple[str | None, int | None]:
        host, port = None, None
        if isinstance(addrport, int) or addrport.isdigit():
            port = int(addrport)
        elif ":" in addrport:
            h, p = addrport.split(":", 1)
            if not h:
                host = "127.0.0.1"
            elif h != "0":
                host = h
            if p.isdigit():
                port = int(p)
        elif verbose:
            echo(f"Ignore argument {addrport = }")
        return host, port

    @staticmethod
    def load_prod_port(config_file: Path, verbose: bool, echo: Callable) -> int:
        import importlib.util

        spec = importlib.util.spec_from_file_location(config_file.stem, config_file)
        if spec is not None and spec.loader is not None:
            gunicorn_config = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(gunicorn_config)
            if p := getattr(gunicorn_config, "PORT", 0):
                if verbose:
                    echo(f"Load `PORT = {p}` from {config_file}")
                return int(p)
            elif (p := getattr(gunicorn_config, "bind", "").split(":")[-1]).isdigit():
                if verbose:
                    echo(f"Load `bind = xxx:{p}` from {config_file}")
                return int(p)
            elif verbose:
                echo(f"{config_file} does not have 'PORT' attribute")
        elif verbose:
            echo(f"Failed to load module from {config_file}")
        return 0

    @staticmethod
    def echo_docs_url(
        app: FastAPI,
        host: str,
        port: int | None,
        docs_params: dict | None = None,
        echo: Callable | None = None,
    ) -> str:
        if host == "0.0.0.0":
            if declared_host := os.getenv("ASYNCTOR_HOST"):
                host = declared_host
            else:
                from asynctor.utils import get_machine_ip

                host = get_machine_ip()
        url = f"http://{host}:{port or 8000}{app.docs_url}"
        if docs_params:
            url += "?" + "&".join(f"{k}={v}" for k, v in docs_params.items())
        tip = "You can view docs at:"
        if echo is None:
            print(f"{tip}\n{url}")
        else:
            echo(tip)
            try:
                echo(url, bold=True)
            except TypeError:
                echo(url)
        return url

    @staticmethod
    def load_port_from_env() -> int | None:
        if p := os.getenv("ASYNCTOR_PORT"):
            try:
                return int(p)
            except ValueError:
                ...
        return None

    @classmethod
    def run(
        cls,
        app: FastAPI,
        addrport: str | None,
        port: int | None,
        host: str,
        reload: bool,
        prod: bool,
        verbose: bool,
        echo: Callable,
        docs_params: dict[str, str] | None = None,
        pre_start: PreStartFunc | None = None,
        open_browser: bool | None = None,
        **kw,
    ) -> None:
        if addrport:
            h, p = cls.parse_host_port(addrport, verbose, echo)
            if h:
                host = h
            if p:
                port = p
        elif prod:
            deployment_dir = Path("deployment")
            for level in range(5):
                if deployment_dir.exists():
                    if (gc := deployment_dir / "gunicorn_config.py").exists():
                        if _port := cls.load_prod_port(gc, verbose, echo):
                            port = _port
                    elif verbose:
                        echo(f"{gc.name} not found in {deployment_dir}")
                    break
                parent = Path.cwd().parent if level == 0 else deployment_dir.parent.parent
                deployment_dir = parent / deployment_dir.name
            else:
                if verbose:
                    echo(f"Deployment dir: {deployment_dir.name!r} not found")
        cls.echo_and_run(app, host, port, reload, docs_params, pre_start, echo, **kw)

    @classmethod
    def echo_and_run(cls, app, host, port, reload, docs_params, pre_start, echo=None, **kw) -> None:
        if not port:
            port = cls.load_port_from_env()
        url = cls.echo_docs_url(app, host, port, docs_params, echo)
        if pre_start is not None:
            try:
                pre_start(host=host, port=port, reload=reload, docs_params=docs_params)
            except TypeError:
                pre_start()
        if kw.pop("open_browser", False) or load_bool("ASYNCTOR_BROWSER"):
            command = "explorer" if platform.system() == "Windows" else "open"
            if host == "0.0.0.0" and (m := re.search(r"://(.*?)[:/]", url)):
                url = url.replace(m.group(1), "127.0.0.1")
            Shell([command, url]).run(verbose=True)
        cls.uvicorn_run(app, host, port, reload, **kw)


def runserver(
    app: FastAPI,
    addrport: str | int | None = None,
    port: int | None = None,
    host: str = "0.0.0.0",
    reload: bool = False,
    verbose: bool = False,
    docs_params: dict[str, str] | None = None,
    pre_start: PreStartFunc | None = None,
    open_browser: bool | None = None,
    **kw,
) -> None:
    kw.update(docs_params=docs_params, pre_start=pre_start, open_browser=open_browser)
    if not (args := sys.argv[1:]):
        return RunServer.echo_and_run(app, host, port, reload, **kw)
    try:
        import typer
    except ImportError:
        raise ImportError(
            "You must install typer or typer-slim to support arguments"
            ", e.g.: pip install typer-slim"
        ) from None

    def cli(
        addrport: Annotated[str | None, "Optional port number, or ipaddr:port"] = typer.Argument(
            default=addrport
        ),
        port: int | None = port,
        host: str = host,
        reload: bool = reload,
        prod: bool = False,
        verbose: bool = verbose,
    ) -> None:
        RunServer.run(app, addrport, port, host, reload, prod, verbose, echo=typer.secho, **kw)

    if (django_style_noreload := "--noreload") in args:
        sys.argv[sys.argv.index(django_style_noreload)] = "--no-reload"

    typer.run(cli)
