import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium", app_title="13 · Subprocesses")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 13 · Subprocesses: running external programs concurrently

    `asyncio.create_subprocess_exec` starts a program and returns right away. Waiting for it, reading its output and
    writing its input are all awaitable, so the event loop keeps running. External programs are separate OS processes,
    which means **free parallelism with no GIL**.
    """)
    return


@app.cell
def _():
    import asyncio
    import os
    import random
    import sys
    from asyncio.subprocess import DEVNULL, PIPE

    import marimo as mo

    from workshop.common import timed

    return DEVNULL, PIPE, asyncio, mo, os, random, sys, timed


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Run, wait, time out

    *Listings 13.1, 13.2.* Use `create_subprocess_exec` (no shell: safer than `create_subprocess_shell`). When a tool hangs,
    time out, `terminate()` it, and then `wait()` again to reap it.
    """)
    return


@app.cell
async def _(DEVNULL, asyncio):
    _process = await asyncio.create_subprocess_exec("ls", "-l", stdout=DEVNULL)
    print("ls exited with", await _process.wait())

    _process = await asyncio.create_subprocess_exec("sleep", "3")
    try:
        await asyncio.wait_for(_process.wait(), timeout=1)
    except TimeoutError:
        _process.terminate()
        print(
            "sleep 3 timed out after 1 s; terminated, exit code", await _process.wait()
        )  # negative: killed by a signal
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Stream output while it runs

    *Listing 13.3.* `process.stdout` is a `StreamReader`, so you can read it line by line **while the program runs**:
    live build logs, `tail -f`, and so on.
    """)
    return


@app.cell
async def _(PIPE, asyncio):
    _process = await asyncio.create_subprocess_exec(
        "sh", "-c", "for i in 1 2 3; do echo step $i; sleep 0.3; done", stdout=PIPE
    )
    async for _line in _process.stdout:
        print("child says:", _line.decode().strip())
    print("exit code", await _process.wait())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Pitfall: an unread pipe leads to deadlock

    *Listings 13.4–13.6.* `workshop/children/lots_of_output.py` writes ~14 MB. The OS pipe buffer holds ~64 KB, so once
    it's full the child blocks on `write()`. We block on `wait()` for the child to exit, so neither side can make progress.
    **Always read the pipes you open**: stream them, or use `communicate()`, which reads everything safely (but buffers
    it all in memory).
    """)
    return


@app.cell
async def _(PIPE, asyncio, sys):
    _child = [sys.executable, "-m", "workshop.children.lots_of_output"]

    _process = await asyncio.create_subprocess_exec(*_child, stdout=PIPE)
    try:
        await asyncio.wait_for(_process.wait(), timeout=2)
    except TimeoutError:
        print("wait() never returned: the child is stuck writing to a full pipe that nobody reads")
        _process.kill()
        await _process.communicate()

    _process = await asyncio.create_subprocess_exec(*_child, stdout=PIPE)
    _stdout, _ = await _process.communicate()
    print(f"communicate() read {len(_stdout):,} bytes")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Many processes at once, with a limit

    *Listings 13.7, 13.8.* Compress 32 inputs with `gzip -9`, a CPU-heavy external tool. Running them concurrently uses
    every core. Starting **all** of them at once can overload the machine (and hit process/file limits), so cap them with
    a `Semaphore`.
    """)
    return


@app.cell
async def _(PIPE, asyncio, os, random, timed):
    _inputs = [random.randbytes(2_000_000) for _ in range(32)]

    async def gzip(data: bytes, limit: asyncio.Semaphore) -> bytes:
        async with limit:
            process = await asyncio.create_subprocess_exec("gzip", "-9", "-c", stdin=PIPE, stdout=PIPE)
            compressed, _ = await process.communicate(data)
            return compressed

    async def compress_all(at_once: int):
        limit = asyncio.Semaphore(at_once)
        await asyncio.gather(*(gzip(data, limit) for data in _inputs))

    with timed("one at a time"):
        await compress_all(1)
    with timed(f"at most {os.cpu_count()} at once"):
        await compress_all(os.cpu_count())
    with timed("all 32 at once"):
        await compress_all(32)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Talking to a program's stdin

    *Listing 13.10.* `communicate(input)` covers the simple case: send everything, then read everything.
    """)
    return


@app.cell
async def _(PIPE, asyncio, sys):
    _process = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "workshop.children.ask_username", stdin=PIPE, stdout=PIPE
    )
    _stdout, _ = await _process.communicate(b"Zoot\n")
    print(_stdout.decode())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Interactive programs: wait for the prompt

    *Listings 13.11–13.14.* `workshop/children/echo_slow.py` prompts `Enter text to echo: `, then prints the input 0–9
    times, slowly, like a real interactive tool.

    **Naive:** read once, write the next input. A single `read()` returns whatever happens to be available, so our inputs get
    out of step with the prompts.
    **Correct (like `expect`):** one task reads output and sets an `Event` when it sees the prompt. Another task writes the
    next input only after that event is set.
    """)
    return


@app.cell
def _(PIPE, asyncio, sys):
    class EchoSlowClient:
        """Drives workshop/children/echo_slow.py through its stdin and stdout."""

        PROMPT = b"Enter text to echo: "

        def __init__(self):
            self.seen = []  # every chunk of output, in order
            self._process = None

        async def send_naively(self, texts: list[str]) -> list[bytes]:
            await self._start()
            for text in texts:
                self.seen.append(await self._process.stdout.read(1024))  # whatever is there right now
                self._process.stdin.write(text.encode())
            await self._process.communicate()
            return self.seen

        async def send_on_prompt(self, texts: list[str]) -> list[bytes]:
            await self._start()
            prompt_shown = asyncio.Event()

            async def read_output():
                while data := await self._process.stdout.read(1024):
                    self.seen.append(data)
                    if data.endswith(self.PROMPT):
                        prompt_shown.set()

            async def write_input():
                for text in texts:
                    await prompt_shown.wait()
                    prompt_shown.clear()
                    self._process.stdin.write(text.encode())

            await asyncio.gather(read_output(), write_input())
            return self.seen

        async def _start(self):
            self._process = await asyncio.create_subprocess_exec(
                sys.executable, "-u", "-m", "workshop.children.echo_slow", stdin=PIPE, stdout=PIPE
            )

    return (EchoSlowClient,)


@app.cell
async def _(EchoSlowClient):
    _texts = ["one\n", "two\n", "three\n", "quit\n"]
    print("naive: prompts and inputs out of step", *await EchoSlowClient().send_naively(_texts), sep="\n    ")
    print("prompt-driven: every input answers a prompt", *await EchoSlowClient().send_on_prompt(_texts), sep="\n    ")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Takeaways

    * Subprocesses are awaitable: run, stream, time out, and terminate without blocking the loop.
    * Read every pipe you open (stream it or `communicate()`), or you risk a deadlock.
    * External tools give easy parallelism. Limit how many run at once with a semaphore.
    * For interactive programs, synchronize on the output (an `Event` when the prompt appears), not on timing.
    """)
    return


if __name__ == "__main__":
    app.run()
