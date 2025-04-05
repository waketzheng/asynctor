import anyio
import pytest


@pytest.mark.anyio
async def test_users(client):
    response = await client.get("/users")
    assert response.status_code == 200
    assert response.json() == [{"id": 1, "name": "John"}]


@pytest.mark.anyio
async def test_redis_keys(client):
    response = await client.get("/redis/keys")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.anyio
async def test_redis_set_get(client):
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
