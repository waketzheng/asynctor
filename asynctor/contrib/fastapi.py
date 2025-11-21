from __future__ import annotations

import logging
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated, Any

import uvicorn
from fastapi import Depends, FastAPI, Request
from fastapi.routing import _merge_lifespan_context

from ..client import AsyncRedis


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


def runserver(
    app: FastAPI,
    addrport: str | int | None = None,
    port: int | None = None,
    host: str = "0.0.0.0",
    reload: bool = False,
) -> None:
    from typing import Union

    if not (args := sys.argv[1:]):
        return uvicorn.run("__main__:app" if reload else app)

    def parse_host_port(addrport: str | int, verbose=True) -> tuple[str | None, int | None]:
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
            print(f"Ignore argument {addrport = }")
        return host, port

    def cli(
        addrport: Annotated[
            Union[str, int, None],  # NOQA:UP007
            "Optional port number, or ipaddr:port",
        ] = None,
        port: Union[int, None] = None,  # NOQA:UP007
        host: str = "0.0.0.0",
        reload: bool = False,
    ) -> None:
        if addrport:
            h, p = parse_host_port(addrport)
            if h:
                host = h
            if p:
                port = p
        asgi = "__main__:app" if reload else app
        if port:
            uvicorn.run(asgi, host=host, port=port)
        else:
            uvicorn.run(asgi, host=host)

    try:
        import typer
    except ImportError:
        noreload = "--noreload" in args or "--no-reload" in args
        cli(addrport, port, host, reload=not noreload)
    else:
        typer.run(cli)
