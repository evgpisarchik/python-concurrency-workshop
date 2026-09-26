"""Listing 6.5: run a process pool from asyncio with loop.run_in_executor().

Use case: do CPU-heavy work from an async app (for example, a web server
resizing images) without blocking the event loop. run_in_executor returns an
awaitable, so gather / as_completed / wait all work with it.

Run: uv run python -m workshop.ch06_cpu_bound_multiprocessing.05_process_pool_with_asyncio
"""

import asyncio
from concurrent.futures import ProcessPoolExecutor
from functools import partial


def countdown(count_from: int) -> int:
    counter = 0
    while counter < count_from:
        counter = counter + 1
    return counter


async def main():
    with ProcessPoolExecutor() as process_pool:
        loop = asyncio.get_running_loop()
        nums = [1, 3, 5, 22, 100_000_000]
        calls = [partial(countdown, num) for num in nums]  # run_in_executor takes no kwargs, so bind args
        call_coros = [loop.run_in_executor(process_pool, call) for call in calls]

        results = await asyncio.gather(*call_coros)

        for result in results:
            print(result)


if __name__ == "__main__":
    asyncio.run(main())
