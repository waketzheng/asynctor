from typing import AsyncGenerator

import httpx
import pytest
from main import app, app2

from asynctor.utils import client_manager


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    async with client_manager(app) as c:
        yield c


@pytest.fixture(scope="session")
async def client_no_lifespan() -> AsyncGenerator[httpx.AsyncClient, None]:
    async with client_manager(app2, mount_lifespan=False) as c:
        yield c
