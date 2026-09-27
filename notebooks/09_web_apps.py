import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium", app_title="9 · Web apps")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 9 · Web applications: WSGI vs ASGI, sync vs async endpoints

    This notebook starts real servers as subprocesses (`workshop/web/`) and load-tests them with a small asyncio
    load generator (`workshop/bench.py`), so you can **measure** each concurrency model instead of taking it on faith.
    """)
    return


@app.cell
def _():
    import asyncio
    import time

    import aiohttp
    import marimo as mo
    from asgiref.sync import async_to_sync, sync_to_async

    from workshop.bench import bench
    from workshop.common import timed
    from workshop.nb import gate, start_server

    return aiohttp, async_to_sync, asyncio, bench, gate, mo, start_server, sync_to_async, time, timed


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
    web_button = mo.ui.run_button(label="Start the servers and run the demos")
    web_button
    return (web_button,)


@app.cell
def _(gate, start_server, web_button):
    gate(web_button, "the web demos")
    start_server(["-m", "uvicorn", "workshop.web.fastapi_app:app", "--port", "8901", "--log-level", "warning"], 8901)
    api = "http://127.0.0.1:8901"
    return (api,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Where does each endpoint run?

    Both endpoints return the name of the thread that ran them. We call each one 5 times concurrently:
    """)
    return


@app.cell
async def _(aiohttp, api, asyncio):
    async with aiohttp.ClientSession() as _session:

        async def thread_name(path: str) -> str:
            async with _session.get(f"{api}{path}") as response:
                return (await response.json())["thread"]

        print("def endpoint ran on:      ", set(await asyncio.gather(*(thread_name("/info") for _ in range(5)))))
        print("async def endpoint ran on:", set(await asyncio.gather(*(thread_name("/info-async") for _ in range(5)))))
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
async def _(api, bench, timed):
    with timed("blocking-in-async"):
        await bench(f"{api}/sleep/blocking-in-async", requests=100, concurrency=100)
    with timed("blocking-in-def  "):
        await bench(f"{api}/sleep/blocking-in-def", requests=100, concurrency=100)
    with timed("to-thread        "):
        await bench(f"{api}/sleep/to-thread", requests=100, concurrency=100)
    with timed("non-blocking     "):
        await bench(f"{api}/sleep/non-blocking", requests=100, concurrency=100)
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
async def _(api, bench, db_button, gate, timed):
    gate(db_button, "the database benchmarks")
    with timed("def + sync driver         "):
        await bench(f"{api}/db/sync-in-def", requests=2000, concurrency=100)
    with timed("async def + sync driver   "):
        await bench(f"{api}/db/sync-in-async", requests=2000, concurrency=100)
    with timed("async def + async driver  "):
        await bench(f"{api}/db/async", requests=2000, concurrency=100)
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
async def _(api, asyncio, bench, start_server, timed):
    with timed("inline, 1 worker    "):
        await bench(f"{api}/cpu/inline", requests=32, concurrency=8)
    with timed("to_thread, 1 worker "):
        await bench(f"{api}/cpu/thread", requests=32, concurrency=8)
    with timed("process pool        "):
        await bench(f"{api}/cpu/process", requests=32, concurrency=8)

    start_server(
        ["-m", "uvicorn", "workshop.web.fastapi_app:app", "--port", "8902", "--workers", "4", "--log-level", "warning"],
        8902,
    )
    await asyncio.sleep(2)  # let all 4 workers finish starting
    with timed("inline, 4 workers   "):
        await bench("http://127.0.0.1:8902/cpu/inline", requests=32, concurrency=8)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## WebSockets: long-lived connections and fan-out

    *Listings 9.9, 9.10.* A Starlette WebSocket endpoint (`workshop/web/websocket_counter.py`) pushes the number of
    connected users to **every** client whenever someone joins or leaves. Long-lived connections like this are something
    only ASGI can serve efficiently. The count is per process: with `--workers N` you'd need Redis pub/sub or similar.
    """)
    return


@app.cell
async def _(aiohttp, gate, start_server, web_button):
    gate(web_button, "the web demos")
    start_server(
        ["-m", "uvicorn", "workshop.web.websocket_counter:app", "--port", "8903", "--log-level", "warning"], 8903
    )
    _url = "http://127.0.0.1:8903/counter"

    async with aiohttp.ClientSession() as _session:
        _alice = await _session.ws_connect(_url)
        print("alice joined: alice sees", (await _alice.receive()).data)

        _bob = await _session.ws_connect(_url)
        print("bob joined:   alice sees", (await _alice.receive()).data, "and bob sees", (await _bob.receive()).data)

        await _bob.close()
        print("bob left:     alice sees", (await _alice.receive()).data)
        await _alice.close()
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
async def _(async_to_sync, asyncio, sync_to_async, time, timed):
    def blocking_call():
        time.sleep(0.5)

    with timed("4 calls, thread_sensitive=True "):
        await asyncio.gather(*(sync_to_async(blocking_call)() for _ in range(4)))

    with timed("4 calls, thread_sensitive=False"):
        await asyncio.gather(*(sync_to_async(blocking_call, thread_sensitive=False)() for _ in range(4)))

    async def async_call() -> str:
        await asyncio.sleep(0.5)
        return "result of an async call"

    # async_to_sync is for SYNC code (e.g. a Django sync view). Here the sync caller is a plain thread.
    print(await asyncio.to_thread(async_to_sync(async_call)))
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
