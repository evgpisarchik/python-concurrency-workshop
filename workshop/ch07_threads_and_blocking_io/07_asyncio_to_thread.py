"""Listing 7.7: asyncio.to_thread(), the simplest way to call blocking code.

Use case: the recommended one-liner (Python 3.9+) for blocking calls. It
accepts args/kwargs directly (no partial needed) and copies contextvars into
the thread.

Run: uv run python -m workshop.ch07_threads_and_blocking_io.07_asyncio_to_thread
"""

import asyncio

import requests

from workshop.common import async_timed


def get_status_code(url: str) -> int:
    response = requests.get(url)
    return response.status_code


@async_timed()
async def main():
    urls = ["https://www.example.com" for _ in range(100)]
    tasks = [asyncio.to_thread(get_status_code, url) for url in urls]
    results = await asyncio.gather(*tasks)
    print(results)


asyncio.run(main())
