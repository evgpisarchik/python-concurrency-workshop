"""Listing 13.10: send input to a subprocess with communicate(input).

Use case: drive a program that reads stdin once (answer a prompt, pipe
data into a filter like `sort` or `jq`).

Run: uv run python -m workshop.ch13_subprocesses.08_communicate_stdin
"""

import asyncio
import sys
from asyncio.subprocess import Process
from pathlib import Path

CHILD = Path(__file__).with_name("child_ask_username.py")


async def main():
    process: Process = await asyncio.create_subprocess_exec(
        sys.executable, str(CHILD), stdout=asyncio.subprocess.PIPE, stdin=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate(b"Zoot")
    print(stdout)
    print(stderr)


asyncio.run(main())
