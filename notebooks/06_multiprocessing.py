import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium", app_title="6 · Multiprocessing")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 6 · CPU-bound work: processes, MapReduce, shared memory

    Processes sidestep the GIL: each has its own interpreter, so CPU-bound Python code runs in parallel.

    > **Notebook rule:** a function you send to a process must be **importable** by the child. Process pools pickle
    > functions by module and name, so worker functions live in `workshop/cpu.py`, `workshop/map_reduce.py` and
    > `workshop/shared_memory.py`, not in cells. (In a script, use the `if __name__ == "__main__":` guard.)
    """)
    return


@app.cell
def _():
    import asyncio
    import functools
    import multiprocessing
    import time
    from collections import Counter
    from concurrent.futures import ProcessPoolExecutor, as_completed

    import marimo as mo

    from workshop import map_reduce, shared_memory
    from workshop.cpu import count, timed_count
    from workshop.nb import gate

    return (
        Counter,
        ProcessPoolExecutor,
        as_completed,
        asyncio,
        count,
        functools,
        gate,
        map_reduce,
        mo,
        multiprocessing,
        shared_memory,
        time,
        timed_count,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Parallel processes

    *Listings 6.1, 6.4.* Two CPU-bound jobs: one after another, then in two processes (each reports its pid).
    """)
    return


@app.cell
def _(ProcessPoolExecutor, count, time, timed_count):
    _jobs = [30_000_000, 60_000_000]

    _start = time.perf_counter()
    for _n in _jobs:
        count(_n)
    print(f"sequential: {time.perf_counter() - _start:.2f} s")

    with ProcessPoolExecutor() as _pool:
        _start = time.perf_counter()
        for _pid, _n, _secs in _pool.map(timed_count, _jobs):
            print(f"  pid {_pid} counted to {_n:,} in {_secs:.2f} s")
        print(f"2 processes: {time.perf_counter() - _start:.2f} s  (≈ the slowest job, not the sum)")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Blocking vs non-blocking submission

    *Listings 6.2, 6.3.* `Pool.apply()` waits for each result before submitting the next job, so it runs sequentially.
    `apply_async()` submits right away and returns a handle, and `.get()` waits later.
    """)
    return


@app.cell
def _(count, multiprocessing, time):
    with multiprocessing.Pool() as _pool:
        _start = time.perf_counter()
        _pool.apply(count, (30_000_000,))
        _pool.apply(count, (30_000_000,))
        print(f"apply x2:       {time.perf_counter() - _start:.2f} s")

        _start = time.perf_counter()
        _handles = [_pool.apply_async(count, (30_000_000,)) for _ in range(2)]
        [_h.get() for _h in _handles]
        print(f"apply_async x2: {time.perf_counter() - _start:.2f} s")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Result order: `map` vs `as_completed`

    *Listing 6.4.* `executor.map` yields in **input order**, so one slow first job delays every result after it.
    `as_completed` yields each result as soon as it's ready.
    """)
    return


@app.cell
def _(ProcessPoolExecutor, as_completed, count, time):
    _numbers = [100_000_000, 1, 3, 5]
    with ProcessPoolExecutor() as _pool:
        _start = time.perf_counter()
        for _result in _pool.map(count, _numbers):
            print(f"map:          {_result:>11,} at {time.perf_counter() - _start:.2f} s")

        _start = time.perf_counter()
        for _future in as_completed([_pool.submit(count, _n) for _n in _numbers]):
            print(f"as_completed: {_future.result():>11,} at {time.perf_counter() - _start:.2f} s")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Processes from asyncio: `run_in_executor`

    *Listing 6.5.* `loop.run_in_executor(process_pool, fn, *args)` returns an awaitable, so gather / wait / as_completed all
    work with it, and the event loop stays free. The ticker below keeps ticking while four CPU jobs run in other processes.
    """)
    return


@app.cell
async def _(ProcessPoolExecutor, asyncio, count, time):
    async def ticker(stop: asyncio.Event):
        ticks = 0
        while not stop.is_set():
            await asyncio.sleep(0.1)
            ticks += 1
        return ticks

    _stop = asyncio.Event()
    _ticker = asyncio.create_task(ticker(_stop))
    _loop = asyncio.get_running_loop()
    with ProcessPoolExecutor() as _pool:
        _start = time.perf_counter()
        _results = await asyncio.gather(*(_loop.run_in_executor(_pool, count, 40_000_000) for _ in range(4)))
    _stop.set()
    print(
        f"4 CPU jobs done in {time.perf_counter() - _start:.2f} s; the event loop ticked {await _ticker} times meanwhile"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## MapReduce

    *Listing 6.6.* **Map** each chunk independently (parallelizable), then **reduce** the partial results into one.
    """)
    return


@app.cell
def _(Counter, functools, map_reduce):
    _lines = ["I know what I know", "I know that I know", "I don't know much", "They don't know much"]
    _mapped = [dict(Counter(_line.split())) for _line in _lines]
    for _m in _mapped:
        print("map   :", _m)
    print("reduce:", functools.reduce(map_reduce.merge_dictionaries, _mapped))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *Listings 6.7–6.9.* Word frequencies over a Google Books style 1-gram file (a synthetic one is generated on first run). We compare:
    one process, a parallel map with a single-process reduce, and a parallel map plus a parallel reduce.
    """)
    return


@app.cell
def _(map_reduce):
    if not map_reduce.NGRAMS_FILE.exists():
        map_reduce.generate_ngrams(2_000_000)
    ngram_lines = map_reduce.read_ngrams()
    print(f"{len(ngram_lines):,} lines loaded")
    return (ngram_lines,)


@app.cell
async def _(
    ProcessPoolExecutor,
    asyncio,
    functools,
    map_reduce,
    ngram_lines,
    time,
):
    async def parallel_reduce(loop, pool, counters: list[dict], chunk_size: int) -> dict:
        chunks = list(map_reduce.partition(counters, chunk_size))
        while len(chunks[0]) > 1:
            reducers = [
                loop.run_in_executor(pool, functools.reduce, map_reduce.merge_dictionaries, chunk) for chunk in chunks
            ]
            chunks = list(map_reduce.partition(await asyncio.gather(*reducers), chunk_size))
        return chunks[0][0]

    _start = time.perf_counter()
    _single = map_reduce.map_frequencies(ngram_lines)
    print(f"single process:               {time.perf_counter() - _start:.2f} s  Aardvark={_single['Aardvark']:,}")

    _loop = asyncio.get_running_loop()
    with ProcessPoolExecutor() as _pool:
        _start = time.perf_counter()
        _partials = await asyncio.gather(
            *(
                _loop.run_in_executor(_pool, map_reduce.map_frequencies, c)
                for c in map_reduce.partition(ngram_lines, 60_000)
            )
        )
        _result = functools.reduce(map_reduce.merge_dictionaries, _partials)
        print(
            f"parallel map ({len(_partials)} chunks):     {time.perf_counter() - _start:.2f} s  Aardvark={_result['Aardvark']:,}"
        )

        _start = time.perf_counter()
        _partials = await asyncio.gather(
            *(
                _loop.run_in_executor(_pool, map_reduce.map_frequencies, c)
                for c in map_reduce.partition(ngram_lines, 60_000)
            )
        )
        _result = await parallel_reduce(_loop, _pool, _partials, 8)
        print(f"parallel map + reduce:        {time.perf_counter() - _start:.2f} s  Aardvark={_result['Aardvark']:,}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Chunk size matters. Chunks that are too small spend their time pickling data between processes, and chunks that are
    too large leave cores idle:
    """)
    return


@app.cell
async def _(ProcessPoolExecutor, asyncio, map_reduce, ngram_lines, time):
    _loop = asyncio.get_running_loop()
    with ProcessPoolExecutor() as _pool:
        for _size in (1_000, 60_000, len(ngram_lines) // 2):
            _start = time.perf_counter()
            await asyncio.gather(
                *(
                    _loop.run_in_executor(_pool, map_reduce.map_frequencies, c)
                    for c in map_reduce.partition(ngram_lines, _size)
                )
            )
            print(f"chunk size {_size:>9,}: {time.perf_counter() - _start:.2f} s")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Shared memory and race conditions

    *Listing 6.10.* Processes don't share objects. `multiprocessing.Value` / `Array` place a C value in **shared memory** that every process can see.
    """)
    return


@app.cell
def _(multiprocessing, shared_memory):
    _integer = multiprocessing.Value("i", 0)
    _array = multiprocessing.Array("i", [0, 0])
    _procs = [
        multiprocessing.Process(target=shared_memory.increment_value, args=(_integer,)),
        multiprocessing.Process(target=shared_memory.increment_array, args=(_array,)),
    ]
    for _p in _procs:
        _p.start()
    for _p in _procs:
        _p.join()
    print(f"Value: {_integer.value}, Array: {_array[:]}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *Listings 6.11, 6.12.* `value += 1` is **read → add → write**. When two processes interleave, increments get lost.
    Holding the Value's lock makes the update atomic, at the cost of speed. Keep critical sections small.
    """)
    return


@app.cell
def _(multiprocessing, shared_memory, time):
    def run_two_incrementers(target, times: int) -> tuple[int, float]:
        shared = multiprocessing.Value("i", 0)
        procs = [multiprocessing.Process(target=target, args=(shared, times)) for _ in range(2)]
        start = time.perf_counter()
        for p in procs:
            p.start()
        for p in procs:
            p.join()
        return shared.value, time.perf_counter() - start

    _value, _secs = run_two_incrementers(shared_memory.increment_many, 100_000)
    print(f"no lock:   expected 200,000, got {_value:,}  ({_secs:.2f} s)")

    _value, _secs = run_two_incrementers(shared_memory.increment_many_locked, 100_000)
    print(f"with lock: expected 200,000, got {_value:,}  ({_secs:.2f} s)")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *Listing 6.13.* Pool workers can't receive a shared `Value` as a normal task argument. Pass it **once**, to each worker
    at start-up, through an `initializer`.
    """)
    return


@app.cell
def _(ProcessPoolExecutor, multiprocessing, shared_memory):
    _counter = multiprocessing.Value("d", 0)
    with ProcessPoolExecutor(initializer=shared_memory.init_counter, initargs=(_counter,)) as _pool:
        _futures = [_pool.submit(shared_memory.increment_shared_counter) for _ in range(10)]
        [_f.result() for _f in _futures]
    print(f"counter after 10 increments in pool workers: {_counter.value}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *Listing 6.14.* The same trick gives **live progress**: workers bump a shared counter, and an asyncio task in this process reports it while we await the pool.
    """)
    return


@app.cell
async def _(
    ProcessPoolExecutor,
    asyncio,
    map_reduce,
    multiprocessing,
    ngram_lines,
):
    async def progress_reporter(progress, total: int):
        while progress.value < total:
            print(f"finished {progress.value}/{total} map operations")
            await asyncio.sleep(0.2)

    _progress = multiprocessing.Value("i", 0)
    _chunks = list(map_reduce.partition(ngram_lines, 20_000))
    _loop = asyncio.get_running_loop()
    with ProcessPoolExecutor(initializer=map_reduce.init_progress, initargs=(_progress,)) as _pool:
        _reporter = asyncio.create_task(progress_reporter(_progress, len(_chunks)))
        _partials = await asyncio.gather(
            *(_loop.run_in_executor(_pool, map_reduce.map_frequencies_with_progress, c) for c in _chunks)
        )
        await _reporter
    print(f"done: {len(_partials)}/{len(_chunks)}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## One event loop per process

    *Listing 6.15.* When one event loop is saturated (for example, parsing thousands of DB rows), run **N processes, each with
    its own loop and connection pool**. That's the model behind `uvicorn --workers N` and `gunicorn -w N`.
    Needs the database from notebook 5.
    """)
    return


@app.cell
def _(mo):
    loops_button = mo.ui.run_button(label="Run 5 processes x 10,000 queries")
    loops_button
    return (loops_button,)


@app.cell
async def _(ProcessPoolExecutor, asyncio, gate, loops_button, time):
    gate(loops_button)
    from workshop.db_workers import query_products_in_new_loop

    _loop = asyncio.get_running_loop()
    with ProcessPoolExecutor() as _pool:
        _start = time.perf_counter()
        _counts = await asyncio.gather(
            *(_loop.run_in_executor(_pool, query_products_in_new_loop, 10_000) for _ in range(5))
        )
    print(f"{sum(_counts):,} queries from 5 processes (5 event loops) in {time.perf_counter() - _start:.2f} s")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Takeaways

    * Processes give real parallelism for CPU-bound Python. Pools reuse processes, which avoids paying start-up per job.
    * Arguments and results are **pickled**, so keep them small and choose chunk sizes to balance overhead against idle cores.
    * `run_in_executor` connects process pools to asyncio.
    * Shared memory is fast but needs locks. Prefer **returning results** over sharing state.
    """)
    return


if __name__ == "__main__":
    app.run()
