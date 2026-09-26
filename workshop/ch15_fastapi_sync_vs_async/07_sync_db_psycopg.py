"""Sync DB access: `def` endpoint + psycopg with a connection pool.

Use case: the classic threaded stack. Throughput is bounded by the thread
pool (40) and the connection pool size.

Prereq: products DB from chapter 5
Run:    uv run uvicorn workshop.ch15_fastapi_sync_vs_async.07_sync_db_psycopg:app --port 8080
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
def work():
    with pool.connection() as conn:
        return conn.execute(PRODUCT_QUERY).fetchone()
