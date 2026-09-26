import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium", app_title="2 · asyncio basics")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 2 · asyncio basics: coroutines, tasks, futures

    > **marimo note:** marimo already runs an event loop, so cells can use `await` directly.
    > In a normal script you would write `asyncio.run(main())` once, at the entry point.
    """)
    return


@app.cell
def _():
    import asyncio
    import logging
    import threading
    import time

    import marimo as mo
    import requests

    from workshop.common import async_timed, delay

    return async_timed, asyncio, delay, logging, mo, requests, threading, time


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    `delay(seconds)` (book listing 2.6) is our stand-in for slow I/O: it prints, awaits `asyncio.sleep`, and returns
    the number of seconds. `@async_timed()` (listing 2.16) prints how long a coroutine took.

    ## A coroutine call doesn't run anything

    *Listings 2.1–2.5.* `async def` defines a coroutine function. Calling it returns a **coroutine object**, and nothing
    runs until something awaits it (or an event loop schedules it).
    """)
    return


@app.cell
async def _():
    async def coroutine_add_one(number: int) -> int:
        return number + 1

    _coroutine = coroutine_add_one(1)
    print(f"Calling it returns: {_coroutine!r}")
    _coroutine.close()  # never awaited; close it to silence the "never awaited" warning

    print(f"Awaiting it returns: {await coroutine_add_one(1)}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## `await` alone is still sequential

    *Listing 2.7.* `await` pauses **this** coroutine until the awaited one finishes, so two awaits in a row take
    the sum of their times.
    """)
    return


@app.cell
async def _(delay, time):
    _start = time.perf_counter()
    await delay(1)
    await delay(1)
    print(f"two awaits in a row: {time.perf_counter() - _start:.2f} s")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Tasks run concurrently

    *Listings 2.8, 2.9.* `asyncio.create_task()` schedules a coroutine on the loop **right away** and returns a `Task`.
    Three 1-second waits take about 1 second in total.
    """)
    return


@app.cell
async def _(asyncio, delay, time):
    _start = time.perf_counter()
    _tasks = [asyncio.create_task(delay(1)) for _ in range(3)]
    print(type(_tasks[0]))
    for _task in _tasks:
        await _task
    print(f"three tasks: {time.perf_counter() - _start:.2f} s")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Do other work while tasks wait

    *Listing 2.10.* While the delays run in the background, the current coroutine keeps working. Total time is about 3 s, not 5 s.
    """)
    return


@app.cell
async def _(asyncio, delay, time):
    async def hello_every_second():
        for _ in range(2):
            await asyncio.sleep(1)
            print("I'm running other code while I'm waiting!")

    _start = time.perf_counter()
    _first = asyncio.create_task(delay(3))
    _second = asyncio.create_task(delay(3))
    await hello_every_second()
    await _first
    await _second
    print(f"total: {time.perf_counter() - _start:.2f} s")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Cancel, time out, shield

    *Listings 2.11–2.13.*

    * `task.cancel()` raises `CancelledError` inside the task at its next `await`.
    * `asyncio.wait_for(aw, timeout)` and `async with asyncio.timeout(s)` (3.11+) cancel the work and raise `TimeoutError`.
    * `asyncio.shield(task)` lets a timeout fire **without** cancelling the task, for example to warn the user that a
      payment is taking a while but still let it finish.
    """)
    return


@app.cell
async def _(asyncio, delay):
    _long_task = asyncio.create_task(delay(10))
    await asyncio.sleep(1)
    _long_task.cancel()
    try:
        await _long_task
    except asyncio.CancelledError:
        print(f"cancelled: {_long_task.cancelled()}")

    _task = asyncio.create_task(delay(2))
    try:
        await asyncio.wait_for(_task, timeout=1)
    except TimeoutError:
        print(f"wait_for timed out, and the task was cancelled: {_task.cancelled()}")

    try:
        async with asyncio.timeout(1):
            await delay(2)
    except TimeoutError:
        print("asyncio.timeout() fired too")

    _task = asyncio.create_task(delay(2))
    try:
        _ = await asyncio.wait_for(asyncio.shield(_task), timeout=1)
    except TimeoutError:
        print("Taking longer than 1 s... still waiting (shielded, so not cancelled)")
        print(f"result: {await _task}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Futures: a value that arrives later

    *Listings 2.14, 2.15.* A `Future` starts "not done". Someone calls `set_result()` later, and every coroutine
    awaiting it wakes up. `Task` is a subclass of `Future`. Futures connect callback-style code (protocols,
    threads, C libraries) to `async`/`await`.
    """)
    return


@app.cell
async def _(asyncio):
    def make_request() -> asyncio.Future:
        future = asyncio.get_running_loop().create_future()

        async def set_future_value():
            await asyncio.sleep(1)
            future.set_result(42)

        asyncio.create_task(set_future_value())
        return future

    _future = make_request()
    print(f"done? {_future.done()}")
    print(f"value: {await _future}")
    print(f"done? {_future.done()}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Measuring concurrency with `@async_timed`

    *Listing 2.17.* `main` takes about as long as its slowest task (3 s), not the sum (5 s).
    """)
    return


@app.cell
async def _(async_timed, asyncio):
    @async_timed()
    async def timed_delay(seconds: int) -> int:
        await asyncio.sleep(seconds)
        return seconds

    @async_timed()
    async def timed_main():
        first = asyncio.create_task(timed_delay(2))
        second = asyncio.create_task(timed_delay(3))
        await first
        await second

    await timed_main()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Pitfall 1: CPU-bound code in a coroutine

    *Listings 2.18, 2.19.* asyncio has **one** thread. A coroutine that computes without awaiting holds the loop, so the
    other tasks, including I/O, can't even **start**. The 1 s delay below finishes after about 2.5 s, and every request
    a server is handling would stall the same way. Fix: move CPU work to processes (notebook 6).
    """)
    return


@app.cell
async def _(async_timed, asyncio, delay, time):
    @async_timed()
    async def cpu_bound_work() -> int:
        counter = 0
        for _ in range(60_000_000):
            counter += 1
        return counter

    _start = time.perf_counter()
    _cpu_one = asyncio.create_task(cpu_bound_work())
    _cpu_two = asyncio.create_task(cpu_bound_work())
    _io_task = asyncio.create_task(delay(1))  # scheduled last: can't start until both CPU tasks finish
    await asyncio.gather(_io_task, _cpu_one, _cpu_two)
    print(f"a 1 s delay took {time.perf_counter() - _start:.2f} s in total")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Pitfall 2: a blocking library in a coroutine

    *Listing 2.20.* `requests.get` blocks the thread, and therefore the loop, so these "concurrent" tasks run one by one.
    Fix: an async library (aiohttp/httpx, notebook 4) or `asyncio.to_thread` (notebook 7).

    > An `async def` with no `await` inside is suspicious.
    """)
    return


@app.cell
async def _(async_timed, asyncio, requests, time):
    @async_timed()
    async def get_example_status() -> int:
        return requests.get("https://www.example.com").status_code

    _start = time.perf_counter()
    await asyncio.gather(*(asyncio.create_task(get_example_status()) for _ in range(3)))
    print(f"3 'concurrent' blocking requests: {time.perf_counter() - _start:.2f} s")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Finding blocking code: debug mode

    *Listings 2.23, 2.24.* In debug mode (`asyncio.run(main(), debug=True)`, `python -X dev`, or `PYTHONASYNCIODEBUG=1`)
    asyncio logs every callback that holds the loop longer than `loop.slow_callback_duration` (default 100 ms).
    The demo runs a separate event loop in a background thread (marimo's own loop is already running) and captures the warnings.
    """)
    return


@app.cell
def _(asyncio, logging, threading, time):
    class _Collect(logging.Handler):
        def __init__(self):
            super().__init__()
            self.messages = []

        def emit(self, record):
            self.messages.append(record.getMessage())

    async def blocking_main():
        asyncio.get_running_loop().slow_callback_duration = 0.05
        time.sleep(0.2)  # blocks the loop for 200 ms

    _handler = _Collect()
    logging.getLogger("asyncio").addHandler(_handler)
    _thread = threading.Thread(target=lambda: asyncio.run(blocking_main(), debug=True))
    _thread.start()
    _thread.join()
    logging.getLogger("asyncio").removeHandler(_handler)
    print("\n".join(_handler.messages))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## call_soon: schedule a plain callback

    *Listing 2.22.* The loop can also run normal functions on its next iteration.
    """)
    return


@app.cell
async def _(asyncio, delay):
    asyncio.get_running_loop().call_soon(lambda: print("called on the next loop iteration"))
    await delay(1)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Modern: structured concurrency with TaskGroup (3.11+)

    A `TaskGroup` guarantees that no task outlives the `async with` block. If one task fails, its siblings are
    cancelled and the errors come back as an `ExceptionGroup` (catch it with `except*`). Prefer it to loose `create_task`
    calls in new code.
    """)
    return


@app.cell
async def _(asyncio, delay):
    async def fail_after(seconds: float):
        await asyncio.sleep(seconds)
        raise ValueError(f"failed after {seconds}s")

    async with asyncio.TaskGroup() as _tg:
        _a = _tg.create_task(delay(1))
        _b = _tg.create_task(delay(2))
    print(f"results: {_a.result()}, {_b.result()}")

    try:
        async with asyncio.TaskGroup() as _tg:
            _slow = _tg.create_task(delay(5))
            _tg.create_task(fail_after(1))
    except* ValueError as group:
        print(f"caught {group.exceptions}; sibling cancelled: {_slow.cancelled()}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Takeaways

    * `create_task` gives concurrency, and `await` on its own does not.
    * Put limits on waiting: `wait_for` / `asyncio.timeout`. Stop work with `cancel()`, and protect it with `shield()`.
    * Never block the loop: no CPU-heavy loops, no blocking libraries. Debug mode finds offenders.
    * Prefer `TaskGroup` for groups of tasks.
    """)
    return


if __name__ == "__main__":
    app.run()
