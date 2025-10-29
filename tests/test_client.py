from __future__ import annotations

import os

import pytest
from redis.asyncio import Redis

from asynctor import AsyncRedis
from asynctor.testing import async_client_fixture

from .main import app

client = async_client_fixture(app)


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
    cached = await AsyncRedis().get("b")
    assert cached == b"1"


def test_redis_host_port():
    remote_ip = "192.168.0.2"
    redis = AsyncRedis(remote_ip)
    assert isinstance(redis, Redis)
    assert redis.connection_pool.connection_kwargs["host"] == remote_ip

    redis = AsyncRedis(host=remote_ip)
    assert redis.connection_pool.connection_kwargs["host"] == remote_ip

    redis = AsyncRedis("localhost", host=remote_ip)
    assert redis.connection_pool.connection_kwargs["host"] == remote_ip

    custom_port = 8888
    redis = AsyncRedis(port=custom_port)
    assert redis.connection_pool.connection_kwargs["port"] == custom_port


@pytest.mark.anyio
async def test_redis_not_installed(monkeypatch):
    import sys

    monkeypatch.setitem(sys.modules, "redis", None)
    monkeypatch.delattr(Redis, "aclose")

    with pytest.raises(RuntimeError, match=r"pip install redis"):
        async with AsyncRedis():
            pass
    with pytest.raises(RuntimeError, match=r'pip install "asynctor\[redis\]"'):
        async with AsyncRedis(check_connection=False):
            pass
