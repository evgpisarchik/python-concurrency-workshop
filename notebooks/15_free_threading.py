import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium", app_title="15 · Free-threaded Python")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 15 · Free-threaded Python: threads without the GIL

    CPython has a second build with **no GIL** ([PEP 703](https://peps.python.org/pep-0703/)): experimental in 3.13,
    officially supported in 3.14 ([PEP 779](https://peps.python.org/pep-0779/)). It is a separate interpreter, usually
    named with a `t`: `python3.14t`.

    | | regular build | free-threaded build |
    |---|---|---|
    | CPU-bound Python in threads | one thread at a time | **parallel on every core** |
    | single-thread speed | baseline | a few % slower (3.14) |
    | a race in your code | often hidden by the GIL | shows up quickly |
    | C extensions | all of them | need a free-threaded wheel, otherwise the GIL comes back |

    ```bash
    uv python install 3.14t
    uv run --python 3.14t python -c "import sys; print(sys._is_gil_enabled())"   # False
    ```

    This notebook runs on the regular build and starts the other builds as subprocesses (through `uv`), so you see
    both side by side. The first run downloads 3.14t.
    """)
    return


@app.cell
def _():
    import contextvars
    import subprocess
    import sys
    import sysconfig
    import threading

    import marimo as mo

    from workshop.freethreading import Counter, lost_updates
    from workshop.nb import gate, run_python

    return (
        Counter,
        contextvars,
        gate,
        lost_updates,
        mo,
        run_python,
        subprocess,
        sys,
        sysconfig,
        threading,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Which build am I on?

    * `sysconfig.get_config_var("Py_GIL_DISABLED")` tells you whether this is the **free-threaded build**
    * `sys._is_gil_enabled()` tells you whether the GIL is **actually off right now**. A free-threaded build turns it
      back on when you import a C extension that isn't marked as free-threading safe, or when you set `PYTHON_GIL=1`
    """)
    return


@app.cell
def _(sys, sysconfig):
    print(sys.version)
    print("free-threaded build:", sysconfig.get_config_var("Py_GIL_DISABLED") == 1)
    print("GIL enabled:", sys._is_gil_enabled())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## The same code on three builds

    `workshop/freethreading.py` runs 4 × `fib(30)` on 1 and on 4 threads, then does `counter.value += 1` from 4 threads
    **without a lock**. We run it on the regular build, on the free-threaded build, and on the free-threaded build with
    `PYTHON_GIL=1`, which switches the GIL back on (this is also what happens when a C extension needs it).
    """)
    return


@app.cell
def _(mo):
    builds_button = mo.ui.run_button(label="Run on all three builds")
    builds_button
    return (builds_button,)


@app.cell
def _(builds_button, gate, run_python):
    gate(builds_button, "the benchmark")

    print("--- 3.14, regular build")
    print(run_python("3.14", ["-m", "workshop.freethreading"]))

    print("--- 3.14t, free-threaded build")
    print(run_python("3.14t", ["-m", "workshop.freethreading"]))

    print("--- 3.14t with PYTHON_GIL=1")
    print(run_python("3.14t", ["-m", "workshop.freethreading"], env={"PYTHON_GIL": "1"}))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    What to read in the output:

    * **4 threads vs 1.** With the GIL, 4 threads take as long as 1. Without it, they use 4 cores.
    * **1 thread.** The free-threaded build pays a small tax on every object access (atomic reference counts,
      per-object locks). Worth it only if you really use the threads.
    * **Lost updates.** `x += 1` is *read, add, write*. The GIL rarely switches threads in the middle, so the race stays
      hidden. Without the GIL most updates get lost. **The race was always there.**

    Single operations on built-in `list`, `dict` and `set` (`append`, `d[k] = v`) stay safe: the free-threaded build
    protects each object with its own lock. Sequences of operations (check-then-set, `+=`) are not.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Fix the race with a lock

    Same as in notebook 7: a `threading.Lock` around the read-modify-write. On the regular build both versions show 0
    lost updates, because the GIL hides the race. Open this notebook on 3.14t to see the unlocked version break here too:

    ```bash
    PYTHONPATH=. uv run --python 3.14t --no-project --with marimo marimo edit notebooks/15_free_threading.py
    ```
    """)
    return


@app.cell
def _(Counter, lost_updates, threading):
    _counter = Counter()
    _lock = threading.Lock()

    def add_with_lock():
        for _ in range(200_000):
            with _lock:
                _counter.value += 1

    _threads = [threading.Thread(target=add_with_lock) for _ in range(4)]
    for _t in _threads:
        _t.start()
    for _t in _threads:
        _t.join()

    print(f"without a lock: {lost_updates():,} lost")
    print(f"with a lock:    {800_000 - _counter.value:,} lost")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## C extensions can switch the GIL back on

    An extension module has to declare that it works without the GIL (`Py_mod_gil`). If it doesn't, importing it on 3.14t
    **re-enables the GIL for the whole process** and prints a `RuntimeWarning`. Your threads silently go back to taking
    turns: check `sys._is_gil_enabled()` *after* your imports.

    * Most popular packages (numpy, pydantic-core, cryptography, …) ship `cp314t` wheels. Check
      [py-free-threading.github.io/tracking](https://py-free-threading.github.io/tracking/).
    * `PYTHON_GIL=0` (or `-X gil=0`) keeps the GIL off anyway, at your own risk.
    * Packages without any 3.14t wheel can't be installed at all. In this workshop that's `psycopg-binary`, which is
      why only notebooks 15–18 run on 3.14t.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## New threads can inherit context variables (3.14)

    Notebook 14 showed that each asyncio task gets a **copy** of the current `contextvars` context. Threads used to start
    with an **empty** context instead: a request id set in the parent was gone in the thread.

    3.14 adds `Thread(context=...)` and the `-X thread_inherit_context` flag. It is **on by default in the free-threaded
    build**, off in the regular one.
    """)
    return


@app.cell
def _(contextvars, sys, threading):
    request_id = contextvars.ContextVar("request_id", default="<none>")
    request_id.set("req-42")

    _seen = []

    def remember_request_id():
        _seen.append(request_id.get())

    _t = threading.Thread(target=remember_request_id)
    _t.start()
    _t.join()

    _t = threading.Thread(target=remember_request_id, context=contextvars.copy_context())
    _t.start()
    _t.join()

    print(f"thread_inherit_context = {sys.flags.thread_inherit_context}")
    print(f"Thread() sees:                        {_seen[0]}")
    print(f"Thread(context=copy_context()) sees:  {_seen[1]}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Warning filters per task and per thread (3.14)

    `warnings.catch_warnings()` used to change the **process-wide** filter list. While one task sits inside
    `catch_warnings(action="ignore")` and awaits, warnings from *every other* task and thread are swallowed too.

    With `-X context_aware_warnings` (**on by default in the free-threaded build**), the filters live in a context
    variable, so they only apply to the current task or thread. `workshop/children/warnings_race.py` runs with the flag
    off and on:
    """)
    return


@app.cell
def _(subprocess, sys):
    print(
        subprocess.check_output(
            [sys.executable, "-X", "context_aware_warnings=0", "-m", "workshop.children.warnings_race"], text=True
        )
    )
    print(
        subprocess.check_output(
            [sys.executable, "-X", "context_aware_warnings=1", "-m", "workshop.children.warnings_race"], text=True
        )
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Takeaways

    * Free-threaded 3.14t runs **CPU-bound Python threads in parallel**. It's a separate build, and your dependencies need
      free-threaded wheels.
    * Check `sys._is_gil_enabled()` after your imports: one old C extension turns the GIL back on for everyone.
    * Races the GIL used to hide show up quickly. Guard shared state with locks, or share nothing (queues, notebook 12).
    * 3.14t also turns on two safer defaults: threads inherit the caller's context variables, and warning filters are per
      context. You can enable both on the regular build with `-X` flags.
    * Other ways to use all cores: processes (notebook 6) and subinterpreters (notebook 16).
    """)
    return


if __name__ == "__main__":
    app.run()
