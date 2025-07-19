from __future__ import annotations

import pytest

from asynctor import AsyncTestClient
from asynctor.utils import get_machine_ip

from .main import app


@pytest.fixture(scope="session")
async def client():
    async with AsyncTestClient(app) as c:
        yield c


@pytest.mark.anyio
async def test_client_ip_dep(client):
    path = "/ip"
    r = await client.get(path)
    assert r.status_code == 200
    assert r.json()["client ip"] == "127.0.0.1"

    ip = get_machine_ip()
    keys = "x_forwarded_for", "x_real_ip", "forwarded"
    client.headers[keys[0]] = ip
    r = await client.get(path)
    assert r.status_code == 200
    assert r.json() == {"client ip": ip, "server ip": ip}

    fake_ip = "127.0.0.2"
    client.headers.pop(keys[0])
    client.headers[keys[1]] = fake_ip
    r = await client.get(path)
    assert r.status_code == 200
    assert r.json() == {"client ip": fake_ip, "server ip": ip}

    client.headers.pop(keys[1])
    client.headers[keys[2]] = fake_ip
    r = await client.get(path)
    assert r.status_code == 200
    assert r.json() == {"client ip": "127.0.0.1", "server ip": ip}

    client.headers[keys[2]] = "for=192.0.2.60;proto=http;by=203.0.113.43"
    r = await client.get(path)
    assert r.status_code == 200
    assert r.json() == {"client ip": "192.0.2.60", "server ip": ip}

    client.headers[keys[1]] = fake_ip
    r = await client.get(path)
    assert r.status_code == 200
    assert r.json() == {"client ip": fake_ip, "server ip": ip}

    client.headers[keys[0]] = ip
    r = await client.get(path)
    assert r.status_code == 200
    assert r.json() == {"client ip": ip, "server ip": ip}

    client.headers[keys[0]] = ip + ",192.0.2.60"
    r = await client.get(path)
    assert r.status_code == 200
    assert r.json() == {"client ip": ip, "server ip": ip}
