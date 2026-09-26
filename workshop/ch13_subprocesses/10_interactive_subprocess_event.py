"""Listing 13.14: drive an interactive program by waiting for its prompt.

Use case: automate interactive CLIs (like `expect`). One task consumes
output and sets an Event when it sees the prompt. Another task writes the next
input only after that Event is set.

Run: uv run python -m workshop.ch13_subprocesses.10_interactive_subprocess_event
"""

import asyncio
import sys
from asyncio import Event, StreamReader, StreamWriter
from asyncio.subprocess import Process
from pathlib import Path

CHILD = Path(__file__).with_name("child_echo_slow.py")


async def output_consumer(input_ready_event: Event, stdout: StreamReader):
    while (data := await stdout.read(1024)) != b"":
        print(data)
        if data.decode().endswith("Enter text to echo: "):
            input_ready_event.set()


async def input_writer(text_data, input_ready_event: Event, stdin: StreamWriter):
    for text in text_data:
        await input_ready_event.wait()
        stdin.write(text.encode())
        await stdin.drain()
        input_ready_event.clear()


async def main():
    process: Process = await asyncio.create_subprocess_exec(
        sys.executable, str(CHILD), stdout=asyncio.subprocess.PIPE, stdin=asyncio.subprocess.PIPE
    )

    input_ready_event = asyncio.Event()

    text_input = ["one\n", "two\n", "three\n", "four\n", "quit\n"]

    await asyncio.gather(
        output_consumer(input_ready_event, process.stdout),
        input_writer(text_input, input_ready_event, process.stdin),
        process.wait(),
    )


asyncio.run(main())
