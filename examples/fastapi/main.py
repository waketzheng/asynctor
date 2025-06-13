from __future__ import annotations

import copy
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import fastapi_cdn_host
import uvicorn
from fastapi import FastAPI, Request
from pydantic import BaseModel

from asynctor.contrib.fastapi import AioRedis, register_aioredis

fake_db = {"users": [{"id": 1, "name": "John"}]}


async def init_db(app: FastAPI) -> None:
    db = copy.deepcopy(fake_db)
    app.state.db = db


async def teardown(app: FastAPI) -> None:
    app.state.db.clear()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    await init_db(app)
    yield
    await teardown(app)


app = FastAPI(lifespan=lifespan)
register_aioredis(app, host="127.0.0.1")
fastapi_cdn_host.patch_docs(app)


@app.get("/users")
async def get_user_list(request: Request) -> list[dict[str, int | str]]:
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


class MsgResponse(BaseModel):
    msg: str


@app.post("/redis/set", response_model=MsgResponse)
async def cache_to_redis(redis: AioRedis, data: KeyValueExpire) -> dict[str, str]:
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


if __name__ == "__main__":
    uvicorn.run(app)
