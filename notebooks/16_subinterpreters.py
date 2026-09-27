import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium", app_title="16 · Subinterpreters")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 16 · Subinterpreters: many Pythons in one process

    One process can host several **isolated interpreters**. Each has its own modules, globals and, since 3.12, **its own
    GIL** ([PEP 684](https://peps.python.org/pep-0684/)). 3.14 made them public as `concurrent.interpreters` and
    `concurrent.futures.InterpreterPoolExecutor` ([PEP 734](https://peps.python.org/pep-0734/)).

    | | threads | subinterpreters | processes |
    |---|---|---|---|
    | CPU-bound Python in parallel | only on 3.14t | ✅ one GIL each | ✅ one GIL each |
    | shared state | everything (needs locks) | nothing by default | nothing by default |
    | start-up | ~µs | ~ms | ~100 ms (spawn) |
    | passing data | direct | copy, or share buffers without copying | pickle through a pipe |
    | C extensions | all | only multi-phase-init ones (numpy: not yet) | all |

    Think of them as **processes' isolation at almost threads' cost**.
    """)
    return


@app.cell
def _():
    from concurrent import interpreters
    from concurrent.futures import InterpreterPoolExecutor, ProcessPoolExecutor, ThreadPoolExecutor

    import marimo as mo

    from workshop.common import timed
    from workshop.cpu import fib

    return (
        InterpreterPoolExecutor,
        ProcessPoolExecutor,
        ThreadPoolExecutor,
        fib,
        interpreters,
        mo,
        timed,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Create one, run code in it

    `interpreters.create()` returns a fresh interpreter. `exec()` runs source code in its `__main__` and blocks until it's
    done. Its globals and `sys.modules` are its own: setting `x` there does nothing to `x` here.
    """)
    return


@app.cell
def _(interpreters):
    x = "main interpreter's x"

    _interp = interpreters.create()
    _interp.exec("x = 'sub-interpreter x'; print('inside: ', x)")
    print("outside:", x)

    # An exception inside becomes ExecutionFailed outside. The original type and message are in .excinfo
    try:
        _interp.exec("1 / 0")
    except interpreters.ExecutionFailed as _e:
        print(f"ExecutionFailed: {_e.excinfo.type.__name__}: {_e.excinfo.msg}")
    _interp.close()
    return (x,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Call a function

    `interp.call(fn, *args)` runs a function there and returns its result. (`call_in_thread()` does the same in a new
    thread, so the caller doesn't block.)

    Functions cross over in one of two ways:

    * **importable** ones (`workshop.cpu.fib`) are imported by name on the other side, like with process pools
    * **self-contained** ones (no globals, no closure) have their code sent over, so unlike with process pools
      (notebook 6), a function defined **in a notebook cell** works too

    A function that uses this interpreter's globals is refused with `NotShareableError`: `x` doesn't exist over there.
    """)
    return


@app.cell
def _(fib, interpreters, x):
    def double(n):
        return 2 * n

    def uses_a_global():
        return x  # a global of *this* interpreter

    _interp = interpreters.create()
    print("fib(25) =", _interp.call(fib, 25))
    print("double(21) =", _interp.call(double, 21))
    try:
        _interp.call(uses_a_global)
    except interpreters.NotShareableError as _e:
        print("uses_a_global():", repr(_e))
    _interp.close()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Passing data: queues, copies and shared buffers

    Interpreters share no objects, so data crosses the boundary in one of three ways:

    * **Shareable objects** (`int`, `float`, `str`, `bytes`, `bool`, `None`, tuples of them) are passed directly,
      without pickling. They're immutable, so it doesn't matter whether the other side gets the same object or a copy
    * **Everything else is pickled**, so you get a copy, just like with processes
    * **A `memoryview` shares its buffer** without copying: both interpreters write to the same memory, like
      `multiprocessing.shared_memory` in notebook 6

    `interpreters.create_queue()` is a queue that works across interpreters. `prepare_main(name=value)` puts values into
    the other interpreter's globals before `exec()`.
    """)
    return


@app.cell
def _(interpreters):
    _interp = interpreters.create()

    # A queue both interpreters can use
    _queue = interpreters.create_queue()
    _interp.prepare_main(queue=_queue)
    _interp.exec("queue.put('hello through the queue')")
    print(_queue.get())

    # A buffer both interpreters write to
    _buffer = bytearray(5)
    _interp.prepare_main(view=memoryview(_buffer))
    _interp.exec("view[:] = b'hello'")
    print("main sees the other interpreter's write:", _buffer)
    _interp.close()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Parallel CPU work: InterpreterPoolExecutor

    A drop-in replacement for the other executors, with one interpreter per worker thread. The same 4 × `fib(30)` on each
    executor, including the time to start the workers:
    """)
    return


@app.cell
def _(InterpreterPoolExecutor, ProcessPoolExecutor, ThreadPoolExecutor, fib, timed):
    with ThreadPoolExecutor(4) as _pool, timed("threads     "):
        list(_pool.map(fib, [30] * 4))

    with InterpreterPoolExecutor(4) as _pool, timed("interpreters"):
        list(_pool.map(fib, [30] * 4))

    with ProcessPoolExecutor(4) as _pool, timed("processes   "):
        list(_pool.map(fib, [30] * 4))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Interpreters run in parallel like processes, but start much faster: processes spend most of this time starting up. Arguments and results are
    still copied, so use them for chunky work with small inputs and outputs, like process pools.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## The catch: C extensions

    Each interpreter imports its own copy of every module. Pure-Python modules and most of the standard library are fine.
    A C extension must support **multi-phase initialisation and per-interpreter state**, and many don't yet. Importing
    one fails with `ImportError` instead of crashing.
    """)
    return


@app.cell
def _(interpreters):
    _interp = interpreters.create()
    _interp.exec("import json, hashlib, asyncio")
    print("json, hashlib, asyncio: imported fine")
    try:
        _interp.exec("import numpy")
    except interpreters.ExecutionFailed as _e:
        print("numpy:", _e.excinfo.msg.splitlines()[-1])  # numpy puts the real reason on its last line
    _interp.close()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Takeaways

    * `concurrent.interpreters` (3.14) gives you isolated interpreters in one process, each with its own GIL, so they
      run CPU-bound Python **in parallel on the regular build**.
    * Share nothing by default: pass data through `create_queue()`, `prepare_main()` and `call()` arguments, or share a
      buffer with a `memoryview`.
    * `InterpreterPoolExecutor` is the easy way in: about as fast as processes for CPU work, with much faster start-up.
    * Check that your C extensions can be imported in a subinterpreter before choosing this over processes.
    * Always `close()` interpreters you create, or use the executor, which does it for you.
    """)
    return


if __name__ == "__main__":
    app.run()
