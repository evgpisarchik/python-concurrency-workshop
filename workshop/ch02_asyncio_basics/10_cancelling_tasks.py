"""Listing 2.11: cancel a task that takes too long.

Use case: the user navigates away, a shutdown starts, or a result is no longer
needed. task.cancel() raises CancelledError inside the task at its next `await`.

Run: uv run python -m workshop.ch02_asyncio_basics.10_cancelling_tasks
"""

import asyncio
from asyncio import CancelledError

from workshop.common import delay


async def main():
    long_task = asyncio.create_task(delay(10))

    seconds_elapsed = 0

    while not long_task.done():
        print("Task not finished, checking again in a second.")
        await asyncio.sleep(1)
        seconds_elapsed = seconds_elapsed + 1
        if seconds_elapsed == 5:
            long_task.cancel()

    try:
        await long_task
    except CancelledError:
        print("Our task was cancelled")


asyncio.run(main())
