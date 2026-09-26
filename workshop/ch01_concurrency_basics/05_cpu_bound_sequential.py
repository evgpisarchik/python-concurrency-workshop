"""Listing 1.5: CPU-bound work, one after another (the baseline).

Use case: measure the baseline before trying to speed CPU-bound code up.
Compare the time with 06_cpu_bound_with_threads_gil.py.

Run: uv run python -m workshop.ch01_concurrency_basics.05_cpu_bound_sequential
"""

import time

from workshop.ch01_concurrency_basics.fib import print_fib

start = time.perf_counter()

print_fib(35)
print_fib(36)

print(f"Completed in {time.perf_counter() - start:.4f} seconds.")
