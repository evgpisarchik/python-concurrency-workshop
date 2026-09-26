"""Listing 2.18: PITFALL. CPU-bound code in coroutines gets no speedup.

Use case: learn what asyncio can NOT do. It is single-threaded, so two
CPU-heavy tasks still run one after the other. For CPU-bound work, use processes
(chapter 6).

Run: uv run python -m workshop.ch02_asyncio_basics.16_cpu_bound_in_coroutines
"""

import asyncio

from workshop.common import async_timed


@async_timed()
async def cpu_bound_work() -> int:
    counter = 0
    for _ in range(50_000_000):
        counter = counter + 1
    return counter


@async_timed()
async def main():
    task_one = asyncio.create_task(cpu_bound_work())
    task_two = asyncio.create_task(cpu_bound_work())
    await task_one
    await task_two


asyncio.run(main())
