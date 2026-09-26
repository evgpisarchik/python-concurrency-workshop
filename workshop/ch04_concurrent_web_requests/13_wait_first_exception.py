"""Listing 4.12: FIRST_EXCEPTION. Stop as soon as anything fails.

Use case: all-or-nothing batches (for example, calls that make no sense
without each other). Return on the first error and cancel what's still running.

Run: uv run python -m workshop.ch04_concurrent_web_requests.13_wait_first_exception
"""

import asyncio
import logging

import aiohttp

from workshop.ch04_concurrent_web_requests.fetch import fetch_status
from workshop.common import async_timed


@async_timed()
async def main():
    async with aiohttp.ClientSession() as session:
        fetchers = [
            asyncio.create_task(fetch_status(session, "python://bad.com")),
            asyncio.create_task(fetch_status(session, "https://www.example.com", delay=3)),
            asyncio.create_task(fetch_status(session, "https://www.example.com", delay=3)),
        ]

        done, pending = await asyncio.wait(fetchers, return_when=asyncio.FIRST_EXCEPTION)

        print(f"Done task count: {len(done)}")
        print(f"Pending task count: {len(pending)}")

        for done_task in done:
            if done_task.exception() is None:
                print(done_task.result())
            else:
                logging.error("Request got an exception", exc_info=done_task.exception())

        for pending_task in pending:
            pending_task.cancel()


asyncio.run(main())
