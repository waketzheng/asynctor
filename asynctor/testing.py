from __future__ import annotations

from collections.abc import Callable, Generator
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import pytest

try:
    from httpx2 import ASGITransport, AsyncClient
except ImportError:
    try:
        from httpx import ASGITransport, AsyncClient  # type:ignore[assignment]
    except ModuleNotFoundError:
        raise RuntimeError(
            "The asynctor.testing module requires the httpx2 package to be installed.\n"
            "You can install this with:\n"
            "    $ pip install httpx2\n"
        ) from None

from .compat import chdir
from .utils import AsyncClientGenerator

if TYPE_CHECKING:
    from types import TracebackType

    from _pytest.config import Config
    from _pytest.fixtures import FixtureFunctionDefinition
    from _pytest.scope import ScopeName
    from asgi_lifespan import LifespanManager
    from asgi_lifespan._types import ASGIApp
    from fastapi import FastAPI


@asynccontextmanager
async def client_manager(
    app: FastAPI,
    base_url: str = "http://test",
    mount_lifespan: bool = True,
    timeout: int | float = 30,
    **kwargs: Any,
) -> AsyncClientGenerator:
    """Async test client

    Usage::

    ```py
    import pytest
    from asynctor.testing import AsyncClient, AsyncClientGenerator, client_manager

    from main import app


    @pytest.fixture(scope='session')
    async def client() -> AsyncClientGenerator:
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
    if mount_lifespan:
        from asgi_lifespan import LifespanManager

        async with (
            LifespanManager(app) as manager,
            _init_client(manager.app, base_url, timeout, **kwargs) as c,
        ):
            yield c
    else:
        async with _init_client(app, base_url, timeout, **kwargs) as c:
            yield c


def _init_client(app: ASGIApp, base_url: str, timeout: int | float, **kwargs: Any) -> AsyncClient:
    return AsyncClient(  # pyright:ignore
        transport=ASGITransport(app),  # ty:ignore[invalid-argument-type]  # pyright:ignore
        timeout=timeout,
        base_url=base_url,
        **kwargs,
    )


class AsyncTestClient(AbstractAsyncContextManager):
    """Async test client for FastAPI

    :param app: a fastapi instance.
    :param mount_lifespan: if True, auto mount lifespan for app.
    :param base_url: scheme and host for the httpx AsyncClient.
    :param kwargs: other kwargs to pass to httpx AsyncClient.

    Usage::

    ... code-block:: python3

        import pytest
        from asynctor.testings import AsyncClient, AsyncTestClient, AsyncClientGenerator

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
        mount_lifespan: bool = True,
        base_url: str = "http://test",
        timeout: int | float = 30,
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
        if self._client is None:
            app = await self._init_app()
            self._client = _init_client(app, self._base_url, self._timeout, **self._kwargs)
        return await self._client.__aenter__()

    async def _init_app(self) -> ASGIApp:
        app: ASGIApp = self._app
        if self._mount_lifespan:
            from asgi_lifespan import LifespanManager

            self._manager = manager = await LifespanManager(app).__aenter__()
            app = manager.app
        return app

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._client:
            await self._client.__aexit__(exc_type, exc_value, traceback)
        if self._manager:
            await self._manager.__aexit__(exc_type, exc_value, traceback)


def async_client_fixture(app: FastAPI, mount_lifespan: bool = True) -> FixtureFunctionDefinition:
    """Create a session-scoped async client fixture for a FastAPI app.

    The returned fixture is named ``client`` and yields an ``httpx.AsyncClient``
    configured with ``AsyncTestClient``.

    :param app: a fastapi instance.
    :param mount_lifespan: if True, auto mount lifespan for app.
    :return: a pytest fixture function named ``client``.

    Usage::

        import pytest
        from asynctor.testing import AsyncClient, async_client_fixture
        from asynctor.testing import anyio_backend_fixture

        from main import app

        anyio_backend = anyio_backend_fixture()
        client = async_client_fixture(app)

        @pytest.mark.anyio
        async def test_api(client: AsyncClient):
            response = await client.get("/")
            assert response.status_code == 200

    """

    @pytest.fixture(scope="session")
    async def client() -> AsyncClientGenerator:
        async with AsyncTestClient(app, mount_lifespan=mount_lifespan) as c:
            yield c

    return client


def anyio_backend_fixture(
    backend: str | Literal["asyncio", "trio", "auto"] = "asyncio",
    scope: ScopeName | Callable[[str, Config], ScopeName] = "session",
) -> FixtureFunctionDefinition:
    """Create a session-scoped anyio backend fixture for pytest.

    The returned fixture is named ``anyio_backend`` and forces pytest-anyio to
    run tests with the ``asyncio`` backend.

    :return: a pytest fixture function named ``anyio_backend``.

    Usage::

        import pytest
        from asynctor.testing import anyio_backend_fixture

        anyio_backend = anyio_backend_fixture()

        @pytest.mark.anyio
        async def test_async():
            ...

    """

    @pytest.fixture(scope=scope)
    def anyio_backend() -> str:
        return backend

    return anyio_backend


def tmp_workdir_fixture() -> FixtureFunctionDefinition:
    """Create a temporary working-directory fixture for pytest.

    It changes the current working directory to pytest's ``tmp_path``
     for the duration of a test, yields that path, and restores the
     previous working directory afterwards.

    :return: a pytest fixture function.

    Usage::

        from asynctor.testing import tmp_workdir_fixture

        tmp_workdir = tmp_workdir_fixture()

        def test_sth(tmp_workdir: Path):
            assert tmp_workdir.is_dir()
            assert list(tmp_workdir.glob('*')) == []

    """

    @pytest.fixture
    def tmp_work_dir(tmp_path: Path) -> Generator[Path]:
        with chdir(tmp_path):
            yield tmp_path

    return tmp_work_dir


chdir_tmp_fixture = tmp_workdir_fixture  # For backward compatible
