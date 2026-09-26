"""Listing 8.6: read stdin without blocking the event loop.

Use case: interactive CLIs that keep doing background work while waiting for
the user. Type a number of seconds and press Enter, several times: the delays
now run concurrently. (Output and input get mixed together, which 05 fixes.)

Run: uv run python -m workshop.ch08_streams.04_async_stdin_reader   (Unix, Ctrl+C to quit)
"""

import asyncio

from workshop.ch08_streams.terminal import create_stdin_reader
from workshop.common import delay


async def main():
    stdin_reader = await create_stdin_reader()
    while True:
        delay_time = await stdin_reader.readline()
        asyncio.create_task(delay(int(delay_time)))


asyncio.run(main())
