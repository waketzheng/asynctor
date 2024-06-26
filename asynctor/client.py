import os
from contextlib import AbstractAsyncContextManager
from typing import TYPE_CHECKING

from redis import asyncio as aioredis

if TYPE_CHECKING:  # pragma: no cover
    from fastapi import FastAPI, Request


class RedisClient(aioredis.Redis, AbstractAsyncContextManager):
    def __init__(self, **kw) -> None:
        if "host" not in kw and (host := os.getenv("REDIS_HOST")):
            kw["host"] = host
        super().__init__(**kw)

    async def __aexit__(self, *args, **kw):
        await self.aclose()  # type:ignore[attr-defined]


class AsyncRedis(RedisClient):
    """Async redis client for FastAPI

    Usage::
        >>> from contextlib import asynccontextmanager
        >>> from fastapi import FastAPI, Request
        >>> @asynccontextmanager
        ... async def lifespan(fastapi_app: FastAPI):
        ...     async with AsyncRedis(fastapi_app):
        ...         yield
        ...
        >>> app = FastAPI(lifespan=lifespan)
        >>> @app.get('/keys')
        ... async def show_redis_keys(request: Request) -> list[str]:
        ...     redis: AsyncRedis = AsyncRedis(request)
        ...     return await redis.keys()
        ...
        >>> async def use_outside_fastapi():
        ...     async with AsyncRedis(host='localhost') as redis:
        ...         keys: list[str] = await redis.keys()
        ...
    """

    def __new__(cls, app: "FastAPI | Request | None" = None, **kw) -> "AsyncRedis":
        if (_app := getattr(app, "app", None)) and (
            state := getattr(_app, "state", None)
        ):
            # isinstance(app, Request)
            return state.redis
        return super().__new__(cls, **kw)

    def __init__(self, app=None, **kw) -> None:
        super().__init__(**kw)
        if app is not None and hasattr(app, "state"):
            # isinstance(app, FastAPI)
            app.state.redis = self

    async def __aenter__(self) -> "AsyncRedis":
        # Check connection when app startup
        await self.ping()
        return self
