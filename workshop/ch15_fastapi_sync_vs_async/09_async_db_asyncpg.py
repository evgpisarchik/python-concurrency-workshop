"""Async DB access: `async def` endpoint + asyncpg pool created in lifespan.

Use case: the recommended async stack. Many requests wait on the database
at once without blocking each other. Keep ONE pool per process, created at
startup (not per request).

Prereq: products DB from chapter 5
Run:    uv run uvicorn workshop.ch15_fastapi_sync_vs_async.09_async_db_asyncpg:app --port 8080
Bench:  uv run python -m workshop.ch15_fastapi_sync_vs_async.bench http://127.0.0.1:8080/work -n 2000 -c 100
"""

from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI, Request

from workshop.common import PRODUCT_QUERY, db_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await asyncpg.create_pool(**db_config("products"), min_size=6, max_size=6)
    yield
    await app.state.pool.close()


app = FastAPI(lifespan=lifespan)


@app.get("/work")
async def work(request: Request):
    async with request.app.state.pool.acquire() as conn:
        return dict(await conn.fetchrow(PRODUCT_QUERY))
