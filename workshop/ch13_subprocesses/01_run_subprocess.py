"""Listing 13.1: run an external program without blocking the event loop.

Use case: call CLI tools (ffmpeg, git, kubectl, ls) from async code.
create_subprocess_exec returns right away, and `await process.wait()` waits
for the exit code without blocking other tasks.

Run: uv run python -m workshop.ch13_subprocesses.01_run_subprocess
"""

import asyncio
from asyncio.subprocess import Process


async def main():
    process: Process = await asyncio.create_subprocess_exec("ls", "-l")
    print(f"Process pid is: {process.pid}")
    status_code = await process.wait()
    print(f"Status code: {status_code}")


asyncio.run(main())
