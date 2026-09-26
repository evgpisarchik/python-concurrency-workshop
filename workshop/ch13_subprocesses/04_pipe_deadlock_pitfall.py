"""Listing 13.5: PITFALL. wait() + a PIPE nobody reads leads to deadlock.

Use case: see a classic subprocess bug. The child fills the OS pipe buffer
(~64 KB) and blocks on write, while we block on wait() for it to exit. Neither can
make progress. (We detect it with a 3 s timeout, but the book version hangs forever.)
Fix: read the pipe (listing 13.3) or use communicate() (listing 13.6).

Run: uv run python -m workshop.ch13_subprocesses.04_pipe_deadlock_pitfall
"""

import asyncio
import sys
from asyncio.subprocess import Process
from pathlib import Path

CHILD = Path(__file__).with_name("child_lots_of_output.py")


async def main():
    process: Process = await asyncio.create_subprocess_exec(sys.executable, str(CHILD), stdout=asyncio.subprocess.PIPE)
    print(f"Process pid is: {process.pid}")

    try:
        return_code = await asyncio.wait_for(process.wait(), timeout=3)
        print(f"Process returned: {return_code}")
    except TimeoutError:
        print("Deadlocked: the child is blocked writing to a full pipe that we never read.")
        process.kill()
        await process.communicate()  # drain the pipe, or wait() would hang waiting for it to close


asyncio.run(main())
