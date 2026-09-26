"""FastAPI `def` endpoint: FastAPI runs it in a thread pool.

Use case: plain (sync) endpoints are safe to write with blocking libraries,
because FastAPI/Starlette offloads each call to AnyIO's worker thread pool
(40 threads by default). Watch the thread id change between requests.

Run:   uv run uvicorn workshop.ch15_fastapi_sync_vs_async.01_sync_endpoint:app --port 8080
Bench: uv run python -m workshop.ch15_fastapi_sync_vs_async.bench http://127.0.0.1:8080/work
"""

import os
import threading

from fastapi import FastAPI

app = FastAPI()


@app.get("/work")
def work():
    return {"pid": os.getpid(), "thread": threading.get_ident(), "threads": threading.active_count()}
