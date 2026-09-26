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
    import time

    import marimo as mo

    from workshop.children import ASK_USERNAME, ECHO_SLOW, LOTS_OF_OUTPUT

    return (
        ASK_USERNAME,
        ECHO_SLOW,
        LOTS_OF_OUTPUT,
        asyncio,
        mo,
        os,
        random,
        sys,
        time,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Run, wait, time out

    *Listings 13.1, 13.2.* Use `create_subprocess_exec` (no shell: safer than `create_subprocess_shell`). When a tool hangs,
    time out, `terminate()` it, and then `wait()` again to reap it.
    """)
    return


@app.cell
async def _(asyncio):
    _process = await asyncio.create_subprocess_exec("ls", "-l", stdout=asyncio.subprocess.DEVNULL)
    print(f"ls: pid {_process.pid}, exit code {await _process.wait()}")

    _process = await asyncio.create_subprocess_exec("sleep", "3")
    try:
        _ = await asyncio.wait_for(_process.wait(), timeout=1)
    except TimeoutError:
        _process.terminate()
        print(
            f"sleep 3 timed out after 1 s; terminated, exit code {await _process.wait()} (negative = killed by signal)"
        )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Stream output while it runs

    *Listing 13.3.* Read `stdout` line by line **concurrently** with waiting for the exit code: live build logs, `tail -f`, and so on.
    """)
    return


@app.cell
async def _(asyncio, sys):
    async def write_output(prefix: str, stdout: asyncio.StreamReader):
        while line := await stdout.readline():
            print(f"[{prefix}] {line.decode().rstrip()}")

    _program = [sys.executable, "-u", "-c", "import time\nfor i in range(4):\n    print(f'step {i}'); time.sleep(0.3)"]
    _process = await asyncio.create_subprocess_exec(*_program, stdout=asyncio.subprocess.PIPE)
    _code, _ = await asyncio.gather(_process.wait(), write_output("child", _process.stdout))
    print(f"exit code {_code}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Pitfall: an unread pipe leads to deadlock

    *Listings 13.4–13.6.* The child writes ~14 MB. The OS pipe buffer holds ~64 KB, so once it's full the child blocks on
    `write()`. We block on `wait()` for the child to exit, so neither side can make progress.
    **Always read the pipes you open**: stream them, or use `communicate()`, which reads everything safely (but buffers it all in memory).
    """)
    return


@app.cell
async def _(LOTS_OF_OUTPUT, asyncio, sys):
    _process = await asyncio.create_subprocess_exec(sys.executable, str(LOTS_OF_OUTPUT), stdout=asyncio.subprocess.PIPE)
    try:
        await asyncio.wait_for(_process.wait(), timeout=2)
    except TimeoutError:
        print("wait() never returned: the child is stuck writing to a full pipe that nobody reads")
        _process.kill()
        await _process.communicate()  # drain the pipe, otherwise even cleanup would hang

    _process = await asyncio.create_subprocess_exec(sys.executable, str(LOTS_OF_OUTPUT), stdout=asyncio.subprocess.PIPE)
    _stdout, _ = await _process.communicate()
    print(f"communicate(): read {len(_stdout):,} bytes, exit code {_process.returncode}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Many processes at once, with a limit

    *Listings 13.7, 13.8.* Compress 32 inputs with `gzip -9`, a CPU-heavy external tool. Running them concurrently uses
    every core. Starting **all** of them at once can overload the machine (and hit process/file limits), so cap them with
    `Semaphore(cpu_count)`.
    """)
    return


@app.cell
def _(asyncio, os, random):
    _words = (
        open("/usr/share/dict/words").read().split()
        if os.path.exists("/usr/share/dict/words")
        else ["asyncio", "thread", "process", "event", "loop"]
    )
    gzip_inputs = [" ".join(random.choices(_words, k=400_000)).encode() for _ in range(32)]

    async def gzip(data: bytes, semaphore: asyncio.Semaphore | None = None) -> bytes:
        async def run():
            process = await asyncio.create_subprocess_exec(
                "gzip", "-9", "-c", stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE
            )
            compressed, _ = await process.communicate(data)
            return compressed

        if semaphore is None:
            return await run()
        async with semaphore:
            return await run()

    return gzip, gzip_inputs


@app.cell
async def _(asyncio, gzip, gzip_inputs, mo, os, time):
    _start = time.perf_counter()
    for _data in gzip_inputs:
        await gzip(_data)
    _sequential = time.perf_counter() - _start

    _start = time.perf_counter()
    await asyncio.gather(*(gzip(_d) for _d in gzip_inputs))
    _all_at_once = time.perf_counter() - _start

    _semaphore = asyncio.Semaphore(os.cpu_count())
    _start = time.perf_counter()
    await asyncio.gather(*(gzip(_d, _semaphore) for _d in gzip_inputs))
    _limited = time.perf_counter() - _start

    mo.md(f"""
    | 32 × `gzip -9` (~{len(gzip_inputs[0]) // 1_000_000} MB each) | seconds |
    |---|---|
    | one at a time | {_sequential:.2f} |
    | all 32 at once | {_all_at_once:.2f} |
    | at most {os.cpu_count()} at once (Semaphore) | {_limited:.2f} |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Talking to a program's stdin

    *Listing 13.10.* `communicate(input)` covers the simple case: send everything, then read everything.
    """)
    return


@app.cell
async def _(ASK_USERNAME, asyncio, sys):
    _process = await asyncio.create_subprocess_exec(
        sys.executable, str(ASK_USERNAME), stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE
    )
    _stdout, _ = await _process.communicate(b"Zoot\n")
    print(_stdout.decode())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Interactive programs: wait for the prompt

    *Listings 13.11–13.14.* The child prompts `Enter text to echo: `, then prints the input 0–9 times, slowly (unbuffered, `-u`, so output arrives bit by bit like a real interactive tool).

    **Naive:** read once, write the next input. A single `read()` returns whatever happens to be available, so our inputs get
    out of step with the prompts.
    **Correct (like `expect`):** one task reads output and sets an `Event` when it sees the prompt. Another task writes the
    next input only after that event is set.
    """)
    return


@app.cell
async def _(ECHO_SLOW, asyncio, random, sys):
    async def naive(texts: list[str]) -> list[bytes]:
        process = await asyncio.create_subprocess_exec(
            sys.executable, "-u", str(ECHO_SLOW), stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE
        )
        seen = []
        for text in texts:
            seen.append(await process.stdout.read(2048))  # whatever is there right now
            process.stdin.write(text.encode())
            await process.stdin.drain()
        await process.communicate()
        return seen

    async def prompt_driven(texts: list[str]) -> list[bytes]:
        process = await asyncio.create_subprocess_exec(
            sys.executable, "-u", str(ECHO_SLOW), stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE
        )
        ready, seen = asyncio.Event(), []

        async def output_consumer():
            while data := await process.stdout.read(1024):
                seen.append(data)
                if data.endswith(b"Enter text to echo: "):
                    ready.set()

        async def input_writer():
            for text in texts:
                await ready.wait()
                ready.clear()
                process.stdin.write(text.encode())
                await process.stdin.drain()

        await asyncio.gather(output_consumer(), input_writer(), process.wait())
        return seen

    random.seed(7)
    _texts = ["one\n", "two\n", "three\n", "quit\n"]
    print("--- naive: prompts and inputs out of step")
    for _chunk in await asyncio.wait_for(naive(_texts), 30):
        print("  ", _chunk)
    print("--- prompt-driven: every input answers a prompt")
    for _chunk in await asyncio.wait_for(prompt_driven(_texts), 30):
        print("  ", _chunk)
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
