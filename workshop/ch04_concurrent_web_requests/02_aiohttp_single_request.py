"""Listing 4.2: an HTTP request with aiohttp.

Use case: non-blocking HTTP client calls. Create ONE ClientSession per
application (it holds the connection pool) and reuse it for every request.

Run: uv run python -m workshop.ch04_concurrent_web_requests.02_aiohttp_single_request
"""

import asyncio

import aiohttp
from aiohttp import ClientSession

from workshop.common import async_timed


@async_timed()
async def fetch_status(session: ClientSession, url: str) -> int:
    async with session.get(url) as result:
        return result.status


@async_timed()
async def main():
    async with aiohttp.ClientSession() as session:
        url = "https://www.example.com"
        status = await fetch_status(session, url)
        print(f"Status for {url} was {status}")


asyncio.run(main())
