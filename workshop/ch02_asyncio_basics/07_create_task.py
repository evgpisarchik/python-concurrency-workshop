"""Listing 2.8: wrap a coroutine in a Task to schedule it on the event loop.

Use case: start a coroutine "in the background". create_task() schedules it
right away and returns a Task. You can await the Task later to get its result.

Run: uv run python -m workshop.ch02_asyncio_basics.07_create_task
"""

import asyncio

from workshop.common import delay


async def main():
    sleep_for_three = asyncio.create_task(delay(3))
    print(type(sleep_for_three))
    result = await sleep_for_three
    print(result)


asyncio.run(main())
