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
    import subprocess
    import sys

    import marimo as mo
    import requests

    from workshop.common import async_timed, delay, timed
    from workshop.cpu import count

    return async_timed, asyncio, count, delay, mo, requests, subprocess, sys, timed


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    `delay(seconds)` (book listing 2.6) is our stand-in for slow I/O: it prints, awaits `asyncio.sleep`, and returns
    the number of seconds. `timed(label)` prints how long a block took.

    ## A coroutine call doesn't run anything

    *Listings 2.1–2.5.* `async def` defines a coroutine function. Calling it returns a **coroutine object**, and nothing
    runs until something awaits it (or an event loop schedules it).
    """)
    return


@app.cell
async def _():
    async def add_one(number: int) -> int:
        return number + 1

    _coroutine = add_one(1)
    print("calling it returns:", _coroutine)
    _coroutine.close()  # never awaited: close it to silence the warning

    print("awaiting it returns:", await add_one(1))
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
async def _(delay, timed):
    with timed("two awaits in a row"):
        await delay(1)
        await delay(1)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Tasks run concurrently

    *Listings 2.8–2.10.* `asyncio.create_task()` schedules a coroutine on the loop **right away** and returns a `Task`.
    Two 1-second waits take about 1 second in total, and the current coroutine keeps running while they wait.
    """)
    return


@app.cell
async def _(asyncio, delay, timed):
    with timed("two tasks"):
        _first = asyncio.create_task(delay(1))
        _second = asyncio.create_task(delay(1))
        print("doing other work while the tasks wait")
        await _first
        await _second
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Cancel, time out, shield

    *Listings 2.11–2.13.*

    * `task.cancel()` raises `CancelledError` inside the task at its next `await`.
    * `async with asyncio.timeout(s)` (3.11+) and `asyncio.wait_for(aw, timeout)` cancel the work and raise `TimeoutError`.
    * `asyncio.shield(task)` lets a timeout fire **without** cancelling the task, for example to warn the user that a
      payment is taking a while but still let it finish.
    """)
    return


@app.cell
async def _(asyncio):
    _task = asyncio.create_task(asyncio.sleep(10))
    await asyncio.sleep(0.1)
    _task.cancel()
    try:
        await _task
    except asyncio.CancelledError:
        print("task cancelled")

    try:
        async with asyncio.timeout(1):
            await asyncio.sleep(2)
    except TimeoutError:
        print("timed out after 1 s")

    _payment = asyncio.create_task(asyncio.sleep(2, result="payment done"))
    try:
        await asyncio.wait_for(asyncio.shield(_payment), timeout=1)
    except TimeoutError:
        print("taking longer than 1 s, still waiting...")
        print(await _payment)
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
    _loop = asyncio.get_running_loop()
    _future = _loop.create_future()
    _loop.call_later(1, _future.set_result, 42)  # someone else sets the result in 1 s

    print("done?", _future.done())
    print("value:", await _future)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Measuring concurrency with `@async_timed`

    *Listings 2.16, 2.17.* `@async_timed()` prints when a coroutine starts and how long it ran. `main` takes about as long
    as its slowest task (2 s), not the sum (3 s).
    """)
    return


@app.cell
async def _(async_timed, asyncio):
    @async_timed()
    async def wait(seconds: int):
        await asyncio.sleep(seconds)

    @async_timed()
    async def main():
        await asyncio.gather(wait(1), wait(2))

    await main()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Pitfall 1: CPU-bound code in a coroutine

    *Listings 2.18, 2.19.* asyncio has **one** thread. A coroutine that computes without awaiting holds the loop, so the
    other tasks, including I/O, can't even **start**. The 1 s delay below finishes only after the counting is done, and
    every request a server is handling would stall the same way. Fix: move CPU work to processes (notebook 6).
    """)
    return


@app.cell
async def _(asyncio, count, delay, timed):
    async def cpu_work():
        count(50_000_000)  # no await inside: holds the loop

    with timed("a 1 s delay next to CPU work"):
        await asyncio.gather(cpu_work(), delay(1))
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
async def _(asyncio, requests, timed):
    async def get_status() -> int:
        return requests.get("https://www.example.com").status_code  # blocks the loop

    with timed("3 'concurrent' blocking requests"):
        await asyncio.gather(get_status(), get_status(), get_status())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Finding blocking code: debug mode

    *Listings 2.23, 2.24.* In debug mode (`asyncio.run(main(), debug=True)`, `python -X dev`, or `PYTHONASYNCIODEBUG=1`)
    asyncio logs every callback that holds the loop longer than 100 ms. `workshop/children/blocking_loop.py` blocks for 200 ms:
    """)
    return


@app.cell
def _(subprocess, sys):
    _result = subprocess.run([sys.executable, "-m", "workshop.children.blocking_loop"], capture_output=True, text=True)
    print(_result.stderr)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## call_soon: schedule a plain callback

    *Listing 2.22.* The loop can also run normal functions on its next iteration.
    """)
    return


@app.cell
async def _(asyncio):
    asyncio.get_running_loop().call_soon(print, "called on the next loop iteration")
    await asyncio.sleep(0)
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
async def _(asyncio):
    async def fail():
        await asyncio.sleep(1)
        raise ValueError("failed")

    try:
        async with asyncio.TaskGroup() as _tg:
            _slow = _tg.create_task(asyncio.sleep(5))
            _tg.create_task(fail())
    except* ValueError as _group:
        print("caught", _group.exceptions)
        print("the slow sibling was cancelled:", _slow.cancelled())
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
