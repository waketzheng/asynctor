from __future__ import annotations

import copy
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from pydantic import BaseModel

from asynctor.contrib.fastapi import AioRedis, register_aioredis

fake_db = {"users": [{"id": 1, "name": "John"}]}


@asynccontextmanager
async def lifespan(app):
    db = copy.deepcopy(fake_db)
    app.state.db = db
    yield
    del db


app = FastAPI(lifespan=lifespan)
register_aioredis(
    app,
    host="127.0.0.1",  # default is: os.getenv('REDIS_HOST', 'localhost')
)


@app.get("/users")
async def get_user_list(request: Request):
    db = request.app.state.db
    users = db["users"]
    return users


@app.get("/redis/keys")
async def get_redis_keys(redis: AioRedis) -> list[str]:
    keys = await redis.keys()
    return keys


class KeyValueExpire(BaseModel):
    key: str
    value: str
    expire: int | None = None


@app.post("/redis/set")
async def cache_to_redis(redis: AioRedis, data: KeyValueExpire):
    await redis.set(data.key, data.value, data.expire)
    return {"msg": "OK"}


@app.get("/redis/get")
async def get_cached_string_from_redis(redis: AioRedis, key: str) -> dict[str, str | None]:
    value = await redis.get(key)
    if isinstance(value, bytes):
        value = value.decode()
    elif value is not None and not isinstance(value, str):
        value = str(value)
    return {key: value}
