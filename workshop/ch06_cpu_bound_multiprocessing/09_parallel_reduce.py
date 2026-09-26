"""Listing 6.9: parallelize the REDUCE step as well.

Use case: when there are many partial results, reducing them one by one
becomes the bottleneck. Merge them in parallel batches (a tree of merges)
until one dictionary is left.

Run: uv run python -m workshop.ch06_cpu_bound_multiprocessing.09_parallel_reduce
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


async def reduce(loop, pool, counters, chunk_size) -> dict[str, int]:
    chunks: list[list[dict]] = list(partition(counters, chunk_size))
    reducers = []
    while len(chunks[0]) > 1:
        for chunk in chunks:
            reducer = functools.partial(functools.reduce, merge_dictionaries, chunk)
            reducers.append(loop.run_in_executor(pool, reducer))
        reducer_chunks = await asyncio.gather(*reducers)
        chunks = list(partition(reducer_chunks, chunk_size))
        reducers.clear()
    return chunks[0][0]


async def main(partition_size: int):
    contents = read_ngrams()
    loop = asyncio.get_running_loop()
    tasks = []
    with concurrent.futures.ProcessPoolExecutor() as pool:
        start = time.perf_counter()

        for chunk in partition(contents, partition_size):
            tasks.append(loop.run_in_executor(pool, functools.partial(map_frequencies, chunk)))

        intermediate_results = await asyncio.gather(*tasks)
        final_result = await reduce(loop, pool, intermediate_results, 500)

        print(f"Aardvark has appeared {final_result['Aardvark']} times.")
        print(f"MapReduce took: {(time.perf_counter() - start):.4f} seconds")


if __name__ == "__main__":
    asyncio.run(main(partition_size=60_000))
