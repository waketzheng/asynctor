from contextlib import asynccontextmanager

from fastapi import FastAPI, Request


async def prepare_stuff(app):
    app.state.redis = "RedisClient"


@asynccontextmanager
async def lifespan(app):
    await prepare_stuff(app)
    yield


app = FastAPI(lifespan=lifespan)
app2 = FastAPI(lifespan=lifespan)


@app.get("/")
@app2.get("/")
async def index(request: Request):
    return {"state": getattr(request.app.state, "redis", None)}
