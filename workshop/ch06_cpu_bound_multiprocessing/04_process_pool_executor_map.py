"""Listing 6.4: concurrent.futures.ProcessPoolExecutor.map().

Use case: the standard executor API (the same interface as ThreadPoolExecutor).
map() returns results in input order, so a slow first item delays all
the results after it.

Run: uv run python -m workshop.ch06_cpu_bound_multiprocessing.04_process_pool_executor_map
"""

from concurrent.futures import ProcessPoolExecutor

from workshop.ch06_cpu_bound_multiprocessing.count import count

if __name__ == "__main__":
    with ProcessPoolExecutor() as process_pool:
        numbers = [1, 3, 5, 22, 100_000_000]
        for result in process_pool.map(count, numbers):
            print(result)
