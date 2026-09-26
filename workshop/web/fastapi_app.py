"""One FastAPI app with every sync/async endpoint variant, so the notebook can load-test them side by side.

    uv run uvicorn workshop.web.fastapi_app:app --port 8101 [--workers 4]

Each endpoint "waits" 100 ms (sleep endpoints) or runs one product query (db endpoints).
"""

import asyncio
import logging
import os
import threading
import time
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI, HTTPException
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from workshop.common import PRODUCT_QUERY, db_config, dsn
from workshop.cpu import count

DELAY = 0.1
CPU_WORK = 5_000_000


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.async_pool = None
    app.state.sync_pool = None
    try:  # the database is optional: only the /db/* endpoints need it
        app.state.async_pool = await asyncpg.create_pool(**db_config("products"), min_size=6, max_size=6)
        app.state.sync_pool = ConnectionPool(dsn("products"), min_size=6, max_size=6, kwargs={"row_factory": dict_row})
    except Exception as error:
        logging.warning("database not available, /db endpoints disabled: %s", error)
    with ProcessPoolExecutor() as process_pool:
        app.state.process_pool = process_pool
        yield
    if app.state.async_pool:
        await app.state.async_pool.close()
        app.state.sync_pool.close()


app = FastAPI(lifespan=lifespan)


@app.get("/info")
def info():
    """`def` endpoint: FastAPI runs it in its thread pool, so the thread id changes."""
    return {"pid": os.getpid(), "thread": threading.current_thread().name}


@app.get("/info-async")
async def info_async():
    """`async def` endpoint: runs on the event loop thread."""
    return {"pid": os.getpid(), "thread": threading.current_thread().name}


# --- waiting on I/O -----------------------------------------------------------
@app.get("/sleep/blocking-in-async")
async def blocking_in_async():
    time.sleep(DELAY)  # PITFALL: blocks the event loop, so the server handles one request at a time
    return {"slept": DELAY}


@app.get("/sleep/blocking-in-def")
def blocking_in_def():
    time.sleep(DELAY)  # blocks one thread of the 40-thread pool
    return {"slept": DELAY}


@app.get("/sleep/to-thread")
async def to_thread():
    await asyncio.to_thread(time.sleep, DELAY)
    return {"slept": DELAY}


@app.get("/sleep/non-blocking")
async def non_blocking():
    await asyncio.sleep(DELAY)
    return {"slept": DELAY}


# --- database -----------------------------------------------------------------
def _require(pool):
    if pool is None:
        raise HTTPException(503, "database not available: docker compose up -d && uv run python -m workshop.db_setup")
    return pool


@app.get("/db/sync-in-def")
def db_sync_in_def():
    with _require(app.state.sync_pool).connection() as conn:
        return conn.execute(PRODUCT_QUERY).fetchone()


@app.get("/db/sync-in-async")
async def db_sync_in_async():
    with _require(app.state.sync_pool).connection() as conn:  # PITFALL: blocking driver on the event loop
        return conn.execute(PRODUCT_QUERY).fetchone()


@app.get("/db/async")
async def db_async():
    async with _require(app.state.async_pool).acquire() as conn:
        return dict(await conn.fetchrow(PRODUCT_QUERY))


# --- CPU-bound ----------------------------------------------------------------
@app.get("/cpu/inline")
async def cpu_inline():
    return {"count": count(CPU_WORK)}  # blocks the loop


@app.get("/cpu/thread")
async def cpu_thread():
    return {"count": await asyncio.to_thread(count, CPU_WORK)}  # frees the loop, but the GIL serializes the work


@app.get("/cpu/process")
async def cpu_process():
    loop = asyncio.get_running_loop()
    return {"count": await loop.run_in_executor(app.state.process_pool, count, CPU_WORK)}
