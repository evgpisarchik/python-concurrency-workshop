"""Listing 4.8: asyncio.as_completed() yields results as soon as each is ready.

Use case: show partial results early (progress bars, streaming search results)
instead of waiting for the slowest request.

Run: uv run python -m workshop.ch04_concurrent_web_requests.08_as_completed
"""

import asyncio

import aiohttp

from workshop.ch04_concurrent_web_requests.fetch import fetch_status
from workshop.common import async_timed


@async_timed()
async def main():
    async with aiohttp.ClientSession() as session:
        fetchers = [
            fetch_status(session, "https://www.example.com", 1),
            fetch_status(session, "https://www.example.com", 1),
            fetch_status(session, "https://www.example.com", 10),
        ]

        for finished_task in asyncio.as_completed(fetchers):
            print(await finished_task)


asyncio.run(main())
