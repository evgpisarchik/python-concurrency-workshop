"""Listing 7.4: ThreadPoolExecutor.map() for blocking I/O.

Use case: speed up code that uses a blocking library (requests, boto3,
psycopg2, a legacy SDK) without asyncio. Threads are fine for I/O because the
GIL is released while waiting on sockets.

Run: uv run python -m workshop.ch07_threads_and_blocking_io.04_thread_pool_executor
"""

import time
from concurrent.futures import ThreadPoolExecutor

import requests


def get_status_code(url: str) -> int:
    response = requests.get(url)
    return response.status_code


start = time.perf_counter()

with ThreadPoolExecutor(max_workers=100) as pool:
    urls = ["https://www.example.com" for _ in range(100)]
    results = pool.map(get_status_code, urls)
    for result in results:
        print(result)

print(f"finished requests in {time.perf_counter() - start:.4f} second(s)")
