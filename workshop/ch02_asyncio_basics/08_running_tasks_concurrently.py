"""Listing 2.9: run several tasks at the same time.

Use case: several independent I/O waits (API calls, queries) should take as long
as the slowest one, not the sum of all of them.
Three 3 s delays finish in about 3 s total, not 9 s.

Run: uv run python -m workshop.ch02_asyncio_basics.08_running_tasks_concurrently
"""

import asyncio
import time

from workshop.common import delay


async def main():
    sleep_for_three = asyncio.create_task(delay(3))
    sleep_again = asyncio.create_task(delay(3))
    sleep_once_more = asyncio.create_task(delay(3))

    await sleep_for_three
    await sleep_again
    await sleep_once_more


start = time.perf_counter()
asyncio.run(main())
print(f"Total: {time.perf_counter() - start:.2f} s")
