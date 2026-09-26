"""Listing 4.3: session-wide and per-request timeouts in aiohttp.

Use case: protect your service from slow upstreams. Set defaults on the
session (total=1 s, connect=0.1 s) and override them for single requests
(here 10 ms, which is meant to fail).

Run: uv run python -m workshop.ch04_concurrent_web_requests.03_aiohttp_timeouts
"""

import asyncio

import aiohttp
from aiohttp import ClientSession


async def fetch_status(session: ClientSession, url: str) -> int:
    ten_millis = aiohttp.ClientTimeout(total=0.01)
    async with session.get(url, timeout=ten_millis) as result:
        return result.status


async def main():
    session_timeout = aiohttp.ClientTimeout(total=1, connect=0.1)
    async with aiohttp.ClientSession(timeout=session_timeout) as session:
        try:
            await fetch_status(session, "https://example.com")
        except TimeoutError:
            print("Request timed out after 10 ms, as expected")


asyncio.run(main())
