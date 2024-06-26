import os

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from asynctor import AsyncRedis

from .main import app


@pytest.fixture(scope="session")
async def client():
    async with LifespanManager(app) as manager:
        transport = ASGITransport(app=manager.app)  # type:ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


@pytest.mark.anyio
async def test_apis(client):
    path = "/"
    r = await client.get(path)
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    path = "/redis"
    r = await client.get(path, params={"key": "a"})
    assert r.status_code == 200
    v = await AsyncRedis().get("a")
    assert r.json().get("a") == (v and v.decode()), r.text
    payload = {"key": "b", "value": "1"}
    r = await client.post(path, json=payload)
    assert r.status_code == 200, r.text
    assert r.json()["b"] == "1"
    os.environ["REDIS_HOST"] = "localhost"
    await AsyncRedis().get("b") == b"1"
