"""Listing 2.13: asyncio.shield() stops a timeout from cancelling the task.

Use case: tell the user "this is taking longer than expected" after N seconds,
but let the work (for example, a payment) finish instead of cancelling it.

Run: uv run python -m workshop.ch02_asyncio_basics.12_shield_from_cancellation
"""

import asyncio

from workshop.common import delay


async def main():
    task = asyncio.create_task(delay(10))

    try:
        result = await asyncio.wait_for(asyncio.shield(task), 5)
        print(result)
    except TimeoutError:
        print("Task took longer than five seconds!")
        result = await task  # the task was not cancelled, so we can keep waiting
        print(result)


asyncio.run(main())
