"""Fix #3 (best): use a non-blocking library and `await` it.

Use case: an I/O-heavy API. No thread pool limit: 1000 concurrent requests
x 0.1 s still take about 0.1 to 0.5 s on a single worker.

Run:   uv run uvicorn workshop.ch15_fastapi_sync_vs_async.06_async_endpoint_async_io:app --port 8080
Bench: uv run python -m workshop.ch15_fastapi_sync_vs_async.bench http://127.0.0.1:8080/work -n 1000 -c 1000
"""

import asyncio

from fastapi import FastAPI

app = FastAPI()


@app.get("/work")
async def work():
    await asyncio.sleep(0.1)
    return {"slept": 0.1}
