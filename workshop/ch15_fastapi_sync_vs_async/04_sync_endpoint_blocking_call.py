"""Fix #1: make the endpoint `def` so the blocking call runs in the thread pool.

Use case: quick fix when you must use a blocking library. Concurrency is
capped by the thread pool size (40): 100 requests x 0.1 s = ~0.3 s.

Run:   uv run uvicorn workshop.ch15_fastapi_sync_vs_async.04_sync_endpoint_blocking_call:app --port 8080
Bench: uv run python -m workshop.ch15_fastapi_sync_vs_async.bench http://127.0.0.1:8080/work -n 100 -c 100
"""

import time

from fastapi import FastAPI

app = FastAPI()


@app.get("/work")
def work():
    time.sleep(0.1)  # blocks only one worker thread
    return {"slept": 0.1}
