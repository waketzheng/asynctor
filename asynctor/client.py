import os
from contextlib import AbstractAsyncContextManager
from typing import TYPE_CHECKING

from redis import asyncio as aioredis

if TYPE_CHECKING:  # pragma: no cover
    from fastapi import FastAPI, Request


# The `RedisClient` class is a subclass of `aioredis.Redis` and `AbstractAsyncContextManager` that
# initializes a Redis client with a host parameter from an environment variable if not provided, and
# implements an asynchronous exit method to close the client.
class RedisClient(aioredis.Redis, AbstractAsyncContextManager):
    def __init__(self, **kw) -> None:
        if "host" not in kw and (host := os.getenv("REDIS_HOST")):
            kw["host"] = host
        super().__init__(**kw)

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
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

    def __new__(
        cls, app: "FastAPI | Request | str | None" = None, check_connection=True, **kw
    ) -> "AsyncRedis":
        if (
            app is not None
            and (app := getattr(app, "app", None))
            and (state := getattr(app, "state", None))
        ):
            # isinstance(app, Request)
            return state.redis
        return super().__new__(cls)

    def __init__(self, app=None, check_connection=True, **kw) -> None:
        if isinstance(app, str):
            kw.setdefault("host", app)
            app = None
        super().__init__(**kw)
        self._check_connection = check_connection
        if app is not None and hasattr(app, "state"):
            # isinstance(app, FastAPI)
            app.state.redis = self

    async def __aenter__(self) -> "AsyncRedis":
        # Check connection when app startup
        if self._check_connection:
            await self.ping()
        return self
