import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium", app_title="18 · Newer APIs")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 18 · Newer APIs: queue shutdown, barriers, bounded `map`, stopping pools, start methods

    Smaller additions from 3.11–3.14 that change how you write everyday concurrent code:

    | API | Since | Replaces |
    |---|---|---|
    | `Queue.shutdown()` (asyncio and `queue`) | 3.13 | sentinel values, cancelling workers |
    | `async for t in asyncio.as_completed(...)` | 3.13 | guessing which awaitable finished |
    | `asyncio.Barrier` | 3.11 | hand-made counters + `Event` |
    | `Executor.map(..., buffersize=N)` | 3.14 | submitting in hand-made batches |
    | `ProcessPoolExecutor.terminate_workers()` / `kill_workers()` | 3.14 | waiting for stuck workers, `os.kill` |
    | `forkserver` is the default start method on Linux | 3.14 | `fork` |
    """)
    return


@app.cell
def _():
    import asyncio
    import itertools
    import multiprocessing
    import time
    from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

    import marimo as mo

    from workshop import start_methods
    from workshop.common import timed

    return (
        ProcessPoolExecutor,
        ThreadPoolExecutor,
        asyncio,
        itertools,
        mo,
        multiprocessing,
        start_methods,
        time,
        timed,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## `Queue.shutdown()`: workers stop by themselves (3.13)

    In notebook 12, workers loop forever and we cancel them once `join()` returns. `shutdown()` is the cleaner way:

    * `queue.shutdown()`: no more `put()`. Workers **finish what's queued**, then `get()` raises `QueueShutDown`
    * `queue.shutdown(immediate=True)`: drop what's queued, and `get()` raises right away

    The same API exists on `queue.Queue` for threads (`queue.ShutDown`).
    """)
    return


@app.cell
async def _(asyncio):
    async def worker(jobs: asyncio.Queue) -> list:
        done = []
        try:
            while True:
                done.append(await jobs.get())
        except asyncio.QueueShutDown:  # raised once the queue is shut down and empty
            return done

    _jobs = asyncio.Queue()
    _worker = asyncio.create_task(worker(_jobs))
    for _i in range(5):
        await _jobs.put(_i)
    _jobs.shutdown()  # no more jobs: the worker finishes the queue, then stops
    print("the worker did these jobs and stopped by itself:", await _worker)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## `as_completed` yields the original tasks (3.13)

    Notebook 4's `for coro in as_completed(...)` gives you *new* awaitables, so you can't tell which request finished
    without returning an id from each one. Iterating with `async for` yields **the tasks you passed in**.
    """)
    return


@app.cell
async def _(asyncio):
    _fast = asyncio.create_task(asyncio.sleep(0.1, result="fast"))
    _slow = asyncio.create_task(asyncio.sleep(0.2, result="slow"))
    async for _task in asyncio.as_completed([_slow, _fast]):
        print(_task.result(), "finished. Is it our task?", _task in (_fast, _slow))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## `asyncio.Barrier`: wait until everyone is ready (3.11)

    `Barrier(n)`: each task calls `await barrier.wait()`, and all of them continue together once `n` have arrived. Useful for
    starting a load test at the same moment, or for phases where every worker must finish step 1 before any starts step 2.
    `threading.Barrier` is the thread version.
    """)
    return


@app.cell
async def _(asyncio):
    _barrier = asyncio.Barrier(3)

    async def client(name: str, warm_up: float):
        await asyncio.sleep(warm_up)  # each client needs a different time to get ready
        print(name, "ready")
        await _barrier.wait()
        print(name, "go!")

    await asyncio.gather(client("A", 0.1), client("B", 0.2), client("C", 0.3))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## `Executor.map(..., buffersize=N)`: don't read all inputs up front (3.14)

    `map()` used to **submit everything immediately**: a generator of 10 million lines became 10 million futures in
    memory before the first result came back. `buffersize=N` keeps at most N tasks in flight and pulls the next input only
    when a result is consumed, so it even works on an **endless** input (without `buffersize` this cell would never
    finish).
    """)
    return


@app.cell
def _(ThreadPoolExecutor, itertools):
    with ThreadPoolExecutor(4) as _pool:
        _results = _pool.map(abs, itertools.count(), buffersize=8)  # an endless input
        print("first results:", [next(_results) for _ in range(5)])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Stop a process pool now: `terminate_workers()` / `kill_workers()` (3.14)

    `shutdown(cancel_futures=True)` cancels **pending** work but waits for work that's **already running**. A stuck worker
    keeps your program alive. `terminate_workers()` (SIGTERM) and `kill_workers()` (SIGKILL) stop the workers now: running
    jobs fail with `BrokenProcessPool`, waiting ones are cancelled.
    """)
    return


@app.cell
def _(ProcessPoolExecutor, time, timed):
    _pool = ProcessPoolExecutor(1)
    _pool.submit(int).result()  # wait until the worker has started
    _job = _pool.submit(time.sleep, 60)
    time.sleep(0.5)  # the job is now running

    with timed("stopping a running sleep(60)"):
        _pool.terminate_workers()
        print(repr(_job.exception()))  # waits until the job is finished
    _pool.shutdown()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Start methods: `fork`, `spawn`, `forkserver`

    How a new process gets its Python:

    | method | how | the child sees | default on |
    |---|---|---|---|
    | `fork` | copy of the parent right now | the parent's current globals, locks and **only the calling thread** | Linux ≤ 3.13 |
    | `spawn` | fresh interpreter, imports your module | module state as imported | macOS, Windows |
    | `forkserver` | forked from a clean helper process | module state as imported | **Linux 3.14+** |

    `fork` in a program that has threads can copy a lock another thread was holding, and the child deadlocks on it.
    That's why 3.12 started warning and 3.14 switched Linux to `forkserver`. Code that **relied on `fork`** now breaks
    on Linux, exactly as it always did on macOS:

    * globals set up at runtime in the parent aren't there in the child
    * arguments and functions must be picklable, so no lambdas or notebook-cell functions (notebook 6)

    The parent below changes a module global, then asks a child started with each method what it sees. (In marimo, which
    runs threads, `fork` also prints a `DeprecationWarning`. `fork` doesn't exist on Windows.)
    """)
    return


@app.cell
def _(multiprocessing, start_methods):
    def child_sees(method: str) -> str:
        context = multiprocessing.get_context(method)
        receiver, sender = context.Pipe()
        child = context.Process(target=start_methods.send_state, args=(sender,))
        child.start()
        child.join()
        return receiver.recv()

    print("default start method here:", multiprocessing.get_start_method())
    start_methods.STATE["config"] = "CHANGED at runtime in the parent"
    print("fork:       child sees", child_sees("fork"))
    print("spawn:      child sees", child_sees("spawn"))
    print("forkserver: child sees", child_sees("forkserver"))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Pass state to workers explicitly (arguments, the pool's `initializer=`/`initargs=`) instead of relying on `fork` to
    copy it. The code then works with every start method, on every OS.

    ## Takeaways

    * Stop consumers with `Queue.shutdown()`, not sentinels or `cancel()`.
    * `async for task in asyncio.as_completed(...)` tells you *which* task finished.
    * `Barrier` lines tasks up. `buffersize=` keeps `Executor.map` from reading a huge input all at once.
    * `terminate_workers()` / `kill_workers()` get you out of a stuck process pool.
    * Don't depend on `fork`: pass state explicitly and keep worker functions importable.
    """)
    return


if __name__ == "__main__":
    app.run()
