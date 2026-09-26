"""Listing 8.4: PITFALL. input() blocks the event loop.

Use case: see why console apps need async stdin. The delay tasks are
created but never make progress while input() blocks the only thread. Nothing
prints "finished sleeping" until you press Enter again.

Run: uv run python -m workshop.ch08_streams.03_blocking_input_pitfall   (Ctrl+C to quit)
"""

import asyncio

from workshop.common import delay


async def main():
    while True:
        delay_time = input("Enter a time to sleep:")
        asyncio.create_task(delay(int(delay_time)))


asyncio.run(main())
