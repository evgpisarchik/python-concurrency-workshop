"""Listing 4.16: identify and cancel one specific slow task.

Use case: the main result arrived in time but an optional enrichment call is
too slow, so drop only that call. wait() needs Task objects (passing bare
coroutines has been an error since Python 3.11), and the Task identity is
what lets us tell "API B" apart.

Run: uv run python -m workshop.ch04_concurrent_web_requests.17_wait_cancel_slow_task
"""

import asyncio

import aiohttp

from workshop.ch04_concurrent_web_requests.fetch import fetch_status


async def main():
    async with aiohttp.ClientSession() as session:
        api_a = asyncio.create_task(fetch_status(session, "https://www.example.com"))
        api_b = asyncio.create_task(fetch_status(session, "https://www.example.com", delay=2))

        done, pending = await asyncio.wait([api_a, api_b], timeout=1)

        for task in pending:
            if task is api_b:
                print("API B too slow, cancelling")
                task.cancel()


asyncio.run(main())
