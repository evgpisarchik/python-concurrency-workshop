"""Listing 14.3: `await asyncio.sleep(0)` forces one iteration of the event loop.

Use case: let freshly created tasks start right away, or yield inside
a long CPU loop so other tasks get a turn (cooperative multitasking).
Compare the order of the "sleeping for" prints in the two runs.

Run: uv run python -m workshop.ch14_advanced_asyncio.03_sleep_zero_yield
"""

import asyncio

from workshop.common import delay


async def create_tasks_no_sleep():
    task1 = asyncio.create_task(delay(1))
    task2 = asyncio.create_task(delay(2))
    print("Gathering tasks:")
    await asyncio.gather(task1, task2)


async def create_tasks_sleep():
    task1 = asyncio.create_task(delay(1))
    await asyncio.sleep(0)
    task2 = asyncio.create_task(delay(2))
    await asyncio.sleep(0)
    print("Gathering tasks:")
    await asyncio.gather(task1, task2)


async def main():
    print("--- Testing without asyncio.sleep(0) ---")
    await create_tasks_no_sleep()
    print("--- Testing with asyncio.sleep(0) ---")
    await create_tasks_sleep()


asyncio.run(main())
