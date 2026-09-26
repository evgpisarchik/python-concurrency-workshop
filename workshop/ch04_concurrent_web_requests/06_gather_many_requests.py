"""Listing 4.6: asyncio.gather() runs many requests concurrently.

Use case: fan out N HTTP calls (scraping, calling a batch API, health checks)
and collect every result. The book uses 1000 requests. We use 100 to be polite
to example.com; raise it to see how well it scales.

Run: uv run python -m workshop.ch04_concurrent_web_requests.06_gather_many_requests
"""

import asyncio

import aiohttp

from workshop.ch04_concurrent_web_requests.fetch import fetch_status
from workshop.common import async_timed


@async_timed()
async def main():
    async with aiohttp.ClientSession() as session:
        urls = ["https://example.com" for _ in range(100)]
        requests = [fetch_status(session, url) for url in urls]
        status_codes = await asyncio.gather(*requests)
        print(status_codes)


asyncio.run(main())
