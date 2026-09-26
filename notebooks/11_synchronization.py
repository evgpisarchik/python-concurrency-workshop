import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium", app_title="11 · Synchronization")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 11 · Synchronization: races, Lock, Semaphore, Event, Condition

    asyncio runs on one thread, but races still happen: **any `await` is a point where other tasks can run and change
    shared state.** Code *between* two awaits is effectively atomic.

    > asyncio primitives are **not thread-safe**. Use `threading.*` for threads and `multiprocessing.*` for processes.
    """)
    return


@app.cell
def _():
    import asyncio
    import time
    from enum import Enum

    import aiohttp
    import marimo as mo

    from workshop.testserver import serve

    return Enum, aiohttp, asyncio, mo, serve, time


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## When asyncio code races

    *Listings 11.1, 11.2.* 100 tasks each increment a counter. When the read-modify-write has **no `await` inside** it
    never races. With an `await` between the read and the write, every task reads the same old value and updates get lost.
    """)
    return


@app.cell
async def _(asyncio):
    _state = {"counter": 0}

    async def increment_safely():
        await asyncio.sleep(0.01)
        _state["counter"] = _state["counter"] + 1  # no await between read and write

    async def increment_racy():
        value = _state["counter"]  # read
        await asyncio.sleep(0.01)  # other tasks run here and read the same value
        _state["counter"] = value + 1  # write back a stale value

    await asyncio.gather(*(increment_safely() for _ in range(100)))
    print(f"no await inside: counter = {_state['counter']} (expected 100)")

    _state["counter"] = 0
    await asyncio.gather(*(increment_racy() for _ in range(100)))
    print(f"await inside:    counter = {_state['counter']} (expected 100)")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Lock

    *Listings 11.3–11.5.* A realistic race: while we broadcast to every user, one of them disconnects, and its socket gets
    closed before its `send()` runs. A lock makes "broadcast" and "remove user" mutually exclusive.
    """)
    return


@app.cell
async def _(asyncio):
    class MockSocket:
        def __init__(self):
            self.closed = False

        async def send(self, message: str):
            if self.closed:
                raise ConnectionError("socket is closed")
            await asyncio.sleep(0.5)

    async def broadcast_demo(use_lock: bool):
        users = {name: MockSocket() for name in ("John", "Terry", "Graham", "Eric")}
        lock = asyncio.Lock()

        async def user_disconnect(username: str):
            if use_lock:
                async with lock:
                    users.pop(username).closed = True
            else:
                users.pop(username).closed = True

        async def message_all_users():
            if use_lock:
                async with lock:
                    await asyncio.gather(*(sock.send(f"Hello {user}") for user, sock in users.items()))
            else:
                await asyncio.gather(*(sock.send(f"Hello {user}") for user, sock in users.items()))

        try:
            await asyncio.gather(message_all_users(), user_disconnect("Eric"))
            return f"ok, users left: {list(users)}"
        except ConnectionError as error:
            return f"FAILED: {error}"

    print(f"without lock: {await broadcast_demo(use_lock=False)}")
    print(f"with lock:    {await broadcast_demo(use_lock=True)}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Semaphore: at most N at a time

    *Listings 11.6, 11.7.* A semaphore limits concurrency, for example to respect an API's limit or to protect a database.
    The test server counts how many requests were **in flight at once**.
    """)
    return


@app.cell
async def _(aiohttp, asyncio, serve, time):
    async def get_limited(session: aiohttp.ClientSession, url: str, semaphore: asyncio.Semaphore) -> int:
        async with semaphore:
            async with session.get(url) as response:
                return response.status

    async with serve() as _base, aiohttp.ClientSession() as _session:
        for _limit in (10, 50):
            await _session.post(f"{_base}/stats/reset")
            _semaphore = asyncio.Semaphore(_limit)
            _start = time.perf_counter()
            await asyncio.gather(*(get_limited(_session, f"{_base}/delay?seconds=0.1", _semaphore) for _ in range(200)))
            _stats = await (await _session.get(f"{_base}/stats")).json()
            print(
                f"Semaphore({_limit}): 200 requests in {time.perf_counter() - _start:.2f} s, server saw at most {_stats['max_in_flight']} at once"
            )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *Listings 11.8, 11.9.* **Pitfall:** one extra `release()` silently raises the limit: `Semaphore(2)` now admits 3.
    `BoundedSemaphore` raises `ValueError` instead.
    """)
    return


@app.cell
async def _(asyncio):
    async def max_concurrent(semaphore, tasks: int) -> int:
        state = {"now": 0, "max": 0}

        async def worker():
            async with semaphore:
                state["now"] += 1
                state["max"] = max(state["max"], state["now"])
                await asyncio.sleep(0.1)
                state["now"] -= 1

        await asyncio.gather(*(worker() for _ in range(tasks)))
        return state["max"]

    _semaphore = asyncio.Semaphore(2)
    _semaphore.release()  # a stray release
    print(f"Semaphore(2) after an extra release lets {await max_concurrent(_semaphore, 5)} in at once")

    _bounded = asyncio.BoundedSemaphore(2)
    try:
        _bounded.release()
    except ValueError as error:
        print(f"BoundedSemaphore: ValueError: {error}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Event: "it happened"

    *Listing 11.10.* Any number of coroutines `await event.wait()` until someone calls `event.set()`. Typical uses: "config
    loaded", "connection ready", "shutdown requested".
    """)
    return


@app.cell
async def _(asyncio, time):
    async def worker(name: str, ready: asyncio.Event, start: float):
        await ready.wait()
        print(f"{name} started at {time.perf_counter() - start:.2f} s")

    _ready = asyncio.Event()
    _start = time.perf_counter()
    asyncio.get_running_loop().call_later(1.0, _ready.set)  # e.g. a connection finishes initializing
    await asyncio.gather(*(worker(f"worker-{i}", _ready, _start) for i in range(3)))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *Listing 11.13.* **Pitfall:** an Event is a flag, not a counter. Calling `set()` while it's already set does nothing,
    so triggers that arrive while the workers are busy are **lost**. If every trigger must be handled, use a queue (notebook 12).
    """)
    return


@app.cell
async def _(asyncio):
    _event = asyncio.Event()
    _handled = {"count": 0}

    async def trigger_every(interval: float, times: int):
        for _ in range(times):
            _event.set()
            await asyncio.sleep(interval)

    async def slow_handler():
        while True:
            await _event.wait()
            _event.clear()
            _handled["count"] += 1
            await asyncio.sleep(0.5)  # busy: triggers arriving now get merged

    _handler = asyncio.create_task(slow_handler())
    await trigger_every(0.1, 20)
    _handler.cancel()
    print(f"triggered 20 times, handled {_handled['count']} times")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Condition: lock + notification, wait for a state

    *Listings 11.14, 11.15.* `Condition.wait_for(predicate)` sleeps until the predicate becomes true. It releases the lock
    while waiting and gets woken by `notify_all()`. Here, queries submitted before a connection is ready wait until it
    reaches `INITIALIZED`, with no polling.
    """)
    return


@app.cell
async def _(Enum, asyncio):
    class ConnectionState(Enum):
        WAIT_INIT = 0
        INITIALIZING = 1
        INITIALIZED = 2

    class Connection:
        def __init__(self):
            self._state = ConnectionState.WAIT_INIT
            self._condition = asyncio.Condition()

        async def initialize(self):
            await self._change_state(ConnectionState.INITIALIZING)
            await asyncio.sleep(1)  # connection start-up
            await self._change_state(ConnectionState.INITIALIZED)

        async def execute(self, query: str):
            async with self._condition:
                await self._condition.wait_for(lambda: self._state is ConnectionState.INITIALIZED)
                print(f"running {query!r}")

        async def _change_state(self, state: ConnectionState):
            async with self._condition:
                print(f"state: {self._state.name} -> {state.name}")
                self._state = state
                self._condition.notify_all()

    _connection = Connection()
    _queries = [asyncio.create_task(_connection.execute(q)) for q in ("select * from a", "select * from b")]
    await _connection.initialize()
    await asyncio.gather(*_queries)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Choosing a primitive

    | Need | Use |
    |---|---|
    | Only one task at a time in a critical section | `asyncio.Lock` |
    | At most N at a time | `asyncio.Semaphore` / `BoundedSemaphore` |
    | Wake everyone once something happened | `asyncio.Event` |
    | Wait until shared state reaches a condition | `asyncio.Condition` |
    | Every signal must be handled, in order | `asyncio.Queue` |
    """)
    return


if __name__ == "__main__":
    app.run()
