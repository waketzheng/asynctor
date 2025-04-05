from __future__ import annotations

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
    async def redis_lifespan(app_instance: FastAPI):
        async with AsyncRedis(app_instance, **kwargs):
            yield

    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = _merge_lifespan_context(redis_lifespan, original_lifespan)


async def get_redis_client(request: Request) -> AsyncRedis:
    return AsyncRedis(request)


AioRedis = Annotated[AsyncRedis, Depends(get_redis_client)]
