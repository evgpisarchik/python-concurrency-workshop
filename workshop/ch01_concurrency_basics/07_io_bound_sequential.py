"""Listing 1.7: I/O-bound work, one after another (the baseline).

Use case: the baseline for 08_io_bound_with_threads.py. Each request spends most
of its time waiting on the network.

Run: uv run python -m workshop.ch01_concurrency_basics.07_io_bound_sequential
"""

import time

import requests


def read_example() -> None:
    response = requests.get("https://www.example.com")
    print(response.status_code)


start = time.perf_counter()

read_example()
read_example()

print(f"Running synchronously took {time.perf_counter() - start:.4f} seconds.")
