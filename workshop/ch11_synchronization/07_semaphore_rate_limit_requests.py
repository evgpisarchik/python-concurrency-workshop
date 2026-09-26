"""Listing 11.7: limit concurrent HTTP requests with a Semaphore.

Use case: respect an API's concurrency limit, or avoid overwhelming a
server, while still sending everything through one gather().

Run: uv run python -m workshop.ch11_synchronization.07_semaphore_rate_limit_requests
"""

import asyncio
from asyncio import Semaphore

from aiohttp import ClientSession


async def get_url(url: str, session: ClientSession, semaphore: Semaphore):
    print("Waiting to acquire semaphore...")
    async with semaphore:
        print("Acquired semaphore, requesting...")
        async with session.get(url) as response:
            print("Finished requesting")
            return response.status


async def main():
    semaphore = Semaphore(10)
    async with ClientSession() as session:
        tasks = [get_url("https://www.example.com", session, semaphore) for _ in range(100)]
        await asyncio.gather(*tasks)


asyncio.run(main())
