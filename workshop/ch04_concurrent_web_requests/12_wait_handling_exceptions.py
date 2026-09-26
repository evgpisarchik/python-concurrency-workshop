"""Listing 4.11: inspect exceptions from wait() without raising them.

Use case: log failures per request and still process the successful ones.
task.exception() returns the exception (or None), so you never have to
`await` a failed task inside a try/except.

Run: uv run python -m workshop.ch04_concurrent_web_requests.12_wait_handling_exceptions
"""

import asyncio
import logging

import aiohttp

from workshop.ch04_concurrent_web_requests.fetch import fetch_status
from workshop.common import async_timed


@async_timed()
async def main():
    async with aiohttp.ClientSession() as session:
        good_request = fetch_status(session, "https://www.example.com")
        bad_request = fetch_status(session, "python://bad")

        fetchers = [asyncio.create_task(good_request), asyncio.create_task(bad_request)]

        done, pending = await asyncio.wait(fetchers)

        print(f"Done task count: {len(done)}")
        print(f"Pending task count: {len(pending)}")

        for done_task in done:
            # `result = await done_task` would raise here for the bad request
            if done_task.exception() is None:
                print(done_task.result())
            else:
                logging.error("Request got an exception", exc_info=done_task.exception())


asyncio.run(main())
