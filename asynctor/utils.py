from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncGenerator, cast

if TYPE_CHECKING:
    from fastapi import FastAPI
    from httpx import AsyncClient
    from httpx._transports.asgi import _ASGIApp


@asynccontextmanager
async def client_manager(
    app: "FastAPI", base_url="http://test", mount_lifespan=True, **kwargs
) -> AsyncGenerator["AsyncClient", None]:
    """Async test client

    Usage::

    ```py
    from typing import AsyncGenerator

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
            transport = httpx.ASGITransport(cast("_ASGIApp", manager.app))
            async with httpx.AsyncClient(
                transport=transport, base_url=base_url, **kwargs
            ) as c:
                yield c
    else:
        # TODO: remove `cast("_ASGIApp"` if "httpx>0.27.0" released
        transport = httpx.ASGITransport(cast("_ASGIApp", app))
        kwargs.update(transport=transport, base_url=base_url)
        async with httpx.AsyncClient(**kwargs) as c:
            yield c


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


def _test() -> None:  # pragma: no cover
    import doctest

    doctest.testmod(verbose=True)


if __name__ == "__main__":
    _test()
