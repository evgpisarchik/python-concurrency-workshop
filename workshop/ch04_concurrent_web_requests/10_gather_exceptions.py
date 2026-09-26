"""Bonus (book section 4.4.1): how gather handles exceptions.

Use case: decide what should happen when one of many requests fails.
  * default: the first exception is raised from gather, and the others keep running
  * return_exceptions=True: exceptions are returned as values, so you can
    split results into successes and failures

Run: uv run python -m workshop.ch04_concurrent_web_requests.10_gather_exceptions
"""

import asyncio

import aiohttp

from workshop.ch04_concurrent_web_requests.fetch import fetch_status
from workshop.common import async_timed


@async_timed()
async def main():
    async with aiohttp.ClientSession() as session:
        urls = ["https://example.com", "python://example.com"]  # the second URL is invalid

        try:
            await asyncio.gather(*[fetch_status(session, url) for url in urls])
        except Exception as error:
            print(f"Default gather raised: {error!r}")

        results = await asyncio.gather(*[fetch_status(session, url) for url in urls], return_exceptions=True)
        exceptions = [res for res in results if isinstance(res, Exception)]
        successful = [res for res in results if not isinstance(res, Exception)]
        print(f"All results: {results}")
        print(f"Finished successfully: {successful}")
        print(f"Threw exceptions: {exceptions}")


asyncio.run(main())
