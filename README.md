# Python Concurrency Workshop

Interactive [marimo](https://marimo.io) notebooks on concurrency in Python: **threads, processes and asyncio**,
from "what is the GIL" up to building your own event loop. Every concept comes with a runnable demo that
**measures** the effect instead of only describing it.

## How to run

```bash
# once
uv sync                                   # Python 3.12+, installs everything into .venv

# open a notebook (the browser opens automatically)
uv run marimo edit notebooks/02_asyncio_basics.py

# or browse all notebooks from one page
uv run marimo edit notebooks/
```

Notebooks 5, 9, 10 (and one cell in 6) need Postgres:

```bash
docker compose up -d                      # Postgres on localhost:55432 (set PGPORT to change it)
uv run python -m workshop.db_setup        # create + seed the products database (once)
```

Demos that start servers, need the database, or take a while have a **Run** button. Everything else runs when the
notebook opens. A notebook can also run as a plain script: `uv run python notebooks/02_asyncio_basics.py`.

## Notebooks

| # | Notebook | Concepts |
|---|---|---|
| 1 | [Concurrency basics](notebooks/01_concurrency_basics.py) | I/O- vs CPU-bound, processes vs threads, the GIL, measured |
| 2 | [asyncio basics](notebooks/02_asyncio_basics.py) | coroutines, tasks, cancel/timeout/shield, futures, CPU & blocking-library pitfalls, debug mode, TaskGroup |
| 3 | [Sockets and the event loop](notebooks/03_sockets_and_event_loop.py) | blocking vs non-blocking sockets, busy polling vs `selectors` (CPU measured), asyncio servers, graceful shutdown |
| 4 | [Concurrent requests](notebooks/04_concurrent_requests.py) | aiohttp, `gather`, `as_completed`, `wait` (ALL/FIRST_COMPLETED/FIRST_EXCEPTION/timeout), connection limits |
| 5 | [Async databases](notebooks/05_async_databases.py) | asyncpg, one query per connection, pools and pool size, async generators, cursors |
| 6 | [Multiprocessing](notebooks/06_multiprocessing.py) | process pools, `run_in_executor`, MapReduce, chunk size, shared memory, races and locks, one loop per process |
| 7 | [Threads](notebooks/07_threads.py) | thread per connection, blocking libraries 5 ways, locks, RLock, deadlock, asyncio in a background thread, GIL-releasing C code |
| 8 | [Streams and a chat server](notebooks/08_streams_and_chat.py) | protocols + futures, streams and back-pressure, concurrent chat server with idle timeout |
| 9 | [Web apps](notebooks/09_web_apps.py) | WSGI vs ASGI, `def` vs `async def` endpoints under load, sync vs async DB drivers, CPU endpoints and `--workers`, WebSockets, `sync_to_async` |
| 10 | [Microservices](notebooks/10_microservices.py) | backend-for-frontend fan-out, time budgets, graceful degradation, retries, circuit breaker |
| 11 | [Synchronization](notebooks/11_synchronization.py) | races across `await`, Lock, Semaphore (measured), BoundedSemaphore, Event (and lost triggers), Condition |
| 12 | [Queues](notebooks/12_queues.py) | workers, back-pressure, background jobs behind an endpoint, crawler, priority/LIFO queues |
| 13 | [Subprocesses](notebooks/13_subprocesses.py) | run/stream/timeout, pipe deadlock, parallel external tools with a limit, driving interactive programs |
| 14 | [Under the hood](notebooks/14_under_the_hood.py) | contextvars, `sleep(0)`, uvloop (measured), generators as coroutines, **build a Future, a Task and an event loop, then run a server on them**, eager tasks |

## Which tool for which job

| Your workload | Use | Why | Notebook |
|---|---|---|---|
| Many network/DB calls, async libraries available | **asyncio** | thousands of concurrent waits on one thread | 2, 4, 5 |
| Blocking library you can't replace (requests, boto3, psycopg2) | **threads** (`asyncio.to_thread`) | the GIL is released during I/O | 7 |
| CPU-heavy pure Python | **processes** (`ProcessPoolExecutor`) | one GIL per process means real parallelism | 1, 6 |
| CPU-heavy C code that releases the GIL (numpy, hashlib, zlib) | **threads** | parallel without pickling | 7 |
| External CLI tools | **asyncio subprocesses** | the OS runs them in parallel | 13 |
| Web API doing I/O | **ASGI** + async drivers | many requests per worker | 9 |
| Scale an async service past one core | **N processes, each with a loop** | `uvicorn --workers N` | 6, 9 |
| Free-threaded Python 3.13t/3.14t | threads for CPU work too | no GIL | 1 |

## Pitfalls, each with a demo

| Pitfall | Notebook | Fix |
|---|---|---|
| Calling a coroutine without awaiting it / awaiting in sequence | 2 | `create_task`, `gather`, `TaskGroup` |
| `await` inside a comprehension | 4 | create all tasks first |
| CPU-bound code in a coroutine | 2, 9 | process pool / more workers |
| Blocking library (`requests`, `time.sleep`, sync DB driver) in `async def` | 2, 9 | async library or `to_thread` |
| Threads for CPU-bound Python | 1 | processes |
| Blocking sockets with several clients / busy polling | 3 | selectors / asyncio |
| Two queries on one DB connection | 5 | a pool |
| Race across an `await` | 11 | `asyncio.Lock` |
| Race on shared memory between processes | 6 | `get_lock()` |
| Re-entrant locking, lock-order deadlock | 7 | `RLock`, one global lock order |
| Extra semaphore release | 11 | `BoundedSemaphore` |
| Events dropping triggers | 11 | a queue |
| Equal priorities in a PriorityQueue | 12 | insertion counter |
| Unread subprocess pipe | 13 | stream it or `communicate()` |
| Timing-based interaction with a subprocess | 13 | wait for the prompt (Event) |
| Worker function defined in a notebook cell | 6 | put it in a module |

## Layout

```
notebooks/            the workshop (marimo notebooks)
workshop/             support code that must live in real modules:
  cpu.py, shared_memory.py, map_reduce.py, db_workers.py   functions sent to process pools (pickled by module + name)
  testserver.py       local HTTP server (/delay, /page, /stats): demos don't depend on the internet
  bench.py            asyncio HTTP load generator
  web/                FastAPI app with every sync/async variant, Starlette WebSocket counter
  microservices/      product / inventory / favorites / cart services + BFF
  children/           child programs for the subprocess notebook
  db_setup.py         create + seed the products database
  nb.py               notebook helpers (run buttons, start/stop servers, thread-safe timeline)
locust/               optional Locust load tests
docker/initdb/        Postgres databases (products, cart, favorites)
```

## Ports used

| Port | Used by |
|---|---|
| 55432 (`PGPORT`) | Postgres |
| 8121, 8141-8142, 8301-8307, 8701-8703, 8801 | servers that run inside single demos |
| 8200-8204 | microservices (notebook 10) |
| 8901-8903 | FastAPI / WebSocket servers (notebook 9) |
| 8089 | Locust UI |

## Credits

Based on the source code of Matthew Fowler's *Concurrency in Python with Asyncio* (Manning):
[concurrency-in-python-with-asyncio](https://github.com/concurrency-in-python-with-asyncio/concurrency-in-python-with-asyncio).
Notebooks reference the book's listing numbers. The FastAPI sync-vs-async experiments were inspired by
[JuanJFarina/python-concurrency-with-asyncio](https://github.com/JuanJFarina/python-concurrency-with-asyncio).

Compared with the book's code: updated for Python 3.12+, rewritten as measured notebook demos, and trimmed to concurrency
concepts. Terminal UIs, the Tkinter GUI, CRUD endpoints, transactions and duplicate listings were left out.
