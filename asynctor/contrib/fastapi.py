from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated, Any

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


ClientIpDep = Annotated[str, Depends(get_client_ip)]
ClientIpDep.__doc__ = """Get real ip of request client.

Usage::
    >>> @app.get('/')
    >>> def index(client_ip: ClientIpDep):
    ...     assert isinstance(client_ip, str)
"""
