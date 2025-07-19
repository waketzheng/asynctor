from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from pydantic import BaseModel

from asynctor import AsyncRedis
from asynctor.contrib.fastapi import AioRedis, AioRedisDep, ClientIpDep, register_aioredis
from asynctor.utils import get_machine_ip


@asynccontextmanager
async def lifespan(app):
    async with AsyncRedis(app):
        yield


app = FastAPI()
app_for_utils_test = FastAPI(lifespan=lifespan)
app_default_to_mount_lifespan = FastAPI(lifespan=lifespan)
register_aioredis(app)


@app.get("/")
async def root(redis: AioRedis) -> list[str]:
    return await redis.keys()


@app_default_to_mount_lifespan.get("/state")
@app_for_utils_test.get("/state")
async def state(request: Request):
    return {"redis": str(getattr(request.app.state, "redis", None))}


@app.get("/redis")
async def get_value_from_redis_by_key(redis: AioRedis, key: str) -> dict[str, str | None]:
    value = await redis.get(key)
    return {key: value and value.decode()}


class Item(BaseModel):
    key: str
    value: str


@app.post("/redis")
async def set_redis_key_value(redis: AioRedisDep, item: Item) -> dict[str, str | None]:
    await redis.set(item.key, item.value)
    return {item.key: (v := await redis.get(item.key)) and v.decode()}


@app.get("/ip")
def get_your_ip(client_ip: ClientIpDep) -> dict[str, str]:
    return {"client ip": client_ip, "server ip": get_machine_ip()}
