"""CPU-bound endpoints: event loop vs thread pool vs process pool vs workers.

Use case: an endpoint that computes something heavy (reports, image resizing,
ML inference in pure Python).
  /inline   blocks the event loop, so every other request waits
  /thread   frees the loop, but the GIL still serializes the computation
  /process  real parallelism with a ProcessPoolExecutor
Also try running /inline with several processes:  --workers 4

Run:   uv run uvicorn workshop.ch15_fastapi_sync_vs_async.10_cpu_bound_endpoint:app --port 8080
Bench: uv run python -m workshop.ch15_fastapi_sync_vs_async.bench http://127.0.0.1:8080/process -n 40 -c 8
"""

import asyncio
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI


def count(n: int = 5_000_000) -> int:
    counter = 0
    while counter < n:
        counter += 1
    return counter


@asynccontextmanager
async def lifespan(app: FastAPI):
    with ProcessPoolExecutor() as pool:
        app.state.process_pool = pool
        yield


app = FastAPI(lifespan=lifespan)


@app.get("/inline")
async def inline():
    return {"count": count()}


@app.get("/thread")
async def thread():
    return {"count": await asyncio.to_thread(count)}


@app.get("/process")
async def process():
    loop = asyncio.get_running_loop()
    return {"count": await loop.run_in_executor(app.state.process_pool, count)}
