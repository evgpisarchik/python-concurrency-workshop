import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium", app_title="17 · Inspecting running programs")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 17 · Inspecting running programs: call graphs, `asyncio ps`, remote exec, sampling profiler

    Your async service stopped answering. Which tasks are stuck, and where? Before 3.14 you added logging and restarted,
    and the bug often went away. Now you can look into the running program:

    | Tool | Since | From | Shows |
    |---|---|---|---|
    | `asyncio.print_call_graph()` / `capture_call_graph()` | 3.14 | inside | which task awaits which, with stacks |
    | `python -m asyncio ps / pstree PID` | 3.14 | outside | every task of another process |
    | `sys.remote_exec(pid, script)` ([PEP 768](https://peps.python.org/pep-0768/)) | 3.14 | outside | runs your code inside that process |
    | `python -m pdb -p PID` | 3.14 | outside | an interactive debugger attached to it |
    | `python -m profiling.sampling` | 3.15 | outside | where the time goes: all threads, near-zero overhead |

    **Permissions.** The "outside" tools read another process's memory:

    * **Linux**: same user. A parent can attach to its own child (so the demos here work); anything else may need
      `sudo` or `sysctl kernel.yama.ptrace_scope=0`
    * **macOS**: `sudo`. The demos below fail with a permission error: run the same command with `sudo` in a terminal
    * **Docker**: `--cap-add=SYS_PTRACE`
    """)
    return


@app.cell
def _():
    import asyncio
    import subprocess
    import sys
    import time

    import marimo as mo

    from workshop.children.stuck_service import serve
    from workshop.nb import gate, run_python

    return asyncio, gate, mo, run_python, serve, subprocess, sys, time


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## From inside: the asyncio call graph

    `workshop/children/stuck_service.py` starts 2 requests in a `TaskGroup`. Each one awaits a backend that never
    answers, with no timeout. We run its `serve()` here for a moment and ask asyncio what a request task is doing:

    * `asyncio.format_call_graph(task)` (or `print_call_graph`) shows the task's **stack** and, recursively, **who awaits it**
    * `asyncio.capture_call_graph(task)` returns the same as data: `.call_stack` frames and `.awaited_by` graphs

    Called with no argument inside a task, they describe the current task: handy in a log line or a debug endpoint.
    """)
    return


@app.cell
async def _(asyncio, serve):
    _server = asyncio.create_task(serve(), name="server")
    await asyncio.sleep(0.1)  # let the requests get stuck

    _request = next(t for t in asyncio.all_tasks() if t.get_name() == "request-1")
    print(asyncio.format_call_graph(_request))

    _graph = asyncio.capture_call_graph(_request)
    print("stack:", [f.frame.f_code.co_name for f in _graph.call_stack])
    print("awaited by:", _graph.awaited_by[0].future.get_name())

    _server.cancel()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## From outside: `python -m asyncio ps` and `pstree`

    Now the same service runs as a **separate process**. We know nothing but its PID. `ps` lists every task with its
    coroutine stack and the task awaiting it. `pstree` draws the tree of awaits. The service exits by itself after 2
    minutes.
    """)
    return


@app.cell
def _(mo):
    service_button = mo.ui.run_button(label="Start the stuck service")
    service_button
    return (service_button,)


@app.cell
def _(gate, service_button, subprocess, sys):
    gate(service_button, "the service")
    service = subprocess.Popen([sys.executable, "-m", "workshop.children.stuck_service"], stdout=subprocess.PIPE)
    service.stdout.readline()  # wait for "ready"
    print(f"stuck service running, pid {service.pid}")
    return (service,)


@app.cell
def _(service, subprocess, sys):
    _ps = subprocess.run([sys.executable, "-m", "asyncio", "ps", str(service.pid)], capture_output=True, text=True)
    print(_ps.stdout, _ps.stderr)

    _tree = subprocess.run(
        [sys.executable, "-m", "asyncio", "pstree", str(service.pid)], capture_output=True, text=True
    )
    print(_tree.stdout, _tree.stderr)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Run your own code inside it: `sys.remote_exec()`

    `sys.remote_exec(pid, script_path)` asks another Python process (same version) to run a script **in its main thread
    the next time it executes Python code**. It's safe: the target stops at a point where running code is allowed, just
    like at a signal handler. The script can see everything: modules, globals, the running event loop.

    `workshop/children/inspect_service.py` writes the service's `stats` and every task's call graph to
    `data/remote_report.txt`, which we then read.

    `python -m pdb -p PID` builds on the same mechanism to attach an interactive debugger. Try it in a terminal.
    """)
    return


@app.cell
def _(service, sys, time):
    try:
        sys.remote_exec(service.pid, "workshop/children/inspect_service.py")
        time.sleep(1)  # the service runs the script at its next heartbeat
        print(open("data/remote_report.txt").read())
    except PermissionError as _e:
        print(_e)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Where does the time go? The sampling profiler (3.15)

    3.15 adds `profiling.sampling`: it reads the target's stacks from outside thousands of times a second. The program
    isn't instrumented, so it runs at full speed, and it sees **all threads**. Useful options for concurrent code:

    * `--mode wall`: where each thread *is*, waiting or not
    * `--mode cpu`: only samples where the thread is running on a CPU. Waiting threads drop out
    * `--mode gil`: only samples holding the GIL, which shows which threads fight over it
    * `--async-aware`: stacks by asyncio **task** instead of by thread
    * `attach PID`, `--live` (a `top`-like view), `--flamegraph -o out.html`

    `workshop/children/mixed_load.py` has one thread computing and one sleeping. We profile it on 3.15 (through `uv`, which
    downloads it on first use) in CPU mode: only the computing thread shows up. On macOS, run it in a terminal with `sudo`:

    ```bash
    sudo env PYTHONPATH=. "$(uv python find 3.15)" -m profiling.sampling run -a --mode cpu -m workshop.children.mixed_load
    ```
    """)
    return


@app.cell
def _(mo):
    profile_button = mo.ui.run_button(label="Profile on Python 3.15")
    profile_button
    return (profile_button,)


@app.cell
def _(gate, profile_button, run_python):
    gate(profile_button, "the profiler")
    try:
        print(
            run_python(
                "3.15", ["-m", "profiling.sampling", "run", "-a", "--mode", "cpu", "-m", "workshop.children.mixed_load"]
            )
        )
    except RuntimeError as _e:
        print(_e)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Takeaways

    * Name your tasks (`create_task(..., name=...)`). Every tool here shows those names.
    * Inside a program, `asyncio.print_call_graph()` answers "who is waiting on whom". Put it behind a debug endpoint.
    * Outside a program, `python -m asyncio pstree PID` shows a hung service's tasks without restarting it.
      `sys.remote_exec()` and `pdb -p` let you run code in it.
    * 3.15's `profiling.sampling` profiles all threads and tasks of a live process with no code changes.
    * All the "outside" tools need permission to read the process's memory. Plan for it in containers
      (`SYS_PTRACE`) and on macOS (`sudo`).
    """)
    return


if __name__ == "__main__":
    app.run()
