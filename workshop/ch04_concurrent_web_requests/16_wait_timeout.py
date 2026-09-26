"""Listing 4.15: asyncio.wait() with a timeout.

Use case: a hard deadline. Unlike wait_for, wait() does NOT raise and does
NOT cancel. Unfinished tasks simply come back in `pending` and it is up to you
what to do with them.

Run: uv run python -m workshop.ch04_concurrent_web_requests.16_wait_timeout
"""

import asyncio

import aiohttp

from workshop.ch04_concurrent_web_requests.fetch import fetch_status
from workshop.common import async_timed


@async_timed()
async def main():
    async with aiohttp.ClientSession() as session:
        url = "https://example.com"
        fetchers = [
            asyncio.create_task(fetch_status(session, url)),
            asyncio.create_task(fetch_status(session, url)),
            asyncio.create_task(fetch_status(session, url, delay=3)),
        ]

        done, pending = await asyncio.wait(fetchers, timeout=1)

        print(f"Done task count: {len(done)}")
        print(f"Pending task count: {len(pending)}")

        for done_task in done:
            print(await done_task)

        for task in pending:
            task.cancel()


asyncio.run(main())
