"""Listing 4.10: asyncio.wait() returns (done, pending) sets of tasks.

Use case: finer control than gather. By default (ALL_COMPLETED) it waits for
everything, but you get Task objects back, so you can inspect each one.

Run: uv run python -m workshop.ch04_concurrent_web_requests.11_wait_all_completed
"""

import asyncio

import aiohttp

from workshop.ch04_concurrent_web_requests.fetch import fetch_status
from workshop.common import async_timed


@async_timed()
async def main():
    async with aiohttp.ClientSession() as session:
        fetchers = [
            asyncio.create_task(fetch_status(session, "https://example.com")),
            asyncio.create_task(fetch_status(session, "https://example.com")),
        ]
        done, pending = await asyncio.wait(fetchers)

        print(f"Done task count: {len(done)}")
        print(f"Pending task count: {len(pending)}")

        for done_task in done:
            result = await done_task
            print(result)


asyncio.run(main())
