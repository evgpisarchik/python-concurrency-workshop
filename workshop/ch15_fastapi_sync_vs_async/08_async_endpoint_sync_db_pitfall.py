"""PITFALL: `async def` endpoint + a SYNC database driver.

Use case: see the "I made it async, why is it slower?" bug. Every query
blocks the event loop, so throughput collapses to one query at a time.

Prereq: products DB from chapter 5
Run:    uv run uvicorn workshop.ch15_fastapi_sync_vs_async.08_async_endpoint_sync_db_pitfall:app --port 8080
Bench:  uv run python -m workshop.ch15_fastapi_sync_vs_async.bench http://127.0.0.1:8080/work -n 2000 -c 100
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from workshop.common import PRODUCT_QUERY, dsn

pool = ConnectionPool(dsn("products"), min_size=6, max_size=6, open=False, kwargs={"row_factory": dict_row})


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open()
    yield
    pool.close()


app = FastAPI(lifespan=lifespan)


@app.get("/work")
async def work():
    with pool.connection() as conn:  # blocking call on the event loop!
        return conn.execute(PRODUCT_QUERY).fetchone()
