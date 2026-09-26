import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium", app_title="1 · Concurrency basics")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 1 · Concurrency basics: processes, threads and the GIL

    Before picking a tool, answer one question for each part of your program:
    **is it waiting (I/O-bound) or computing (CPU-bound)?**

    | | I/O-bound | CPU-bound |
    |---|---|---|
    | Time goes to | network, disk, database | the processor |
    | asyncio | ✅ many waits on one thread | ❌ |
    | threads | ✅ the GIL is released while waiting | ❌ (except C code that releases the GIL) |
    | processes | ✅ (heavier) | ✅ one GIL per process |
    """)
    return


@app.cell
def _():
    import os
    import threading
    import time
    from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

    import marimo as mo
    import requests

    from workshop.cpu import fib
    from workshop.nb import Timeline

    return (
        ProcessPoolExecutor,
        ThreadPoolExecutor,
        Timeline,
        fib,
        mo,
        os,
        requests,
        threading,
        time,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## I/O-bound vs CPU-bound in one program

    *Book listing 1.1.* Fetch a page (**I/O**), format its headers (**CPU**). The timings show where the time goes.
    """)
    return


@app.cell
def _(requests, time):
    _start = time.perf_counter()
    _response = requests.get("https://www.example.com")  # I/O: waiting for the network
    _io = time.perf_counter() - _start

    _start = time.perf_counter()
    _formatted = "\n".join(f"{k}: {v}" for k, v in _response.headers.items())  # CPU: work on data in memory
    _cpu = time.perf_counter() - _start

    print(f"I/O  (HTTP request):   {_io * 1000:8.2f} ms")
    print(f"CPU  (format headers): {_cpu * 1000:8.2f} ms")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Processes and threads

    *Listings 1.2–1.4.* A **process** has its own memory (and its own GIL). **Threads** live inside a process and share its memory.
    """)
    return


@app.cell
def _(ProcessPoolExecutor, Timeline, os, threading):
    print(f"This notebook runs in process {os.getpid()} with {threading.active_count()} thread(s)")

    _timeline = Timeline()
    _thread = threading.Thread(target=lambda: _timeline.log("hello from a second thread"), name="worker-thread")
    _thread.start()
    _timeline.log("main thread keeps running while the worker runs")
    _thread.join()  # wait for the worker to finish
    _timeline.show()

    # A child process gets its own pid. The function we send (os.getpid) must be importable by the child.
    with ProcessPoolExecutor(max_workers=1) as _pool:
        print(f"A child process has pid {_pool.submit(os.getpid).result()}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## CPU-bound work: threads don't help, processes do

    *Listings 1.5, 1.6.* The **GIL** allows only one thread at a time to run Python bytecode. Two CPU-bound threads take
    about as long as running the work sequentially. Two processes run truly in parallel.

    > On a free-threaded build (`uv run --python 3.14t marimo edit ...`) the thread version gets faster too.
    """)
    return


@app.cell
def _(ProcessPoolExecutor, ThreadPoolExecutor, fib, mo, time):
    N = 30
    _start = time.perf_counter()
    fib(N), fib(N)
    _sequential = time.perf_counter() - _start

    with ThreadPoolExecutor(2) as _threads:
        _start = time.perf_counter()
        list(_threads.map(fib, [N, N]))
        _with_threads = time.perf_counter() - _start

    with ProcessPoolExecutor(2) as _processes:
        _processes.submit(int).result()  # start the workers first, so start-up isn't timed
        _start = time.perf_counter()
        list(_processes.map(fib, [N, N]))
        _with_processes = time.perf_counter() - _start

    mo.md(f"""
    | fib({N}) twice | seconds |
    |---|---|
    | sequential | {_sequential:.2f} |
    | 2 threads | {_with_threads:.2f} ← the GIL: no speedup |
    | 2 processes | {_with_processes:.2f} ← real parallelism |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## I/O-bound work: threads DO help

    *Listings 1.7, 1.8.* A blocking socket call releases the GIL while it waits, so other threads can run.
    """)
    return


@app.cell
def _(ThreadPoolExecutor, requests, time):
    def read_example() -> int:
        return requests.get("https://www.example.com").status_code

    _start = time.perf_counter()
    [read_example() for _ in range(4)]
    _sequential = time.perf_counter() - _start

    with ThreadPoolExecutor(4) as _threads:
        _start = time.perf_counter()
        list(_threads.map(lambda _: read_example(), range(4)))
        _with_threads = time.perf_counter() - _start

    print(f"4 requests sequentially: {_sequential:.2f} s")
    print(f"4 requests in 4 threads: {_with_threads:.2f} s")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Where asyncio fits

    Threads give I/O concurrency, but each one costs memory and OS scheduling, and shared state needs locks.
    **asyncio** gets I/O concurrency on **one thread**. It uses non-blocking sockets plus an **event loop** that asks
    the OS which sockets are ready and resumes the code waiting on them:

    ```
                   ┌──────────── event loop (1 thread) ────────────┐
     task A ──run──┤ await socket ─► paused   ...ready! ─► resume   │
     task B ───────┤        run ─► await db ─► paused  ...          │
     task C ───────┤               run ─► done                      │
                   └────────────────────────────────────────────────┘
    ```

    Notebook 3 builds that loop from raw sockets, and notebook 14 builds it from scratch.
    """)
    return


if __name__ == "__main__":
    app.run()
