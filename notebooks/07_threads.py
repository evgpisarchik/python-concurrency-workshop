import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium", app_title="7 · Threads")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 7 · Threads: blocking libraries, locks, and bridging to asyncio

    Use threads when you must call **blocking code** (requests, boto3, psycopg2, a legacy SDK) or **C code that releases
    the GIL** (hashlib, zlib, numpy). Threads share memory, so shared state needs locks.
    """)
    return


@app.cell
def _():
    import asyncio
    import os
    import socket
    import threading
    import time
    from concurrent.futures import ThreadPoolExecutor

    import marimo as mo
    import requests

    from workshop.common import timed
    from workshop.cpu import hash_password
    from workshop.nb import start_server, stop_server

    return (
        ThreadPoolExecutor,
        asyncio,
        hash_password,
        mo,
        os,
        requests,
        socket,
        start_server,
        stop_server,
        threading,
        time,
        timed,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Thread per connection

    *Listings 7.1, 7.2.* The simplest way to make blocking code concurrent is to give each connection its own thread, so a
    blocked `recv()` only blocks that thread. Python can't kill threads, so shutting down means making each thread **exit
    by itself**: `socket.shutdown()` makes the blocked `recv()` return `b""`.
    """)
    return


@app.cell
def _(socket, threading):
    def echo(connection: socket.socket):
        while data := connection.recv(1024):  # blocks only this thread
            connection.sendall(data)

    _connections = [socket.socketpair() for _ in range(3)]  # (server side, client side)
    _threads = [threading.Thread(target=echo, args=(server_side,)) for server_side, _ in _connections]
    for _thread in _threads:
        _thread.start()

    for _i, (_, _client_side) in enumerate(_connections):
        _client_side.sendall(f"hello {_i}".encode())
        print(_client_side.recv(1024))

    for _server_side, _ in _connections:
        _server_side.shutdown(socket.SHUT_RDWR)  # recv() returns b"": the thread exits
    for _thread in _threads:
        _thread.join()
    print("all threads finished")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## A blocking library from threads

    *Listings 7.3–7.7.* 20 blocking `requests.get` calls to an endpoint that takes 0.2 s: one by one, on a thread pool, and
    with `asyncio.to_thread(fn, *args)`, the recommended way to call blocking code from async code. (`to_thread` uses
    the loop's default pool of `min(32, cpu_count + 4)` threads; `loop.run_in_executor(pool, ...)` takes your own pool.)
    """)
    return


@app.cell
async def _(ThreadPoolExecutor, asyncio, requests, start_server, stop_server, timed):
    _server = start_server(["-m", "workshop.testserver", "--port", "8702"], 8702)
    _urls = ["http://127.0.0.1:8702/delay?seconds=0.2"] * 20

    with timed("one by one"):
        [requests.get(url) for url in _urls]

    with ThreadPoolExecutor(20) as _pool, timed("ThreadPoolExecutor"):
        list(_pool.map(requests.get, _urls))

    with timed("asyncio.to_thread"):
        await asyncio.gather(*(asyncio.to_thread(requests.get, url) for url in _urls))

    stop_server(_server)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Shared state needs a lock

    *Listing 7.8.* 100 threads each count a finished job. `done += 1` is read-modify-write, so it is guarded with
    `threading.Lock`. (asyncio locks are **not** thread-safe. Use the `threading` ones for threads.)
    """)
    return


@app.cell
async def _(asyncio, threading, time):
    class JobCounter:
        def __init__(self):
            self.done = 0
            self._lock = threading.Lock()

        def run_job(self):
            time.sleep(0.1)  # blocking work
            with self._lock:
                self.done += 1

    _counter = JobCounter()
    await asyncio.gather(*(asyncio.to_thread(_counter.run_job) for _ in range(100)))
    print("jobs done:", _counter.done)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Re-entrant locks and deadlocks

    *Listings 7.9, 7.10.* A thread that holds a `Lock` and tries to take it again (for example, a recursive function)
    waits for itself forever. `RLock` lets the thread that already owns the lock acquire it again.
    """)
    return


@app.cell
def _(threading):
    _lock = threading.Lock()
    with _lock:
        print("Lock:  acquired again by the same thread?", _lock.acquire(timeout=0.5))  # would wait forever

    _rlock = threading.RLock()
    with _rlock:
        print("RLock: acquired again by the same thread?", _rlock.acquire(timeout=0.5))
        _rlock.release()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *Listing 7.11.* The classic deadlock: thread 1 holds A and waits for B, while thread 2 holds B and waits for A.
    Fix it by always acquiring locks in the **same global order**.
    """)
    return


@app.cell
def _(threading, time):
    def take_both(first: threading.Lock, second: threading.Lock):
        with first:
            time.sleep(0.2)
            with second:
                pass

    def deadlocks(same_order: bool) -> bool:
        lock_a, lock_b = threading.Lock(), threading.Lock()
        thread_1 = threading.Thread(target=take_both, args=(lock_a, lock_b), daemon=True)
        thread_2 = threading.Thread(
            target=take_both, args=(lock_a, lock_b) if same_order else (lock_b, lock_a), daemon=True
        )
        thread_1.start()
        thread_2.start()
        thread_1.join(timeout=1)
        thread_2.join(timeout=1)
        return thread_1.is_alive()  # still waiting after 1 s

    print("opposite lock order, deadlocked:", deadlocks(same_order=False))
    print("same lock order, deadlocked:    ", deadlocks(same_order=True))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## asyncio in a background thread

    *Listings 7.13–7.15.* GUI toolkits (Tkinter, Qt), game loops and sync web frameworks own the main thread. To use async
    code from them, run an event loop **forever in a background thread** and send work to it thread-safely:

    * `asyncio.run_coroutine_threadsafe(coro, loop)` returns a `concurrent.futures.Future` you can wait on from sync code
    * `loop.call_soon_threadsafe(callback)` schedules a callback on the loop's thread

    Never touch loop objects or GUI widgets from the wrong thread. Pass messages instead.
    """)
    return


@app.cell
def _(asyncio, threading):
    _loop = asyncio.new_event_loop()
    _thread = threading.Thread(target=_loop.run_forever)
    _thread.start()

    # From here on this is "sync" code, e.g. a button click handler in a GUI
    _future = asyncio.run_coroutine_threadsafe(asyncio.sleep(0.5, result="done on the asyncio thread"), _loop)
    print(_future.result())  # blocks this thread until the coroutine finishes

    _loop.call_soon_threadsafe(_loop.stop)
    _thread.join()
    _loop.close()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## C extensions that release the GIL run in parallel on threads

    *Listings 7.16–7.19.* `hashlib.scrypt` (and most numpy operations) release the GIL, so threads speed them up with no
    process start-up and no pickling.
    """)
    return


@app.cell
def _(ThreadPoolExecutor, hash_password, os, timed):
    _passwords = [os.urandom(10) for _ in range(1_000)]

    with timed("1 thread"):
        [hash_password(password) for password in _passwords]

    with ThreadPoolExecutor() as _pool, timed("thread pool"):
        list(_pool.map(hash_password, _passwords))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Takeaways

    * Blocking library in async code: `asyncio.to_thread` (pool size = default executor, so pass your own pool for more).
    * Threads parallelize I/O and GIL-releasing C code, **not** pure-Python CPU work (use processes, notebook 6).
    * Protect shared state with `threading.Lock`. Use `RLock` for re-entrant code and one global lock order.
    * To mix sync frameworks with asyncio: a loop in a background thread plus `run_coroutine_threadsafe` / `call_soon_threadsafe`.
    """)
    return


if __name__ == "__main__":
    app.run()
