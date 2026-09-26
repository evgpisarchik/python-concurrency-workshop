"""Listing 7.5: use a blocking library from asyncio with run_in_executor.

Use case: you're in an async app but the only SDK available is blocking. Run it
in a thread pool and `await` it like any other coroutine, and the event loop
stays responsive.

Run: uv run python -m workshop.ch07_threads_and_blocking_io.05_thread_pool_with_asyncio
"""

import asyncio
import functools
from concurrent.futures import ThreadPoolExecutor

import requests

from workshop.common import async_timed


def get_status_code(url: str) -> int:
    response = requests.get(url)
    return response.status_code


@async_timed()
async def main():
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        urls = ["https://www.example.com" for _ in range(100)]
        tasks = [loop.run_in_executor(pool, functools.partial(get_status_code, url)) for url in urls]
        results = await asyncio.gather(*tasks)
        print(results)


asyncio.run(main())
