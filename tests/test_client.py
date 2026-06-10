from __future__ import annotations

import builtins
import importlib.util
import os
import re
import sys

import pytest
from fastapi import FastAPI, Request
from redis.asyncio import Redis

import asynctor.client as client_mod
from asynctor import AsyncRedis
from asynctor.contrib import fastapi as fastapi_utils
from asynctor.testing import async_client_fixture
from asynctor.utils import AsyncTestClient

from .main import app

client = async_client_fixture(app)


def _load_client_without_redis(monkeypatch):
    real_import = builtins.__import__

    def import_without_redis(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "redis" or name.startswith("redis."):
            raise ImportError
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", import_without_redis)
    spec = importlib.util.spec_from_file_location(
        "asynctor._client_without_redis", client_mod.__file__
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def test_redis_reuses_fastapi_state_instance():
    app = FastAPI()
    redis = AsyncRedis(app, check_connection=False, host="192.168.0.2")

    assert app.state.redis is redis
    assert AsyncRedis(app, host="127.0.0.1") is redis
    assert redis.connection_pool.connection_kwargs["host"] == "192.168.0.2"


@pytest.mark.anyio
async def test_register_aioredis_passes_check_connection(monkeypatch):
    calls = []

    class FakeRedis:
        def __init__(self, app, check_connection=True, **kwargs):
            calls.append((app, check_connection, kwargs))

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

    monkeypatch.setattr(fastapi_utils, "AsyncRedis", FakeRedis)
    app = FastAPI()
    fastapi_utils.register_aioredis(app, check_connection=False, host="redis")

    async with AsyncTestClient(app) as client:
        response = await client.get("/missing")

    assert response.status_code == 404
    assert len(calls) == 1
    assert calls[0][1:] == (False, {"host": "redis"})


@pytest.mark.anyio
async def test_register_aioredis_preserves_host_for_dependency():
    app = FastAPI()
    fastapi_utils.register_aioredis(app, check_connection=False, host="redis", port=6380)

    def _get_redis_config(redis: AsyncRedis) -> dict[str, str | int]:
        connection_kwargs = redis.connection_pool.connection_kwargs
        return {"host": connection_kwargs["host"], "port": connection_kwargs["port"]}

    @app.get("/redis-config")
    async def redis_config(redis: fastapi_utils.AioRedisDep) -> dict[str, str | int]:
        return _get_redis_config(redis)

    @app.get("/redis-check")
    async def redis_check(request: Request) -> dict[str, str | int]:
        redis = AsyncRedis(request)
        return _get_redis_config(redis)

    async with AsyncTestClient(app) as client:
        response = await client.get("/redis-config")
        response2 = await client.get("/redis-check")

    assert response.status_code == 200
    assert response.json() == {"host": "redis", "port": 6380}
    assert app.state.redis.connection_pool.connection_kwargs["host"] == "redis"
    assert response2.status_code == 200
    assert response2.json() == {"host": "redis", "port": 6380}


@pytest.mark.anyio
async def test_redis_not_installed(monkeypatch):
    monkeypatch.setitem(sys.modules, "redis", None)
    monkeypatch.delattr(Redis, "aclose")

    with pytest.raises(RuntimeError, match=r"pip install redis"):
        async with AsyncRedis():
            pass
    with pytest.raises(RuntimeError, match=r'pip install "asynctor\[redis\]"'):
        async with AsyncRedis(check_connection=False):
            pass


@pytest.mark.anyio
async def test_redis_not_installed_accepts_connection_kwargs(monkeypatch):
    module = _load_client_without_redis(monkeypatch)
    app = FastAPI()
    with pytest.raises(RuntimeError, match=r'pip install "asynctor\[redis\]"'):
        async with module.AsyncRedis(app, check_connection=False, host="redis"):
            pass


@pytest.mark.anyio
async def test_register_aioredis_not_installed_accepts_connection_kwargs(monkeypatch):
    module = _load_client_without_redis(monkeypatch)
    monkeypatch.setattr(fastapi_utils, "AsyncRedis", module.AsyncRedis)

    app = FastAPI()
    fastapi_utils.register_aioredis(app, check_connection=False, host="redis")

    with pytest.raises(RuntimeError, match=re.escape('pip install "asynctor[redis]"')):
        async with AsyncTestClient(app):
            pass
