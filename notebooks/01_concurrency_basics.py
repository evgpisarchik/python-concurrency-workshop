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
    from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

    import marimo as mo
    import requests

    from workshop.common import timed
    from workshop.cpu import fib

    return ProcessPoolExecutor, ThreadPoolExecutor, fib, mo, os, requests, threading, timed


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## I/O-bound vs CPU-bound in one program

    *Book listing 1.1.* Fetch a page (**I/O**), format its headers (**CPU**). The timings show where the time goes.
    """)
    return


@app.cell
def _(requests, timed):
    with timed("I/O: HTTP request"):
        response = requests.get("https://www.example.com")  # waiting for the network

    with timed("CPU: format headers"):
        "\n".join(f"{k}: {v}" for k, v in response.headers.items())  # work on data in memory
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Processes and threads

    *Listings 1.2–1.4.* A **process** has its own memory (and its own GIL). **Threads** live inside a process and share its memory.
    """)
    return


@app.cell
def _(ProcessPoolExecutor, os, threading):
    print("this notebook's process:", os.getpid())

    with ProcessPoolExecutor(1) as _pool:
        print("a child process:        ", _pool.submit(os.getpid).result())

    _shared = []  # threads share their process's memory
    _thread = threading.Thread(target=_shared.append, args=("written by another thread",))
    _thread.start()
    _thread.join()
    print(_shared)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## CPU-bound work: threads don't help, processes do

    *Listings 1.5, 1.6.* The **GIL** allows only one thread at a time to run Python bytecode. Two CPU-bound threads take
    about as long as running the work sequentially. Two processes run truly in parallel.

    > On the free-threaded build (3.14t) the thread version gets faster too: notebook 15 measures it. Subinterpreters
    > (notebook 16) are a third way to run Python in parallel.
    """)
    return


@app.cell
def _(ProcessPoolExecutor, ThreadPoolExecutor, fib, timed):
    with timed("sequential"):
        fib(33)
        fib(33)

    with ThreadPoolExecutor(2) as _pool, timed("2 threads  (the GIL: no speedup)"):
        list(_pool.map(fib, [33, 33]))

    with ProcessPoolExecutor(2) as _pool:
        list(_pool.map(fib, [33, 33]))  # the first run also starts the workers, so time the second
        with timed("2 processes (real parallelism)"):
            list(_pool.map(fib, [33, 33]))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## I/O-bound work: threads DO help

    *Listings 1.7, 1.8.* A blocking socket call releases the GIL while it waits, so other threads can run.
    """)
    return


@app.cell
def _(ThreadPoolExecutor, requests, timed):
    _urls = ["https://www.example.com"] * 4

    with timed("4 requests, one by one"):
        [requests.get(url) for url in _urls]

    with ThreadPoolExecutor(4) as _pool, timed("4 requests, 4 threads"):
        list(_pool.map(requests.get, _urls))
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
