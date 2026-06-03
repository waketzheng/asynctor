from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from .compat import chdir
from .utils import AsyncClientGenerator, AsyncTestClient

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureFunctionDefinition
    from fastapi import FastAPI


def async_client_fixture(app: FastAPI, mount_lifespan: bool = True) -> FixtureFunctionDefinition:
    """Create a session-scoped async client fixture for a FastAPI app.

    The returned fixture is named ``client`` and yields an ``httpx.AsyncClient``
    configured with ``AsyncTestClient``.

    :param app: a fastapi instance.
    :param mount_lifespan: if True, auto mount lifespan for app.
    :return: a pytest fixture function named ``client``.

    Usage::

        import pytest
        from asynctor.testing import async_client_fixture
        from httpx import AsyncClient

        from main import app

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


def anyio_backend_fixture() -> FixtureFunctionDefinition:
    """Create a session-scoped anyio backend fixture for pytest.

    The returned fixture is named ``anyio_backend`` and forces pytest-anyio to
    run tests with the ``asyncio`` backend.

    :return: a pytest fixture function named ``anyio_backend``.

    Usage::

        from asynctor.testing import anyio_backend_fixture

        anyio_backend = anyio_backend_fixture()

    """

    @pytest.fixture(scope="session")
    def anyio_backend() -> str:
        return "asyncio"

    return anyio_backend


def tmp_workdir_fixture() -> FixtureFunctionDefinition:
    """Create a temporary working-directory fixture for pytest.

    The returned fixture is named ``tmp_work_dir``. It changes the current
    working directory to pytest's ``tmp_path`` for the duration of a test,
    yields that path, and restores the previous working directory afterwards.

    :return: a pytest fixture function named ``tmp_work_dir``.

    Usage::

        from asynctor.testing import tmp_workdir_fixture

        tmp_work_dir = tmp_workdir_fixture()

    """

    @pytest.fixture
    def tmp_work_dir(tmp_path: Path) -> Generator[Path]:
        with chdir(tmp_path):
            yield tmp_path

    return tmp_work_dir


chdir_tmp_fixture = tmp_workdir_fixture  # For backward compatible
