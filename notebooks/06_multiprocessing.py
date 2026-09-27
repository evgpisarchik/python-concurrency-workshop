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
    from collections import Counter
    from concurrent.futures import ProcessPoolExecutor, as_completed

    import marimo as mo

    from workshop import map_reduce, shared_memory
    from workshop.common import timed
    from workshop.cpu import count
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
        timed,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Parallel processes

    *Listings 6.1, 6.4.* Two CPU-bound jobs, one after another, then in a pool of processes.
    """)
    return


@app.cell
def _(ProcessPoolExecutor, count, timed):
    with timed("sequential"):
        count(30_000_000)
        count(30_000_000)

    with ProcessPoolExecutor() as _pool:
        list(_pool.map(count, [30_000_000, 30_000_000]))  # the first run also starts the workers, so time the second
        with timed("2 processes"):
            list(_pool.map(count, [30_000_000, 30_000_000]))
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
def _(count, multiprocessing, timed):
    with multiprocessing.Pool(2) as _pool:
        with timed("apply x2"):
            _pool.apply(count, (30_000_000,))
            _pool.apply(count, (30_000_000,))

        with timed("apply_async x2"):
            _first = _pool.apply_async(count, (30_000_000,))
            _second = _pool.apply_async(count, (30_000_000,))
            _first.get()
            _second.get()
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
def _(ProcessPoolExecutor, as_completed, count):
    _jobs = [100_000_000, 1, 3]
    with ProcessPoolExecutor() as _pool:
        print("map:         ", list(_pool.map(count, _jobs)))
        print("as_completed:", [f.result() for f in as_completed(_pool.submit(count, n) for n in _jobs)])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Processes from asyncio: `run_in_executor`

    *Listing 6.5.* `loop.run_in_executor(process_pool, fn, *args)` returns an awaitable, so gather / wait / as_completed all
    work with it, and the event loop stays free while the processes compute.
    """)
    return


@app.cell
async def _(ProcessPoolExecutor, asyncio, count):
    async def still_responsive():
        await asyncio.sleep(0.1)
        print("the event loop is still free")

    _loop = asyncio.get_running_loop()
    with ProcessPoolExecutor() as _pool:
        _results = await asyncio.gather(
            _loop.run_in_executor(_pool, count, 40_000_000),
            _loop.run_in_executor(_pool, count, 40_000_000),
            still_responsive(),
        )
    print(_results)
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
    _lines = ["I know what I know", "I know that I know", "I don't know much"]
    _mapped = [dict(Counter(line.split())) for line in _lines]
    print("map:   ", _mapped)
    print("reduce:", functools.reduce(map_reduce.merge_dictionaries, _mapped))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *Listings 6.7, 6.8.* Word frequencies over a Google Books style 1-gram file (a synthetic one is generated on first run):
    one process vs a process pool that maps chunks in parallel.

    Chunk size matters. Chunks that are too small spend their time pickling data between processes, and chunks that are
    too large leave cores idle.
    """)
    return


@app.cell
def _(map_reduce):
    ngram_lines = map_reduce.read_ngrams()
    print(f"{len(ngram_lines):,} lines loaded")
    return (ngram_lines,)


@app.cell
def _(ProcessPoolExecutor, functools, map_reduce, ngram_lines, timed):
    class WordCounter:
        def __init__(self, lines: list[str]):
            self.lines = lines

        def in_one_process(self) -> dict:
            return map_reduce.map_frequencies(self.lines)

        def in_pool(self, pool, chunk_size: int) -> dict:
            chunks = map_reduce.partition(self.lines, chunk_size)
            partials = pool.map(map_reduce.map_frequencies, chunks)  # map: in parallel
            return functools.reduce(map_reduce.merge_dictionaries, partials)  # reduce: here

    _counter = WordCounter(ngram_lines)
    with timed("one process"):
        _counter.in_one_process()

    with ProcessPoolExecutor() as _pool:
        with timed("pool, chunks of 1,000"):
            _counter.in_pool(_pool, 1_000)
        with timed("pool, chunks of 60,000"):
            _counter.in_pool(_pool, 60_000)
        with timed("pool, 2 huge chunks"):
            _counter.in_pool(_pool, len(ngram_lines) // 2)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Shared memory and race conditions

    *Listing 6.10.* Processes don't share objects. `multiprocessing.Value` / `Array` place a C value in **shared memory**
    that every process can see.
    """)
    return


@app.cell
def _(multiprocessing, shared_memory):
    _number = multiprocessing.Value("i", 0)
    _process = multiprocessing.Process(target=shared_memory.increment_value, args=(_number,))
    _process.start()
    _process.join()
    print("the child incremented the shared value to", _number.value)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *Listings 6.11, 6.12.* `value += 1` is **read → add → write**. When two processes interleave, increments get lost.
    Holding the Value's lock makes the update atomic.
    """)
    return


@app.cell
def _(multiprocessing, shared_memory):
    def run_in_two_processes(target) -> int:
        number = multiprocessing.Value("i", 0)
        processes = [multiprocessing.Process(target=target, args=(number, 100_000)) for _ in range(2)]
        for process in processes:
            process.start()
        for process in processes:
            process.join()
        return number.value

    print(f"no lock:   {run_in_two_processes(shared_memory.increment_many):,} of 200,000")
    print(f"with lock: {run_in_two_processes(shared_memory.increment_many_locked):,} of 200,000")
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
    _counter = multiprocessing.Value("i", 0)
    with ProcessPoolExecutor(initializer=shared_memory.init_counter, initargs=(_counter,)) as _pool:
        for _ in range(10):
            _pool.submit(shared_memory.increment_shared_counter)
    print("counter after 10 increments in pool workers:", _counter.value)
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
def _(ProcessPoolExecutor, gate, loops_button, timed):
    gate(loops_button)
    from workshop.db_workers import query_products_in_new_loop

    with ProcessPoolExecutor(5) as _pool, timed("5 processes x 10,000 queries"):
        list(_pool.map(query_products_in_new_loop, [10_000] * 5))
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
