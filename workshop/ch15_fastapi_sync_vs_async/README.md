# Chapter 15 (bonus): FastAPI sync vs async under load

Inspired by [JuanJFarina/python-concurrency-with-asyncio](https://github.com/JuanJFarina/python-concurrency-with-asyncio).
Every app exposes `GET /work`, so the same benchmark works for all of them.

```bash
uv run uvicorn workshop.ch15_fastapi_sync_vs_async.<file>:app --port 8080
uv run python -m workshop.ch15_fastapi_sync_vs_async.bench http://127.0.0.1:8080/work -n 1000 -c 100
# or: uv run --group load locust -f locust/work.py
```

| File | Use case |
|---|---|
| `01_sync_endpoint.py` | `def` endpoint runs in AnyIO's thread pool (40 threads) |
| `02_async_endpoint.py` | `async def` runs on the event loop with no thread hop |
| `03_async_endpoint_blocking_call_pitfall.py` | **Pitfall:** `time.sleep` inside `async def` serializes the whole server |
| `04_sync_endpoint_blocking_call.py` | Fix: `def` endpoint, limited by the thread pool |
| `05_async_endpoint_to_thread.py` | Fix: `await asyncio.to_thread(blocking)` |
| `06_async_endpoint_async_io.py` | Best: a non-blocking library, where only the event loop limits concurrency |
| `07_sync_db_psycopg.py` | `def` + psycopg pool: the classic threaded stack |
| `08_async_endpoint_sync_db_pitfall.py` | **Pitfall:** `async def` + a sync DB driver |
| `09_async_db_asyncpg.py` | `async def` + asyncpg pool from `lifespan` |
| `10_cpu_bound_endpoint.py` | CPU work: inline vs thread vs process pool vs `--workers` |
| `bench.py` | An asyncio load generator (Semaphore + one ClientSession) |

## Sample results (100 concurrent requests, 1 worker, laptop)

| App | Handler does | Total |
|---|---|---|
| 03 | `async def` + `time.sleep(0.1)` | **~10 s** (one request at a time) |
| 04 | `def` + `time.sleep(0.1)` | ~0.3 s |
| 05 | `async def` + `to_thread(sleep)` | ~0.4 s |
| 06 | `async def` + `asyncio.sleep(0.1)` | ~0.12 s |

| App (2000 req, c=100, product query) | req/s |
|---|---|
| 07 `def` + psycopg | ~1,800 |
| 08 `async def` + psycopg (pitfall) | ~480 |
| 09 `async def` + asyncpg | ~9,300 |

## The rules

1. Blocking library → `def` endpoint (or `asyncio.to_thread`).
2. Async library → `async def` endpoint.
3. **Never** call blocking code directly inside `async def`.
4. CPU-heavy → a process pool, a job queue, or more `--workers`.
