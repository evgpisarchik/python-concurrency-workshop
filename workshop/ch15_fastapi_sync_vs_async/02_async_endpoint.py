"""FastAPI `async def` endpoint: runs directly on the event loop.

Use case: the fastest option for endpoints that do no blocking work (no
thread hop). Every request runs on the same thread.

Run:   uv run uvicorn workshop.ch15_fastapi_sync_vs_async.02_async_endpoint:app --port 8080
Bench: uv run python -m workshop.ch15_fastapi_sync_vs_async.bench http://127.0.0.1:8080/work
"""

import os
import threading

from fastapi import FastAPI

app = FastAPI()


@app.get("/work")
async def work():
    return {"pid": os.getpid(), "thread": threading.get_ident(), "threads": threading.active_count()}
