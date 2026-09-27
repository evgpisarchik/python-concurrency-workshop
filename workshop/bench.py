"""A tiny asyncio HTTP load generator (an alternative to Locust).

uv run python -m workshop.bench URL [-n REQUESTS] [-c CONCURRENCY]
"""

import argparse
import asyncio
import time

import aiohttp


async def bench(url: str, requests: int, concurrency: int) -> None:
    """Send `requests` GET requests to `url`, at most `concurrency` at a time."""

    async def get(session: aiohttp.ClientSession):
        async with session.get(url) as response:
            await response.read()

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=concurrency)) as session:
        await asyncio.gather(*(get(session) for _ in range(requests)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("-n", "--requests", type=int, default=1000)
    parser.add_argument("-c", "--concurrency", type=int, default=100)
    args = parser.parse_args()
    start = time.perf_counter()
    asyncio.run(bench(args.url, args.requests, args.concurrency))
    print(f"{args.requests} requests in {time.perf_counter() - start:.2f} s")
