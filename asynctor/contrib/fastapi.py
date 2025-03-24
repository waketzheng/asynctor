from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.routing import _merge_lifespan_context

from asynctor import AsyncRedis


def register_aioredis(
    app: FastAPI,
) -> None:
    @asynccontextmanager
    async def redis_lifespan(app_instance: FastAPI):
        async with AsyncRedis(app_instance):
            yield

    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = _merge_lifespan_context(redis_lifespan, original_lifespan)


def get_redis_client(request: Request) -> AsyncRedis:
    return AsyncRedis(request)


AioRedis = Annotated[AsyncRedis, Depends(get_redis_client)]
