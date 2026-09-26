"""Fix #2: keep `async def` and push only the blocking part to a thread.

Use case: an async endpoint that mostly awaits async I/O but has one blocking
call. asyncio.to_thread (or starlette.concurrency.run_in_threadpool) wraps it.

Run:   uv run uvicorn workshop.ch15_fastapi_sync_vs_async.05_async_endpoint_to_thread:app --port 8080
Bench: uv run python -m workshop.ch15_fastapi_sync_vs_async.bench http://127.0.0.1:8080/work -n 100 -c 100
"""

import asyncio
import time

from fastapi import FastAPI

app = FastAPI()


@app.get("/work")
async def work():
    await asyncio.to_thread(time.sleep, 0.1)
    return {"slept": 0.1}
