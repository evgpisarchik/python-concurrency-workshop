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

    import marimo as mo

    from workshop.common import timed

    return asyncio, mo, timed


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## A race across `await`, fixed with a Lock

    *Listings 11.1–11.5.* 100 tasks each increment a counter. With an `await` between the read and the write, every task
    reads the same old value and updates get lost. An `asyncio.Lock` lets only one task at a time run the
    read-await-write section.
    """)
    return


@app.cell
async def _(asyncio):
    class Counter:
        def __init__(self):
            self.value = 0
            self._lock = asyncio.Lock()

        async def increment(self):
            value = self.value  # read
            await asyncio.sleep(0.01)  # other tasks run here and read the same value
            self.value = value + 1  # write back a stale value

        async def increment_with_lock(self):
            async with self._lock:
                await self.increment()

    _counter = Counter()
    await asyncio.gather(*(_counter.increment() for _ in range(100)))
    print("without a lock: counter =", _counter.value)

    _counter = Counter()
    await asyncio.gather(*(_counter.increment_with_lock() for _ in range(100)))
    print("with a lock:    counter =", _counter.value)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Semaphore: at most N at a time

    *Listings 11.6, 11.7.* A semaphore limits concurrency, for example to respect an API's limit or to protect a database.
    `ConcurrencyMeter` runs tasks through a semaphore and records how many were inside at once.
    """)
    return


@app.cell
def _(asyncio):
    class ConcurrencyMeter:
        def __init__(self, semaphore: asyncio.Semaphore):
            self.semaphore = semaphore
            self.inside = 0
            self.peak = 0

        async def run(self, tasks: int) -> int:
            """Run `tasks` tasks through the semaphore and return the most that were inside at once."""
            await asyncio.gather(*(self._task() for _ in range(tasks)))
            return self.peak

        async def _task(self):
            async with self.semaphore:
                self.inside += 1
                self.peak = max(self.peak, self.inside)
                await asyncio.sleep(0.1)  # e.g. an API call
                self.inside -= 1

    return (ConcurrencyMeter,)


@app.cell
async def _(ConcurrencyMeter, asyncio, timed):
    with timed("200 tasks through Semaphore(10)"):
        print("at most at once:", await ConcurrencyMeter(asyncio.Semaphore(10)).run(tasks=200))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *Listings 11.8, 11.9.* **Pitfall:** one extra `release()` silently raises the limit: `Semaphore(2)` now admits 3.
    `BoundedSemaphore` raises `ValueError` instead.
    """)
    return


@app.cell
async def _(ConcurrencyMeter, asyncio):
    _semaphore = asyncio.Semaphore(2)
    _semaphore.release()  # a stray release
    print("Semaphore(2) after an extra release admits", await ConcurrencyMeter(_semaphore).run(tasks=5))

    try:
        asyncio.BoundedSemaphore(2).release()
    except ValueError as _error:
        print("BoundedSemaphore:", repr(_error))
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
async def _(asyncio, timed):
    _ready = asyncio.Event()

    async def worker(name: str):
        await _ready.wait()
        print(name, "started")

    asyncio.get_running_loop().call_later(1, _ready.set)  # e.g. a connection finishes initializing
    with timed("the workers waited"):
        await asyncio.gather(worker("A"), worker("B"), worker("C"))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *Listing 11.13.* **Pitfall:** an Event is a flag, not a counter. Calling `set()` while it's already set does nothing,
    so triggers that arrive while the handler is busy are **lost**. If every trigger must be handled, use a queue (notebook 12).
    """)
    return


@app.cell
async def _(asyncio):
    class SlowHandler:
        def __init__(self):
            self.trigger = asyncio.Event()
            self.handled = 0

        async def run(self):
            while True:
                await self.trigger.wait()
                self.trigger.clear()
                self.handled += 1
                await asyncio.sleep(0.5)  # busy: triggers arriving now get merged

    _handler = SlowHandler()
    _task = asyncio.create_task(_handler.run())
    for _ in range(20):
        _handler.trigger.set()
        await asyncio.sleep(0.1)
    _task.cancel()
    print("triggered 20 times, handled", _handler.handled, "times")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Condition: lock + notification, wait for a state

    *Listings 11.14, 11.15.* `Condition.wait_for(predicate)` sleeps until the predicate becomes true. It releases the lock
    while waiting and gets woken by `notify_all()`. Here, queries submitted before a connection is ready wait until it
    is connected, with no polling.
    """)
    return


@app.cell
async def _(asyncio):
    class Connection:
        def __init__(self):
            self.ready = False
            self._condition = asyncio.Condition()

        async def connect(self):
            await asyncio.sleep(1)  # connection start-up
            async with self._condition:
                self.ready = True
                print("connected")
                self._condition.notify_all()

        async def query(self, sql: str):
            async with self._condition:
                await self._condition.wait_for(lambda: self.ready)
                print("running", sql)

    _connection = Connection()
    await asyncio.gather(_connection.query("select 1"), _connection.query("select 2"), _connection.connect())
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
