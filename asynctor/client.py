from __future__ import annotations

import os
from typing import TYPE_CHECKING, Annotated, Any, cast

try:
    from redis.asyncio import Redis
except ImportError:  # pragma: no cover
    from contextlib import AbstractAsyncContextManager

    class Redis(AbstractAsyncContextManager):  # type:ignore[no-redef]
        def __aexit__(self, *args, **kw): ...


if TYPE_CHECKING:
    from fastapi import FastAPI, Request

    from .compat import Self


def ensure_redis_is_installed() -> None:
    try:
        import redis  # NOQA:F401
    except ImportError:
        raise RuntimeError(
            "AsyncRedis requires redis to be installed. \n"
            "You can install it with: \n\n"
            "    pip install redis\n"
            "Or:\n"
            '    pip install "asynctor[redis]"\n'
        ) from None


class RedisClient(Redis):
    def __init__(self, **kw: Annotated[Any, "Same as redis.asyncio.Redis"]) -> None:
        """Expand `redis.asyncio.Redis` to auto load REDIS_HOST from os environ,
        if host parameter not explicitly set.

        Example::
            ```
            import os
            os.environ['REDIS_HOST'] = '192.168.0.2'
            r = RedisClient()
            assert r.connection_pool.connection_kwargs['host'] == '192.168.0.2'

            r = RedisClient(host='127.0.0.1')
            assert r.connection_pool.connection_kwargs['host'] == '127.0.0.1'
            ```
        """
        if "host" not in kw and (host := os.getenv("REDIS_HOST")):
            kw["host"] = host
        super().__init__(**kw)


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
        cls,
        app: FastAPI | Request | Annotated[str, "redis host, e.g.: 127.0.0.1"] | None = None,
        check_connection: bool = True,
        **kw: Annotated[Any, "kwargs that pass to the Redis class"],
    ) -> AsyncRedis:
        """Create a new redis instance or get the redis instance from fastapi state

        :param app: fastapi/fastapi.Request/redis host, if None get redis host from os environ
        :param check_connection: whether check redis host pingable when __aenter__
        :param kw: kwargs that pass to the Redis class when initial
        """
        if (
            app is not None
            and (app := getattr(app, "app", None))
            and (state := getattr(app, "state", None))
        ):
            # app isinstance of fastapi.FastAPI or fastapi.Request
            return cast(AsyncRedis, state.redis)
        return super().__new__(cls)

    def __init__(
        self,
        app: FastAPI | Request | Annotated[str, "redis host, e.g.: 127.0.0.1"] | None = None,
        check_connection: bool = True,
        **kw: Annotated[Any, "kwargs that pass to the Redis class"],
    ) -> None:
        """Create a new redis instance, and then mount to the state if app is a fastapi application

        :param app: fastapi/fastapi.Request/redis host, if None get redis host from os environ
        :param check_connection: whether check redis host pingable when __aenter__
        :param kw: kwargs that pass to the Redis class when initial
        """
        if isinstance(app, str):
            kw.setdefault("host", app)
            app = None
        super().__init__(**kw)
        self._check_connection = check_connection
        if app is not None and hasattr(app, "state"):
            # isinstance(app, FastAPI)
            app.state.redis = self

    async def __aenter__(self) -> Self:
        if not hasattr(self, "aclose"):
            ensure_redis_is_installed()
        # Check connection when app startup
        if self._check_connection:
            await self.ping()
        return self
