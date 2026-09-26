import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium", app_title="9 · Web apps")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 9 · Web applications: WSGI vs ASGI, sync vs async endpoints

    This notebook starts real servers as subprocesses (`workshop/web/`) and load-tests them with a small asyncio
    benchmark (`workshop/bench.py`), so you can **measure** each concurrency model instead of taking it on faith.
    """)
    return


@app.cell
def _():
    import asyncio
    import threading
    import time
    from functools import partial

    import aiohttp
    import marimo as mo
    from asgiref.sync import async_to_sync, sync_to_async

    from workshop.bench import bench
    from workshop.nb import gate, start_server, stop_server

    return (
        aiohttp,
        async_to_sync,
        asyncio,
        bench,
        gate,
        mo,
        partial,
        start_server,
        stop_server,
        sync_to_async,
        threading,
        time,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## WSGI vs ASGI

    *Listings 9.6, 9.7.* The interface between the web server and your app decides the concurrency model.

    ```python
    # WSGI (PEP 3333): a sync callable; a worker thread/process is busy until it returns
    def application(environ, start_response):
        start_response("200 OK", [("Content-Type", "text/html")])
        return [b"WSGI hello!"]

    # ASGI: a coroutine that exchanges events; one worker interleaves many requests
    async def application(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": [[b"content-type", b"text/html"]]})
        await send({"type": "http.response.body", "body": b"ASGI hello!"})
    ```

    | | WSGI | ASGI |
    |---|---|---|
    | Concurrency | one request per worker thread/process | many requests per worker (event loop) |
    | WebSockets / streaming / long polling | ❌ / limited | ✅ |
    | Frameworks | Flask, Django (sync), Bottle | FastAPI, Starlette, Django 3+, Litestar, Quart |
    | Servers | gunicorn, uWSGI | uvicorn, hypercorn, granian, daphne |

    `aiohttp` is async-native but **not** ASGI: it ships its own server.

    FastAPI (ASGI) lets you mix both styles. **`def` endpoints** run in a thread pool (AnyIO, 40 threads by default), and
    **`async def` endpoints** run directly on the event loop. All the variants live in `workshop/web/fastapi_app.py`.
    """)
    return


@app.cell
def _(mo):
    web_button = mo.ui.run_button(label="Start the FastAPI server and run the I/O benchmarks")
    web_button
    return (web_button,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Where does each endpoint run?
    """)
    return


@app.cell
async def _(aiohttp, asyncio, gate, start_server, stop_server, web_button):
    gate(web_button)
    _server = start_server(
        ["-m", "uvicorn", "workshop.web.fastapi_app:app", "--port", "8901", "--log-level", "warning"], 8901
    )
    async with aiohttp.ClientSession() as _session:
        for _path in ("/info", "/info-async"):
            _replies = await asyncio.gather(*(_session.get(f"http://127.0.0.1:8901{_path}") for _ in range(5)))
            _threads = sorted({(await _r.json())["thread"] for _r in _replies})
            print(f"{_path:<12} ran on: {_threads}")
    stop_server(_server)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Waiting on I/O: the classic pitfall and its fixes

    100 concurrent requests. Each handler waits 0.1 s:

    | endpoint | handler |
    |---|---|
    | `/sleep/blocking-in-async` | `async def` + `time.sleep(0.1)`: **blocks the event loop** |
    | `/sleep/blocking-in-def` | `def` + `time.sleep(0.1)`: blocks one of 40 pool threads |
    | `/sleep/to-thread` | `async def` + `await asyncio.to_thread(time.sleep, 0.1)` |
    | `/sleep/non-blocking` | `async def` + `await asyncio.sleep(0.1)` |
    """)
    return


@app.cell
async def _(bench, gate, start_server, stop_server, web_button):
    gate(web_button)
    _server = start_server(
        ["-m", "uvicorn", "workshop.web.fastapi_app:app", "--port", "8901", "--log-level", "warning"], 8901
    )
    for _endpoint in ("blocking-in-async", "blocking-in-def", "to-thread", "non-blocking"):
        _r = await bench(f"http://127.0.0.1:8901/sleep/{_endpoint}", requests=100, concurrency=100)
        print(f"/sleep/{_endpoint:<18} {_r['total_s']} s total, {_r['req_per_s']} req/s")
    stop_server(_server)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Database drivers

    Same idea with a real query (needs the database from notebook 5): a sync driver in `def`, **a sync driver inside
    `async def`**, and an async driver.
    """)
    return


@app.cell
def _(mo):
    db_button = mo.ui.run_button(label="Run the database benchmarks")
    db_button
    return (db_button,)


@app.cell
async def _(bench, db_button, gate, start_server, stop_server):
    gate(db_button)
    _server = start_server(
        ["-m", "uvicorn", "workshop.web.fastapi_app:app", "--port", "8901", "--log-level", "warning"], 8901
    )
    for _endpoint in ("sync-in-def", "sync-in-async", "async"):
        _r = await bench(f"http://127.0.0.1:8901/db/{_endpoint}", requests=2000, concurrency=100)
        print(f"/db/{_endpoint:<14} {_r['req_per_s']} req/s, {_r['errors']} errors")
    stop_server(_server)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## CPU-bound endpoints

    A CPU-heavy handler blocks the loop just like `time.sleep`. Compare: inline, `to_thread` (frees the loop, but the GIL
    still serializes the work), a process pool, and simply running **4 worker processes** (`uvicorn --workers 4`).
    """)
    return


@app.cell
def _(mo):
    cpu_button = mo.ui.run_button(label="Run the CPU benchmarks")
    cpu_button
    return (cpu_button,)


@app.cell
async def _(asyncio, bench, cpu_button, gate, start_server, stop_server):
    gate(cpu_button)
    _server = start_server(
        ["-m", "uvicorn", "workshop.web.fastapi_app:app", "--port", "8901", "--log-level", "warning"], 8901
    )
    for _endpoint in ("inline", "thread", "process"):
        _r = await bench(f"http://127.0.0.1:8901/cpu/{_endpoint}", requests=32, concurrency=8)
        print(f"/cpu/{_endpoint:<8} 1 worker:  {_r['total_s']} s total")
    stop_server(_server)

    _server = start_server(
        ["-m", "uvicorn", "workshop.web.fastapi_app:app", "--port", "8902", "--workers", "4", "--log-level", "warning"],
        8902,
    )
    await asyncio.sleep(2)  # let all 4 workers finish starting
    _r = await bench("http://127.0.0.1:8902/cpu/inline", requests=32, concurrency=8)
    print(f"/cpu/inline   4 workers: {_r['total_s']} s total")
    stop_server(_server)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## WebSockets: long-lived connections and fan-out

    *Listings 9.9, 9.10.* A Starlette WebSocket endpoint pushes the number of connected users to **every** client whenever
    someone joins or leaves, sending to all of them concurrently. Long-lived connections like this are something only ASGI can
    serve efficiently. The count is per process: with `--workers N` you'd need Redis pub/sub or similar to share it.
    """)
    return


@app.cell
def _(mo):
    ws_button = mo.ui.run_button(label="Run the WebSocket demo")
    ws_button
    return (ws_button,)


@app.cell
async def _(aiohttp, asyncio, gate, start_server, stop_server, ws_button):
    gate(ws_button)
    _server = start_server(
        ["-m", "uvicorn", "workshop.web.websocket_counter:app", "--port", "8903", "--log-level", "warning"], 8903
    )
    async with aiohttp.ClientSession() as _session:
        _sockets = []
        for _i in range(3):
            _sockets.append(await _session.ws_connect("http://127.0.0.1:8903/counter"))
            await asyncio.sleep(0.1)
            print(f"user {_i + 1} joined -> every client now sees:", [(await _ws.receive()).data for _ws in _sockets])
        await _sockets.pop().close()
        await asyncio.sleep(0.1)
        print("one user left     -> remaining clients see:", [(await _ws.receive()).data for _ws in _sockets])
        for _ws in _sockets:
            await _ws.close()
    stop_server(_server)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Crossing the sync/async boundary (Django's asgiref)

    *Book section 9.4.* Django (and anything built on `asgiref`) bridges both worlds:

    | Call from ↓ / to → | sync code | async code |
    |---|---|---|
    | **async view** | `await sync_to_async(fn, thread_sensitive=...)()` | `await` |
    | **sync view** | call it | `async_to_sync(coro_fn)()` |

    `thread_sensitive=True` (the default) runs **every** call on one shared thread: safe for the Django ORM, but serial.
    `thread_sensitive=False` uses a thread pool.
    """)
    return


@app.cell
async def _(async_to_sync, asyncio, partial, sync_to_async, threading, time):
    def blocking_sleep(seconds: float) -> str:
        time.sleep(seconds)
        return threading.current_thread().name

    for _sensitive in (True, False):
        _fn = sync_to_async(partial(blocking_sleep, 0.5), thread_sensitive=_sensitive)
        _start = time.perf_counter()
        _threads = await asyncio.gather(*(_fn() for _ in range(4)))
        print(
            f"thread_sensitive={_sensitive!s:<5}: 4 x 0.5 s took {time.perf_counter() - _start:.2f} s on {len(set(_threads))} thread(s)"
        )

    async def fetch_all_async() -> list[float]:
        return await asyncio.gather(*(asyncio.sleep(0.5, result=i) for i in range(10)))

    # async_to_sync is for SYNC code (e.g. a Django sync view); here it runs in a plain thread
    _start = time.perf_counter()
    _results = await asyncio.to_thread(async_to_sync(fetch_all_async))
    print(f"async_to_sync from sync code: {len(_results)} async calls in {time.perf_counter() - _start:.2f} s")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## The rules

    1. Blocking library: use a `def` endpoint, or `asyncio.to_thread`.
    2. Async library: use an `async def` endpoint.
    3. **Never** call blocking code directly inside `async def`.
    4. CPU-heavy work: a process pool, a job queue, or more `--workers`.

    For a bigger load test with a UI, see `locust/README.md`.
    """)
    return


if __name__ == "__main__":
    app.run()
