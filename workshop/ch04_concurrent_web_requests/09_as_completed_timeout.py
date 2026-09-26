"""Listing 4.9: as_completed with a timeout.

Use case: "give me whatever finishes within 2 s". Any awaitable not done by
then raises TimeoutError. Note that the slow tasks KEEP RUNNING in the
background (see the all_tasks() printout), so cancel them yourself if needed.

Run: uv run python -m workshop.ch04_concurrent_web_requests.09_as_completed_timeout
"""

import asyncio

import aiohttp

from workshop.ch04_concurrent_web_requests.fetch import fetch_status
from workshop.common import async_timed


@async_timed()
async def main():
    async with aiohttp.ClientSession() as session:
        fetchers = [
            fetch_status(session, "https://example.com", 1),
            fetch_status(session, "https://example.com", 10),
            fetch_status(session, "https://example.com", 10),
        ]

        for done_task in asyncio.as_completed(fetchers, timeout=2):
            try:
                result = await done_task
                print(result)
            except TimeoutError:
                print("We got a timeout error!")

        for task in asyncio.all_tasks():
            print(task)


asyncio.run(main())
