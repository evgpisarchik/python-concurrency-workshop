"""Listing 6.13: share a Value with pool workers through an initializer.

Use case: pool workers can't receive a shared Value as a normal argument
(it can't be pickled per task). Pass it once, when each worker starts, and
store it in a module-level global.

Run: uv run python -m workshop.ch06_cpu_bound_multiprocessing.13_shared_state_in_pool_initializer
"""

import asyncio
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Value

shared_counter = None


def init(counter):
    global shared_counter
    shared_counter = counter


def increment():
    with shared_counter.get_lock():
        shared_counter.value += 1


async def main():
    counter = Value("d", 0)
    with ProcessPoolExecutor(initializer=init, initargs=(counter,)) as pool:
        await asyncio.get_running_loop().run_in_executor(pool, increment)
        print(counter.value)


if __name__ == "__main__":
    asyncio.run(main())
