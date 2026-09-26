"""Listing 2.17: measure coroutines with the @async_timed decorator.

Use case: prove that two tasks overlap. main() takes about 3 s (the longest
task), not 5 s. (Listing 2.16, the decorator, is in workshop/common/timer.py.)

Run: uv run python -m workshop.ch02_asyncio_basics.15_timing_coroutines
"""

import asyncio

from workshop.common import async_timed


@async_timed()
async def delay(delay_seconds: int) -> int:
    print(f"sleeping for {delay_seconds} second(s)")
    await asyncio.sleep(delay_seconds)
    print(f"finished sleeping for {delay_seconds} second(s)")
    return delay_seconds


@async_timed()
async def main():
    task_one = asyncio.create_task(delay(2))
    task_two = asyncio.create_task(delay(3))

    await task_one
    await task_two


asyncio.run(main())
