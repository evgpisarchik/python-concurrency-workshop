"""Listing 2.23: debug mode reports coroutines that block the loop.

Use case: find hidden blocking code. With debug=True (or PYTHONASYNCIODEBUG=1 /
python -X dev), asyncio logs "Executing <Task ...> took N seconds" for any step
that runs longer than 100 ms without yielding.

Run: uv run python -m workshop.ch02_asyncio_basics.21_debug_mode
"""

import asyncio

from workshop.common import async_timed


@async_timed()
async def cpu_bound_work() -> int:
    counter = 0
    for _ in range(50_000_000):
        counter = counter + 1
    return counter


async def main() -> None:
    task_one = asyncio.create_task(cpu_bound_work())
    await task_one


asyncio.run(main(), debug=True)
