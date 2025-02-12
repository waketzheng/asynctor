from __future__ import annotations

import functools
import socket
from collections.abc import AsyncGenerator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from asgi_lifespan import LifespanManager
    from asgi_lifespan._types import ASGIApp
    from fastapi import FastAPI
    from httpx import AsyncClient

T = TypeVar("T")
AsyncClientGenerator = AsyncGenerator["AsyncClient", None]


@asynccontextmanager
async def client_manager(
    app: FastAPI, base_url="http://test", mount_lifespan=True, timeout=30, **kwargs
) -> AsyncClientGenerator:
    """Async test client

    Usage::

    ```py
    from collections.abc import AsyncGenerator

    import pytest
    from asynctor.utils import client_manager
    from httpx import AsyncClient

    from main import app


    @pytest.fixture(scope='session')
    async def client() -> AsyncGenerator[AsyncClient, None]:
        async with client_manager(app) as c:
            yield c


    @pytest.fixture(scope="session")
    def anyio_backend():
        return "asyncio"


    @pytest.mark.anyio
    async def test_api(client: AsyncClient):
        response = await client.get("/")
        assert response.status_code == 200
    ```
    """
    import httpx

    if mount_lifespan:
        from asgi_lifespan import LifespanManager

        async with LifespanManager(app) as manager:
            transport = httpx.ASGITransport(manager.app)
            async with httpx.AsyncClient(
                timeout=timeout, transport=transport, base_url=base_url, **kwargs
            ) as c:
                yield c
    else:
        transport = httpx.ASGITransport(app)
        kwargs.update(transport=transport, base_url=base_url)
        async with httpx.AsyncClient(timeout=timeout, **kwargs) as c:
            yield c


class AsyncTestClient(AbstractAsyncContextManager):
    """Async test client for FastAPI

    :param app: a fastapi instance.
    :param mount_lifespan: if True, auto mount lifespan for app.
    :param base_url: scheme and host for the httpx AsyncClient.
    :param kwargs: other kwargs to pass to httpx AsyncClient.

    Usage::

    ... code-block:: python3

        import pytest
        from asynctor import AsyncTestClient, AsyncClientGenerator
        from httpx import AsyncClient

        from main import app

        @pytest.fixture(scope='session')
        async def client() -> AsyncClientGenerator:
            async with AsyncTestClient(app) as c:
                yield c

        @pytest.fixture(scope="session")
        def anyio_backend():
            return "asyncio"

        @pytest.mark.anyio
        async def test_api(client: AsyncClient):
            response = await client.get("/")
            assert response.status_code == 200

    """

    def __init__(
        self,
        app: FastAPI,
        mount_lifespan=True,
        base_url="http://test",
        timeout=30,
        **kwargs,
    ) -> None:
        self._app = app
        self._mount_lifespan = mount_lifespan
        self._manager: LifespanManager | None = None
        self._client: AsyncClient | None = None
        self._base_url = base_url
        self._timeout = timeout
        self._kwargs = kwargs

    async def __aenter__(self) -> AsyncClient:
        from httpx import ASGITransport, AsyncClient

        app: ASGIApp = self._app
        if self._mount_lifespan:
            from asgi_lifespan import LifespanManager

            self._manager = manager = await LifespanManager(app).__aenter__()
            app = manager.app
        self._client = client = await AsyncClient(
            transport=ASGITransport(app),
            base_url=self._base_url,
            timeout=self._timeout,
            **self._kwargs,
        ).__aenter__()
        return client

    async def __aexit__(self, *args, **kw) -> None:
        if self._client:
            await self._client.__aexit__(*args, **kw)
        if self._manager:
            await self._manager.__aexit__(*args, **kw)


class AttrDict(dict):
    """Support get dict value by attribution

    Usage::
        >>> d = AttrDict({'a': 1, 'b': {'c': 2, 'd': {'e': 3}}})
        >>> d.a == d['a'] == 1
        True
        >>> d.b.c == d['b']['c'] == 2
        True
        >>> d.b.d == d['b']['d'] == {'e': 3}
        True
        >>> d.b.d.e == d['b']['d']['e'] == 3
        True
        >>> dd = AttrDict({'keys': 2}, items=1)
        >>> list(dd.items()) == [('keys', 2), ('items', 1)]
        True
        >>> dd['items'] == 1
        True
        >>> list(dd.keys()) == ['keys', 'items']
        True
        >>> dd['keys'] == 2
        True
        >>> d3 = AttrDict({b'a': 1})
        >>> d3[b'a'] == 1 and getattr(d3, 'a', None) is None
        True
    """

    def __init__(self, *args, **kw) -> None:
        super().__init__(*args, **kw)
        exclude = set(dir(self)) | set(self.__dict__)
        for k, v in self.items():
            if not isinstance(k, str) or k in exclude:
                continue
            if isinstance(v, dict):
                v = self.__class__(v)
            self.__dict__.setdefault(k, v)

    def __str__(self) -> str:
        return super().__repr__()

    def __repr__(self) -> str:
        return self.__class__.__name__ + "(" + super().__repr__() + ")"


def get_machine_ip() -> str:
    r"""Get IP of current machine by socket, if failed, return '127.0.0.1'

    Usage::
        >>> import re
        >>> my_ip = get_machine_ip()
        >>> bool(re.search(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', my_ip))
        True
        >>> inets = my_ip.split('.')
        >>> len(inets) == 4
        True
        >>> sum(map(lambda x: 0 <= int(x) <= 255, inets))
        4
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(0)
        try:
            # doesn't even have to be reachable
            s.connect(("10.254.254.254", 1))
            return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"


def cache_attr(func: Callable[..., T]) -> Callable[..., T]:
    """Cache result to class attribute

    Usage::
    ```py
    class A:
        @classmethod
        @cache_attr
        def do_sth(cls):
            ...

    result = A.do_sth()
    ```

    Example::
        >>> from datetime import datetime
        >>> class A:
        ...     @classmethod
        ...     @cache_attr
        ...     def now(cls) -> datetime:
        ...         return datetime.now()
        >>> now_a = A.now()
        >>> now = datetime.now()
        >>> now_a == A.now()
        True
        >>> A.now() <= now
        True

    """

    @functools.wraps(func)
    def run(cls) -> T:
        key = "-cache-" + func.__name__
        if hasattr(cls, key):
            return getattr(cls, key)
        res = func(cls)
        setattr(cls, key, res)
        return res

    return run


def _test() -> None:  # pragma: no cover
    import doctest

    doctest.testmod(verbose=True)


if __name__ == "__main__":
    _test()
