import anyio
import pytest

from asynctor.testing import AsyncClient


@pytest.mark.anyio
async def test_redis_keys(client: AsyncClient):
    response = await client.get("/redis/keys")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    process_time = response.headers.get("X-Process-Time")
    assert process_time is not None
    assert process_time.endswith(" ms")
    assert process_time.replace(" ms", "").isdigit()


@pytest.mark.anyio
async def test_redis_set_get(client: AsyncClient):
    response = await client.post("/redis/set", json={"key": "foo", "value": "sth"})
    assert response.status_code == 200
    assert response.json() == {"msg": "OK"}
    response = await client.get("/redis/get", params={"key": "foo"})
    assert response.status_code == 200
    assert response.json() == {"foo": "sth"}
    response = await client.post("/redis/set", json={"key": "foo", "value": "sth", "expire": 10})
    assert response.status_code == 200
    assert response.json() == {"msg": "OK"}
    response = await client.get("/redis/get", params={"key": "foo"})
    assert response.status_code == 200
    assert response.json() == {"foo": "sth"}
    response = await client.post("/redis/set", json={"key": "foo", "value": "sth", "expire": 1})
    assert response.status_code == 200
    assert response.json() == {"msg": "OK"}
    await anyio.sleep(1.01)
    response = await client.get("/redis/get", params={"key": "foo"})
    assert response.status_code == 200
    assert response.json() == {"foo": None}
