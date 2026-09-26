import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium", app_title="4 · Concurrent requests")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 4 · Concurrent web requests: gather, as_completed, wait

    All requests go to a **local test server** (`workshop/testserver.py`) with a `/delay?seconds=` endpoint, so timings
    are predictable and no public site gets hammered. Each cell starts the server with `async with serve()` and stops it at the end.
    """)
    return


@app.cell
def _():
    import asyncio
    import logging
    import time

    import aiohttp
    import marimo as mo

    from workshop.common import async_timed
    from workshop.testserver import serve

    return aiohttp, async_timed, asyncio, logging, mo, serve, time


@app.cell
def _(aiohttp, async_timed):
    @async_timed()
    async def fetch_status(session: aiohttp.ClientSession, url: str) -> int:
        async with session.get(url) as response:
            return response.status

    return (fetch_status,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## One request, one shared session, timeouts

    *Listings 4.1–4.3.* `ClientSession` holds the connection pool, so create **one per application** and reuse it. It's an
    *async context manager* (`async with`, via `__aenter__`/`__aexit__`), because opening and closing it needs I/O.
    Always set timeouts: a session-wide default, overridden per request when needed.
    """)
    return


@app.cell
async def _(aiohttp, fetch_status, serve):
    async with serve() as _base:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=1, connect=0.1)) as _session:
            print(await fetch_status(_session, f"{_base}/delay?seconds=0.1"))
            try:
                _short = aiohttp.ClientTimeout(total=0.2)  # overrides the session default for this request
                async with _session.get(f"{_base}/delay?seconds=0.5", timeout=_short) as _response:
                    await _response.read()
            except TimeoutError:
                print("per-request timeout of 0.2 s fired")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Pitfall: `await` inside a comprehension

    *Listings 4.4, 4.5.* Each task is created **and awaited** before the next one is created, so this is sequential.
    Create all the tasks first, then await them.
    """)
    return


@app.cell
async def _(aiohttp, asyncio, fetch_status, serve, time):
    async with serve() as _base, aiohttp.ClientSession() as _session:
        _url = f"{_base}/delay?seconds=1"

        _start = time.perf_counter()
        [await asyncio.create_task(fetch_status(_session, _url)) for _ in range(3)]
        print(f"await inside the comprehension: {time.perf_counter() - _start:.2f} s")

        _start = time.perf_counter()
        _tasks = [asyncio.create_task(fetch_status(_session, _url)) for _ in range(3)]
        [await _t for _t in _tasks]
        print(f"create all, then await:         {time.perf_counter() - _start:.2f} s")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## `gather`: fan out, collect everything, in order

    *Listings 4.6, 4.7.* 500 requests that each take 0.5 s. A `ClientSession` opens at most **100 connections** by default
    (`TCPConnector(limit=100)`), so they run in 5 waves of about 0.5 s each. Raising the limit lets them overlap (the rest of the time is opening 500 connections, with the server sharing this same event loop). Results come back in **input
    order**, not completion order.
    """)
    return


@app.cell
async def _(aiohttp, asyncio, serve, time):
    async def get_many(session: aiohttp.ClientSession, url: str, n: int) -> list[int]:
        async def one():
            async with session.get(url) as response:
                return response.status

        return await asyncio.gather(*(one() for _ in range(n)))

    async with serve() as _base:
        for _limit in (100, 500):
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=_limit)) as _s:
                _start = time.perf_counter()
                await get_many(_s, f"{_base}/delay?seconds=0.5", 500)
                print(f"500 requests, connection limit {_limit}: {time.perf_counter() - _start:.2f} s")

    async with serve() as _base, aiohttp.ClientSession() as _session:

        async def slept(seconds):
            async with _session.get(f"{_base}/delay?seconds={seconds}") as response:
                return (await response.json())["slept"]

        print("order of results:", await asyncio.gather(slept(1), slept(0.1), slept(0.5)))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## `gather` and exceptions

    By default the **first** exception propagates out of `gather`, and the other awaitables keep running. With
    `return_exceptions=True` exceptions come back as values, so you can keep the successes and log the failures.
    """)
    return


@app.cell
async def _(aiohttp, asyncio, fetch_status, serve):
    async with serve() as _base, aiohttp.ClientSession() as _session:
        _urls = [f"{_base}/delay?seconds=0.1", "python://not-a-valid-url"]
        try:
            await asyncio.gather(*(fetch_status(_session, _u) for _u in _urls))
        except Exception as error:
            print(f"default: gather raised {error!r}")

        _results = await asyncio.gather(*(fetch_status(_session, _u) for _u in _urls), return_exceptions=True)
        print("successes:", [_r for _r in _results if not isinstance(_r, Exception)])
        print("failures: ", [_r for _r in _results if isinstance(_r, Exception)])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## `as_completed`: handle each result as soon as it arrives

    *Listings 4.8, 4.9.* Useful for progress bars and streaming partial results. With `timeout=` whatever isn't done in time
    raises `TimeoutError`, but that work **keeps running in the background**, so cancel it yourself.
    """)
    return


@app.cell
async def _(aiohttp, asyncio, fetch_status, serve, time):
    async with serve() as _base, aiohttp.ClientSession() as _session:
        _start = time.perf_counter()
        for _next in asyncio.as_completed([fetch_status(_session, f"{_base}/delay?seconds={s}") for s in (2, 0.5, 1)]):
            await _next
            print(f"got a result at {time.perf_counter() - _start:.2f} s")

        _tasks = [asyncio.create_task(fetch_status(_session, f"{_base}/delay?seconds={s}")) for s in (0.5, 5, 5)]
        for _next in asyncio.as_completed(_tasks, timeout=1):
            try:
                await _next
            except TimeoutError:
                print("timed out waiting")
        print(f"still running in the background: {sum(not _t.done() for _t in _tasks)} task(s), cancelling them")
        for _t in _tasks:
            _t.cancel()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## `wait`: done/pending sets for fine-grained control

    *Listings 4.10–4.16.* `asyncio.wait(tasks, return_when=..., timeout=...)` returns `(done, pending)` sets of **Tasks**
    (bare coroutines aren't accepted since Python 3.11). Nothing is raised or cancelled for you:
    inspect `task.exception()`, and cancel what's pending.
    """)
    return


@app.cell
async def _(aiohttp, asyncio, fetch_status, logging, serve):
    async with serve() as _base, aiohttp.ClientSession() as _session:

        def _fetch(seconds):
            return asyncio.create_task(fetch_status(_session, f"{_base}/delay?seconds={seconds}"))

        print("--- ALL_COMPLETED + per-task exception handling (4.10, 4.11)")
        _done, _pending = await asyncio.wait([_fetch(0.1), asyncio.create_task(fetch_status(_session, "python://bad"))])
        for _t in _done:
            if _t.exception() is None:
                print("  result:", _t.result())
            else:
                logging.error("  request failed: %r", _t.exception())

        print("--- FIRST_EXCEPTION: all-or-nothing batch (4.12)")
        _tasks = [asyncio.create_task(fetch_status(_session, "python://bad")), _fetch(3), _fetch(3)]
        _done, _pending = await asyncio.wait(_tasks, return_when=asyncio.FIRST_EXCEPTION)
        print(f"  done={len(_done)} pending={len(_pending)} -> cancelling the rest")
        for _t in _pending:
            _t.cancel()

        print("--- FIRST_COMPLETED: fastest replica wins (4.13)")
        _done, _pending = await asyncio.wait([_fetch(1), _fetch(0.2), _fetch(2)], return_when=asyncio.FIRST_COMPLETED)
        print(f"  done={len(_done)} pending={len(_pending)}")
        for _t in _pending:
            _t.cancel()

        print("--- FIRST_COMPLETED in a loop: results as they arrive, keeping the Task objects (4.14)")
        _pending = {_fetch(s) for s in (0.3, 0.1, 0.2)}
        while _pending:
            _done, _pending = await asyncio.wait(_pending, return_when=asyncio.FIRST_COMPLETED)
            print(f"  {len(_done)} finished, {len(_pending)} left")

        print("--- timeout: a hard deadline, then drop only the slow optional call (4.15, 4.16)")
        _api_a, _api_b = _fetch(0.1), _fetch(2)
        _done, _pending = await asyncio.wait([_api_a, _api_b], timeout=1)
        if _api_b in _pending:
            print("  API B too slow, cancelling it; API A returned", _api_a.result())
            _api_b.cancel()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Which one to use

    | Need | Use |
    |---|---|
    | All results, in input order | `gather(*aws)` |
    | All results even if some fail | `gather(*aws, return_exceptions=True)` |
    | Results as soon as they're ready | `as_completed(aws)` |
    | Stop everything on the first error, with automatic cleanup | `asyncio.TaskGroup` (notebook 2) or `wait(..., FIRST_EXCEPTION)` |
    | First result wins | `wait(tasks, return_when=FIRST_COMPLETED)` |
    | Deadline for a group, decide what to cancel | `wait(tasks, timeout=...)` |
    | Deadline that cancels everything | `async with asyncio.timeout(...)` |
    """)
    return


if __name__ == "__main__":
    app.run()
