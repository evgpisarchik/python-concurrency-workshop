"""Listing 6.1: run two CPU-bound functions in parallel processes.

Use case: real parallelism for CPU-heavy work. Each process has its own
interpreter and GIL, so the total time is about max(a, b), not a + b.

Run: uv run python -m workshop.ch06_cpu_bound_multiprocessing.01_parallel_processes
"""

import time
from multiprocessing import Process

from workshop.ch06_cpu_bound_multiprocessing.count import count

if __name__ == "__main__":
    start_time = time.perf_counter()

    to_one_hundred_million = Process(target=count, args=(100_000_000,))
    to_two_hundred_million = Process(target=count, args=(200_000_000,))

    to_one_hundred_million.start()
    to_two_hundred_million.start()

    to_one_hundred_million.join()
    to_two_hundred_million.join()

    print(f"Completed in {time.perf_counter() - start_time:.4f}")
