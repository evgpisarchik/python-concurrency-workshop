"""Listing 2.24: set the "slow callback" threshold used by debug mode.

Use case: latency-sensitive services where even 50 ms of blocking matters.
The default threshold is 100 ms.

Run: uv run python -m workshop.ch02_asyncio_basics.22_slow_callback_duration
"""

import asyncio
import time


async def main():
    loop = asyncio.get_running_loop()
    loop.slow_callback_duration = 0.250
    time.sleep(0.3)  # blocks longer than the threshold, so it gets reported


asyncio.run(main(), debug=True)
