import pytest
from main import app

from asynctor import AsyncClientGenerator, AsyncTestClient


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def client() -> AsyncClientGenerator:
    async with AsyncTestClient(app) as c:
        yield c
