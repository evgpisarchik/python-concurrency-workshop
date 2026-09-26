"""Listing 7.6: run_in_executor(None, ...) uses the loop's default thread pool.

Use case: a one-off blocking call without creating and managing your own
pool. The default pool size is min(32, cpu_count + 4).

Run: uv run python -m workshop.ch07_threads_and_blocking_io.06_default_executor
"""

import asyncio
import functools

import requests

from workshop.common import async_timed


def get_status_code(url: str) -> int:
    response = requests.get(url)
    return response.status_code


@async_timed()
async def main():
    loop = asyncio.get_running_loop()
    urls = ["https://www.example.com" for _ in range(100)]
    tasks = [loop.run_in_executor(None, functools.partial(get_status_code, url)) for url in urls]
    results = await asyncio.gather(*tasks)
    print(results)


asyncio.run(main())
