"""PITFALL: a blocking call inside an `async def` endpoint freezes the whole server.

Use case: the most common FastAPI performance bug. time.sleep (or requests,
psycopg, boto3, open().read() on slow disks...) blocks the event loop, so requests
are handled ONE AT A TIME. 100 concurrent requests x 0.1 s = ~10 s.

Run:   uv run uvicorn workshop.ch15_fastapi_sync_vs_async.03_async_endpoint_blocking_call_pitfall:app --port 8080
Bench: uv run python -m workshop.ch15_fastapi_sync_vs_async.bench http://127.0.0.1:8080/work -n 100 -c 100
"""

import time

from fastapi import FastAPI

app = FastAPI()


@app.get("/work")
async def work():
    time.sleep(0.1)  # blocks the event loop!
    return {"slept": 0.1}
