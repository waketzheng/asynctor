import pytest
from main import app, app2

from asynctor import AsyncClientGenerator, AsyncTestClient


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def client() -> AsyncClientGenerator:
    async with AsyncTestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
async def client_no_lifespan() -> AsyncClientGenerator:
    async with AsyncTestClient(app2, mount_lifespan=False) as c:
        yield c
