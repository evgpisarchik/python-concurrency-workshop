"""Listing 13.12: PITFALL. Talking to an interactive program naively.

Use case: see why "read once, write once" breaks with interactive
programs. The child prints a random number of lines slowly, so a single read()
returns partial output and our input gets out of sync with its prompts.

Run: uv run python -m workshop.ch13_subprocesses.09_interactive_subprocess_naive
"""

import asyncio
import sys
from asyncio import StreamReader, StreamWriter
from asyncio.subprocess import Process
from pathlib import Path

CHILD = Path(__file__).with_name("child_echo_slow.py")


async def consume_and_send(text_list, stdout: StreamReader, stdin: StreamWriter):
    for text in text_list:
        line = await stdout.read(2048)
        print(line)
        stdin.write(text.encode())
        await stdin.drain()


async def main():
    process: Process = await asyncio.create_subprocess_exec(
        sys.executable, str(CHILD), stdout=asyncio.subprocess.PIPE, stdin=asyncio.subprocess.PIPE
    )

    text_input = ["one\n", "two\n", "three\n", "four\n", "quit\n"]

    await asyncio.gather(consume_and_send(text_input, process.stdout, process.stdin), process.wait())


asyncio.run(main())
