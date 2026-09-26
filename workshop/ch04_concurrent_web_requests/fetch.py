"""Shared helper for chapter 4: GET a URL and return its status code.

`delay` adds an artificial pause before the request so you can simulate slow
endpoints and see how gather / as_completed / wait behave.
"""

import asyncio

from aiohttp import ClientSession

from workshop.common import async_timed


@async_timed()
async def fetch_status(session: ClientSession, url: str, delay: float = 0) -> int:
    await asyncio.sleep(delay)
    async with session.get(url) as result:
        return result.status
