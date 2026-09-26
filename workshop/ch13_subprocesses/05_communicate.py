"""Listing 13.6: communicate() reads all output safely.

Use case: run a command and collect its full stdout/stderr with no deadlock
risk. The catch: everything is buffered in memory, so for huge or endless
output, stream it instead (listing 13.3).

Run: uv run python -m workshop.ch13_subprocesses.05_communicate
"""

import asyncio
import sys
from asyncio.subprocess import Process
from pathlib import Path

CHILD = Path(__file__).with_name("child_lots_of_output.py")


async def main():
    process: Process = await asyncio.create_subprocess_exec(sys.executable, str(CHILD), stdout=asyncio.subprocess.PIPE)
    print(f"Process pid is: {process.pid}")

    stdout, stderr = await process.communicate()
    print(f"Got {len(stdout):,} bytes of stdout: {stdout[:28]}...")
    print(stderr)
    print(f"Process returned: {process.returncode}")


asyncio.run(main())
