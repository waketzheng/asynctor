import pytest


@pytest.mark.anyio
async def test_index(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"state": "RedisClient"}


@pytest.mark.anyio
async def test_index_no_lifespan(client_no_lifespan):
    response = await client_no_lifespan.get("/")
    assert response.status_code == 200
    assert response.json() == {"state": None}
