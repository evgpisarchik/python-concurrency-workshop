"""Listing 4.14: loop on FIRST_COMPLETED to process results as they arrive.

Use case: like as_completed, but you keep the Task objects. That lets you
map a result back to its request, add new tasks while looping, or cancel
specific ones.

Run: uv run python -m workshop.ch04_concurrent_web_requests.15_wait_first_completed_loop
"""

import asyncio

import aiohttp

from workshop.ch04_concurrent_web_requests.fetch import fetch_status
from workshop.common import async_timed


@async_timed()
async def main():
    async with aiohttp.ClientSession() as session:
        url = "https://www.example.com"
        pending = [asyncio.create_task(fetch_status(session, url)) for _ in range(3)]

        while pending:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)

            print(f"Done task count: {len(done)}")
            print(f"Pending task count: {len(pending)}")

            for done_task in done:
                print(await done_task)


asyncio.run(main())
