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
    """Async test client for FastAPI as session fixture

    :param app: a fastapi instance.
    :param mount_lifespan: if True, auto mount lifespan for app.

    Usage::

    ... code-block:: python3

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
        async with AsyncTestClient(app) as c:
            yield c

    return client


def anyio_backend_fixture() -> FixtureFunctionDefinition:
    @pytest.fixture(scope="session")
    def anyio_backend() -> str:
        return "asyncio"

    return anyio_backend


def tmp_workdir_fixture() -> FixtureFunctionDefinition:
    @pytest.fixture
    def tmp_work_dir(tmp_path: Path) -> Generator[Path]:
        with chdir(tmp_path):
            yield tmp_path

    return tmp_work_dir


chdir_tmp_fixture = tmp_workdir_fixture  # For backward compatible
