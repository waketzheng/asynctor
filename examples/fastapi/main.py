from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from asynctor.contrib.fastapi import (
    AioRedisDep,
    add_timing_middleware,
    config_access_log,
    register_aioredis,
    runserver,
)

app = FastAPI()
add_timing_middleware(app)
register_aioredis(app)
config_access_log(app)


@app.get("/redis/keys")
async def get_redis_keys(redis: AioRedisDep) -> list[str]:
    keys = await redis.keys()
    return keys


class KeyValueExpire(BaseModel):
    key: str
    value: str
    expire: int | None = None


class MsgResponse(BaseModel):
    msg: str


@app.post("/redis/set", response_model=MsgResponse)
async def cache_to_redis(redis: AioRedisDep, data: KeyValueExpire) -> dict[str, str]:
    await redis.set(data.key, data.value, data.expire)
    return {"msg": "OK"}


@app.get("/redis/get")
async def get_cached_string_from_redis(redis: AioRedisDep, key: str) -> dict[str, str | None]:
    value = await redis.get(key)
    if isinstance(value, bytes):
        value = value.decode()
    elif value is not None and not isinstance(value, str):
        value = str(value)
    return {key: value}


if __name__ == "__main__":
    runserver(app, reload=True)
