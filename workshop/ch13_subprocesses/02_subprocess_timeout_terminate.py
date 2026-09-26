"""Listing 13.2: time out a subprocess and terminate it.

Use case: don't let a hung external tool hang your service. Wait with a
timeout, send SIGTERM, then reap the process (wait() again).

Run: uv run python -m workshop.ch13_subprocesses.02_subprocess_timeout_terminate
"""

import asyncio
from asyncio.subprocess import Process


async def main():
    process: Process = await asyncio.create_subprocess_exec("sleep", "3")
    print(f"Process pid is: {process.pid}")
    try:
        status_code = await asyncio.wait_for(process.wait(), timeout=1.0)
        print(status_code)
    except TimeoutError:
        print("Timed out waiting to finish, terminating...")
        process.terminate()
        status_code = await process.wait()
        print(status_code)  # negative = killed by that signal (-15 = SIGTERM)


asyncio.run(main())
