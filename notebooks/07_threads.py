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
    import numpy as np
    import requests

    from workshop.cpu import hash_password
    from workshop.nb import Timeline, start_server, stop_server

    return (
        ThreadPoolExecutor,
        Timeline,
        asyncio,
        hash_password,
        mo,
        np,
        os,
        requests,
        socket,
        start_server,
        stop_server,
        threading,
        time,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Thread per connection

    *Listings 7.1, 7.2.* The simplest way to make blocking code concurrent is to give each client its own thread, so a blocked
    `recv()` only blocks that thread. Python can't kill threads, so shutting down means making each thread **exit by itself**:
    `socket.shutdown()` makes the blocked `recv()` return `b"\"`.
    """)
    return


@app.cell
def _(Timeline, socket, threading):
    class ClientEchoThread(threading.Thread):
        def __init__(self, client: socket.socket, timeline: Timeline):
            super().__init__(name=f"client-thread-{client.getpeername()[1]}")
            self.client, self.timeline = client, timeline

        def run(self):
            while data := self.client.recv(2048):  # blocks only this thread
                self.client.sendall(data)
            self.timeline.log("recv() returned b'': thread exits")

        def close(self):
            self.client.shutdown(socket.SHUT_RDWR)  # unblocks recv() in run()

    _timeline = Timeline()
    _server = socket.create_server(("127.0.0.1", 8701))
    _clients = [socket.create_connection(("127.0.0.1", 8701)) for _ in range(3)]
    _threads = []
    for _ in _clients:
        _connection, _ = _server.accept()
        _thread = ClientEchoThread(_connection, _timeline)
        _thread.start()
        _threads.append(_thread)

    for _i, _c in enumerate(_clients):
        _c.sendall(f"hello {_i}".encode())
        _timeline.log(f"client {_i} got {_c.recv(100)!r}")

    _timeline.log("shutting down")
    for _thread in _threads:
        _thread.close()
        _thread.join()
    for _c in _clients:
        _c.close()
    _server.close()
    _timeline.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## A blocking library, five ways

    *Listings 7.3–7.7.* 50 blocking `requests.get` calls to an endpoint that takes 0.2 s:

    * sequential
    * `ThreadPoolExecutor.map`, without asyncio
    * `loop.run_in_executor(pool, ...)` from async code, with our own pool
    * `run_in_executor(None, ...)`: the loop's **default** pool, `min(32, cpu_count + 4)` threads
    * `asyncio.to_thread(fn, *args)`, the recommended one-liner (also uses the default pool)
    """)
    return


@app.cell
async def _(
    ThreadPoolExecutor,
    asyncio,
    mo,
    os,
    requests,
    start_server,
    stop_server,
    time,
):
    _server = start_server(["-m", "workshop.testserver", "--port", "8702"], 8702)
    _url = "http://127.0.0.1:8702/delay?seconds=0.2"

    def get_status_code(url: str) -> int:
        return requests.get(url).status_code

    _results = {}

    _start = time.perf_counter()
    [get_status_code(_url) for _ in range(50)]
    _results["sequential"] = time.perf_counter() - _start

    with ThreadPoolExecutor(max_workers=50) as _pool:
        _start = time.perf_counter()
        list(_pool.map(get_status_code, [_url] * 50))
        _results["ThreadPoolExecutor(50).map"] = time.perf_counter() - _start

    _loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=50) as _pool:
        _start = time.perf_counter()
        await asyncio.gather(*(_loop.run_in_executor(_pool, get_status_code, _url) for _ in range(50)))
        _results["run_in_executor(own pool of 50)"] = time.perf_counter() - _start

    _start = time.perf_counter()
    await asyncio.gather(*(_loop.run_in_executor(None, get_status_code, _url) for _ in range(50)))
    _results[f"run_in_executor(None): default pool of {min(32, os.cpu_count() + 4)}"] = time.perf_counter() - _start

    _start = time.perf_counter()
    await asyncio.gather(*(asyncio.to_thread(get_status_code, _url) for _ in range(50)))
    _results["asyncio.to_thread (default pool)"] = time.perf_counter() - _start

    stop_server(_server)
    mo.md(
        "| 50 blocking requests of 0.2 s | seconds |\n|---|---|\n"
        + "\n".join(f"| {k} | {v:.2f} |" for k, v in _results.items())
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Shared state needs a lock

    *Listing 7.8.* Many threads update a counter while an asyncio task reports progress. `counter += 1` is read-modify-write,
    so it is guarded with `threading.Lock`. (asyncio locks are **not** thread-safe. Use the `threading` ones for threads.)
    """)
    return


@app.cell
async def _(asyncio, requests, start_server, stop_server, threading):
    _server = start_server(["-m", "workshop.testserver", "--port", "8703"], 8703)
    _counter_lock = threading.Lock()
    _state = {"done": 0}

    def get_and_count(url: str) -> int:
        status = requests.get(url).status_code
        with _counter_lock:
            _state["done"] += 1
        return status

    async def reporter(total: int):
        while _state["done"] < total:
            print(f"finished {_state['done']}/{total} requests")
            await asyncio.sleep(0.25)

    _reporter = asyncio.create_task(reporter(100))
    await asyncio.gather(
        *(asyncio.to_thread(get_and_count, "http://127.0.0.1:8703/delay?seconds=0.2") for _ in range(100))
    )
    await _reporter
    print(f"finished {_state['done']}/100 requests")
    stop_server(_server)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Re-entrant locks and deadlocks

    *Listings 7.9, 7.10.* A function that takes a lock and then calls code that takes the **same** lock blocks forever with
    `Lock`. `RLock` lets the thread that already owns the lock acquire it again.
    """)
    return


@app.cell
def _(threading):
    def make_recursive_sum(lock):
        def sum_list(values: list[int]) -> int:
            with lock:
                if not values:
                    return 0
                head, *tail = values
                return head + sum_list(tail)  # acquires the same lock again

        return sum_list

    def try_recursive_sum(lock) -> str:
        result = {}
        sum_list = make_recursive_sum(lock)
        thread = threading.Thread(target=lambda: result.update(value=sum_list([1, 2, 3, 4])), daemon=True)
        thread.start()
        thread.join(timeout=1)
        return "stuck (deadlocked on itself)" if thread.is_alive() else f"sum = {result['value']}"

    print(f" Lock: {try_recursive_sum(threading.Lock())}")
    print(f"RLock: {try_recursive_sum(threading.RLock())}")
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
    def deadlock_demo(ordered: bool) -> str:
        lock_a, lock_b = threading.Lock(), threading.Lock()

        def first():
            with lock_a:
                time.sleep(0.2)
                with lock_b:
                    pass

        def second():
            locks = (lock_a, lock_b) if ordered else (lock_b, lock_a)
            with locks[0]:
                time.sleep(0.2)
                with locks[1]:
                    pass

        threads = [threading.Thread(target=first, daemon=True), threading.Thread(target=second, daemon=True)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=1)
        return "DEADLOCK" if any(t.is_alive() for t in threads) else "finished"

    print(f"opposite lock order: {deadlock_demo(ordered=False)}")
    print(f"same lock order:     {deadlock_demo(ordered=True)}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## asyncio in a background thread

    *Listings 7.13–7.15.* GUI toolkits (Tkinter, Qt), game loops and sync web frameworks own the main thread. To use async
    code from them, run an event loop **forever in a background thread** and send work to it thread-safely:

    * `asyncio.run_coroutine_threadsafe(coro, loop)` returns a `concurrent.futures.Future` you can wait on from sync code
    * `loop.call_soon_threadsafe(callback)` schedules a callback on the loop's thread (for example, to cancel)

    Never touch loop objects or GUI widgets from the wrong thread. Pass messages instead.
    """)
    return


@app.cell
def _(asyncio, threading, time):
    _bg_loop = asyncio.new_event_loop()
    _bg_thread = threading.Thread(target=_bg_loop.run_forever, name="asyncio-thread", daemon=True)
    _bg_thread.start()

    async def fetch_many(n: int) -> list[float]:
        results = await asyncio.gather(*(asyncio.sleep(0.5, result=i) for i in range(n)))
        return results

    # --- from here on this is "sync" code, e.g. a button click handler in a GUI ---
    _future = asyncio.run_coroutine_threadsafe(fetch_many(100), _bg_loop)
    print(f"submitted from {threading.current_thread().name}; waiting for the result...")
    print(f"got {len(_future.result(timeout=5))} results from the asyncio thread")

    _slow = asyncio.run_coroutine_threadsafe(asyncio.sleep(60), _bg_loop)
    _bg_loop.call_soon_threadsafe(_slow.cancel)  # e.g. a "Cancel" button
    time.sleep(0.1)
    print(f"cancelled from another thread: {_slow.cancelled()}")

    _bg_loop.call_soon_threadsafe(_bg_loop.stop)
    _bg_thread.join()
    _bg_loop.close()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## C extensions that release the GIL run in parallel on threads

    *Listings 7.16–7.19.* `hashlib.scrypt` and most numpy operations release the GIL, so threads speed them up with no
    process start-up and no pickling.
    """)
    return


@app.cell
def _(ThreadPoolExecutor, hash_password, mo, np, os, time):
    _passwords = [os.urandom(10) for _ in range(2_000)]

    _start = time.perf_counter()
    for _p in _passwords:
        hash_password(_p)
    _sequential = time.perf_counter() - _start

    with ThreadPoolExecutor() as _pool:
        _start = time.perf_counter()
        list(_pool.map(hash_password, _passwords))
        _threaded = time.perf_counter() - _start

    _matrix = np.arange(100_000_000).reshape(50, -1)  # ~800 MB of int64; lower it if you're short on RAM
    _start = time.perf_counter()
    np.mean(_matrix, axis=1)
    _np_single = time.perf_counter() - _start
    with ThreadPoolExecutor() as _pool:
        _start = time.perf_counter()
        list(_pool.map(np.mean, _matrix))  # one row per task
        _np_threads = time.perf_counter() - _start

    mo.md(f"""
    | | 1 thread | thread pool |
    |---|---|---|
    | scrypt × 2,000 | {_sequential:.2f} s | {_threaded:.2f} s |
    | numpy row means (100M values) | {_np_single:.3f} s | {_np_threads:.3f} s |
    """)
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
