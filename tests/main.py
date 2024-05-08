from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from pydantic import BaseModel

from asyncur import AsyncRedis


@asynccontextmanager
async def lifespan(app):
    async with AsyncRedis(app):
        yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root(request: Request) -> list[str]:
    return await AsyncRedis(request).keys()


@app.get("/redis")
async def get_value_from_redis_by_key(
    request: Request, key: str
) -> dict[str, str | None]:
    value = await AsyncRedis(request).get(key)
    return {key: value and value.decode()}


class Item(BaseModel):
    key: str
    value: str


@app.post("/redis")
async def set_redis_key_value(request: Request, item: Item) -> dict[str, str | None]:
    redis = AsyncRedis(request)
    await redis.set(item.key, item.value)
    return {item.key: (v := await redis.get(item.key)) and v.decode()}
