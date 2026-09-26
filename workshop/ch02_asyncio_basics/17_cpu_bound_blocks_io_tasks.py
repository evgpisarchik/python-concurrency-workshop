"""Listing 2.19: PITFALL. CPU-bound tasks delay the I/O tasks too.

Use case: see how one heavy computation freezes the whole event loop. The 4 s
delay cannot even START until both CPU tasks have finished, so every other
request your server is handling stalls with it.

Run: uv run python -m workshop.ch02_asyncio_basics.17_cpu_bound_blocks_io_tasks
"""

import asyncio

from workshop.common import async_timed, delay


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
    delay_task = asyncio.create_task(delay(4))
    await task_one
    await task_two
    await delay_task


asyncio.run(main())
