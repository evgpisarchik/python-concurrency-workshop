"""Listing 7.19: compute row means in a thread pool.

Use case: numpy releases the GIL inside most operations, so one row per
thread gives real parallel speedup for large arrays.

Run: uv run python -m workshop.ch07_threads_and_blocking_io.17_numpy_mean_threads
"""

import asyncio
import functools
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from workshop.common import async_timed


def mean_for_row(arr, row):
    return np.mean(arr[row])


DATA_POINTS = 100_000_000
rows = 50
columns = DATA_POINTS // rows

matrix = np.arange(DATA_POINTS).reshape(rows, columns)


@async_timed()
async def main():
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        tasks = []
        for i in range(rows):
            mean = functools.partial(mean_for_row, matrix, i)
            tasks.append(loop.run_in_executor(pool, mean))

        results = await asyncio.gather(*tasks)
        print(results[:3], "...")


asyncio.run(main())
