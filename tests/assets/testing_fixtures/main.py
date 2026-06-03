from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    app.state.started = True
    yield
    app.state.started = False


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def index():
    return {"a": 1, "lifespan": getattr(app.state, "started", False)}
