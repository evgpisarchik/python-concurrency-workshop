"""Listing 4.13: FIRST_COMPLETED. Return as soon as any task finishes.

Use case: "fastest replica wins" (hedged requests to several mirrors) or
reacting to the first available result.

Run: uv run python -m workshop.ch04_concurrent_web_requests.14_wait_first_completed
"""

import asyncio

import aiohttp

from workshop.ch04_concurrent_web_requests.fetch import fetch_status
from workshop.common import async_timed


@async_timed()
async def main():
    async with aiohttp.ClientSession() as session:
        url = "https://www.example.com"
        fetchers = [asyncio.create_task(fetch_status(session, url)) for _ in range(3)]

        done, pending = await asyncio.wait(fetchers, return_when=asyncio.FIRST_COMPLETED)

        print(f"Done task count: {len(done)}")
        print(f"Pending task count: {len(pending)}")

        for done_task in done:
            print(await done_task)

        for task in pending:
            task.cancel()


asyncio.run(main())
