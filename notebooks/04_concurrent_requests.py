import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium", app_title="4 · Concurrent requests")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 4 · Concurrent web requests: gather, as_completed, wait

    All requests go to a **local test server** (`workshop/testserver.py`) whose `/delay?seconds=` endpoint answers after
    that many seconds, so timings are predictable and no public site gets hammered. `DelayApi(session).get(seconds)`
    requests it and returns the delay it got back.
    """)
    return


@app.cell
async def _():
    import asyncio

    import aiohttp
    import marimo as mo

    from workshop.common import timed
    from workshop.testserver import start

    base_url = await start()  # runs for the rest of the notebook

    class DelayApi:
        """Client for the test server: `get(seconds)` answers after that many seconds."""

        def __init__(self, session: aiohttp.ClientSession):
            self.session = session

        async def get(self, seconds: float, **request_options) -> float:
            async with self.session.get(f"{base_url}/delay?seconds={seconds}", **request_options) as response:
                return (await response.json())["slept"]

        async def get_invalid_url(self):
            async with self.session.get("python://not-a-valid-url"):
                pass

    return DelayApi, aiohttp, asyncio, mo, timed


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## One shared session, timeouts

    *Listings 4.1–4.3.* `ClientSession` holds the connection pool, so create **one per application** and reuse it. It's an
    *async context manager* (`async with`), because opening and closing it needs I/O. Always set timeouts: a
    session-wide default, overridden per request when needed.
    """)
    return


@app.cell
async def _(DelayApi, aiohttp):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=1)) as _session:
        _api = DelayApi(_session)
        print("slept", await _api.get(0.1))

        try:
            await _api.get(0.5, timeout=aiohttp.ClientTimeout(total=0.2))  # overrides the session default
        except TimeoutError:
            print("the per-request timeout of 0.2 s fired")
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
async def _(DelayApi, aiohttp, asyncio, timed):
    async with aiohttp.ClientSession() as _session:
        _api = DelayApi(_session)
        with timed("await inside the comprehension"):
            [await asyncio.create_task(_api.get(1)) for _ in range(3)]

        with timed("create all, then await"):
            _tasks = [asyncio.create_task(_api.get(1)) for _ in range(3)]
            [await _task for _task in _tasks]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## `gather`: fan out, collect everything, in order

    *Listings 4.6, 4.7.* `gather` runs all awaitables concurrently and returns the results in **input order**, not
    completion order:
    """)
    return


@app.cell
async def _(asyncio):
    print(await asyncio.gather(asyncio.sleep(1, result="slow"), asyncio.sleep(0.1, result="fast")))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    500 requests that each take 0.5 s. A `ClientSession` opens at most **100 connections** by default
    (`TCPConnector(limit=100)`), so they run in 5 waves. Raising the limit lets them all overlap.
    """)
    return


@app.cell
async def _(DelayApi, aiohttp, asyncio, timed):
    async with aiohttp.ClientSession() as _session:
        _api = DelayApi(_session)
        with timed("500 requests, 100 connections (default)"):
            await asyncio.gather(*(_api.get(0.5) for _ in range(500)))

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=500)) as _session:
        _api = DelayApi(_session)
        with timed("500 requests, 500 connections"):
            await asyncio.gather(*(_api.get(0.5) for _ in range(500)))
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
async def _(DelayApi, aiohttp, asyncio):
    async with aiohttp.ClientSession() as _session:
        _api = DelayApi(_session)
        try:
            await asyncio.gather(_api.get(0.1), _api.get_invalid_url())
        except aiohttp.ClientError as _error:
            print("gather raised", repr(_error))

        print(await asyncio.gather(_api.get(0.1), _api.get_invalid_url(), return_exceptions=True))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## `as_completed`: handle each result as soon as it arrives

    *Listings 4.8, 4.9.* Useful for progress bars and streaming partial results. With `timeout=`, whatever isn't done in
    time raises `TimeoutError`, but that work **keeps running in the background**, so cancel it yourself.
    """)
    return


@app.cell
async def _(DelayApi, aiohttp, asyncio):
    async with aiohttp.ClientSession() as _session:
        _api = DelayApi(_session)
        for _next_done in asyncio.as_completed([_api.get(1), _api.get(0.2), _api.get(0.5)]):
            print("got", await _next_done)

        _tasks = [asyncio.create_task(_api.get(0.5)), asyncio.create_task(_api.get(5))]
        try:
            for _next_done in asyncio.as_completed(_tasks, timeout=1):
                print("got", await _next_done)
        except TimeoutError:
            print("timed out: cancelling what's still running")
            for _task in _tasks:
                _task.cancel()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## `wait`: done/pending sets for fine-grained control

    *Listings 4.10–4.16.* `asyncio.wait(tasks, return_when=..., timeout=...)` returns `(done, pending)` sets of **Tasks**.
    Nothing is raised or cancelled for you: read `task.result()` / `task.exception()`, and cancel what's pending.
    """)
    return


@app.cell
async def _(DelayApi, aiohttp, asyncio):
    async with aiohttp.ClientSession() as _session:
        _api = DelayApi(_session)
        # The fastest of three replicas wins
        _replicas = [asyncio.create_task(_api.get(_s)) for _s in (1, 0.2, 2)]
        _done, _pending = await asyncio.wait(_replicas, return_when=asyncio.FIRST_COMPLETED)
        print("FIRST_COMPLETED: got", _done.pop().result(), "| cancelling", len(_pending))
        for _task in _pending:
            _task.cancel()

        # All or nothing: stop at the first failure
        _batch = [asyncio.create_task(_api.get_invalid_url()), asyncio.create_task(_api.get(3))]
        _done, _pending = await asyncio.wait(_batch, return_when=asyncio.FIRST_EXCEPTION)
        print("FIRST_EXCEPTION:", repr(_done.pop().exception()), "| cancelling", len(_pending))
        for _task in _pending:
            _task.cancel()

        # A hard deadline: keep what's done, drop the slow optional call
        _api_a = asyncio.create_task(_api.get(0.1))
        _api_b = asyncio.create_task(_api.get(2))
        await asyncio.wait([_api_a, _api_b], timeout=1)
        print("timeout: API A returned", _api_a.result(), "| API B still running:", not _api_b.done())
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
