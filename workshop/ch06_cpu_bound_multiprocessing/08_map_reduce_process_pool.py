"""Listing 6.8: parallel MapReduce with asyncio + ProcessPoolExecutor.

Use case: split a big dataset into chunks, map them on all CPU cores, then
reduce. Try different partition sizes: chunks that are too small waste time
pickling data between processes, and chunks that are too large leave cores idle.

Run: uv run python -m workshop.ch06_cpu_bound_multiprocessing.08_map_reduce_process_pool
"""

import asyncio
import concurrent.futures
import functools
import time

from workshop.ch06_cpu_bound_multiprocessing.map_reduce import (
    map_frequencies,
    merge_dictionaries,
    partition,
    read_ngrams,
)


async def main(partition_size: int):
    contents = read_ngrams()
    loop = asyncio.get_running_loop()
    tasks = []
    start = time.perf_counter()
    with concurrent.futures.ProcessPoolExecutor() as pool:
        for chunk in partition(contents, partition_size):
            tasks.append(loop.run_in_executor(pool, functools.partial(map_frequencies, chunk)))

        intermediate_results = await asyncio.gather(*tasks)
        final_result = functools.reduce(merge_dictionaries, intermediate_results)

        print(f"Aardvark has appeared {final_result['Aardvark']} times.")
        print(f"MapReduce took: {(time.perf_counter() - start):.4f} seconds")


if __name__ == "__main__":
    asyncio.run(main(partition_size=60_000))
