"""Bonus (Python 3.11+): structured concurrency with asyncio.TaskGroup.

Use case: start a group of tasks and guarantee that none outlive the block.
If any task fails, the others are cancelled and the errors come back together
as an ExceptionGroup (handled with `except*`). This is the modern replacement for
most create_task + gather code.

Run: uv run python -m workshop.ch02_asyncio_basics.23_task_group_modern
"""

import asyncio

from workshop.common import async_timed, delay


async def fail_after(seconds: float) -> None:
    await asyncio.sleep(seconds)
    raise ValueError(f"failed after {seconds}s")


@async_timed()
async def main():
    async with asyncio.TaskGroup() as tg:
        first = tg.create_task(delay(1))
        second = tg.create_task(delay(2))
    print(f"All done: {first.result()=}, {second.result()=}")

    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(delay(5))  # gets cancelled when the sibling fails
            tg.create_task(fail_after(1))
    except* ValueError as group:
        print(f"Caught: {group.exceptions}")


asyncio.run(main())
