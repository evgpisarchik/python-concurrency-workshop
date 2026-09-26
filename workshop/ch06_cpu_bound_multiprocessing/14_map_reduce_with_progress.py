"""Listing 6.14: report MapReduce progress from a shared counter.

Use case: show live progress for a long parallel job. Workers increment a
shared Value, and an asyncio task in the parent process prints it every second
while the event loop waits for the pool.

Run: uv run python -m workshop.ch06_cpu_bound_multiprocessing.14_map_reduce_with_progress
"""

import asyncio
import functools
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Value

from workshop.ch06_cpu_bound_multiprocessing.map_reduce import merge_dictionaries, partition, read_ngrams

map_progress = None


def init(progress):
    global map_progress
    map_progress = progress


def map_frequencies(chunk: list[str]) -> dict[str, int]:
    counter = {}
    for line in chunk:
        word, _, count, _ = line.split("\t")
        if counter.get(word):
            counter[word] = counter[word] + int(count)
        else:
            counter[word] = int(count)

    with map_progress.get_lock():
        map_progress.value += 1

    return counter


async def progress_reporter(total_partitions: int):
    while map_progress.value < total_partitions:
        print(f"Finished {map_progress.value}/{total_partitions} map operations")
        await asyncio.sleep(1)


async def main(partition_size: int):
    global map_progress

    contents = read_ngrams()
    loop = asyncio.get_running_loop()
    tasks = []
    map_progress = Value("i", 0)

    with ProcessPoolExecutor(initializer=init, initargs=(map_progress,)) as pool:
        total_partitions = len(contents) // partition_size
        reporter = asyncio.create_task(progress_reporter(total_partitions))

        for chunk in partition(contents, partition_size):
            tasks.append(loop.run_in_executor(pool, functools.partial(map_frequencies, chunk)))

        counters = await asyncio.gather(*tasks)

        await reporter

        final_result = functools.reduce(merge_dictionaries, counters)

        print(f"Aardvark has appeared {final_result['Aardvark']} times.")


if __name__ == "__main__":
    asyncio.run(main(partition_size=60_000))
