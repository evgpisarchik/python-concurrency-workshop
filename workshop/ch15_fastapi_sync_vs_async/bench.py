"""A tiny asyncio HTTP load generator (an alternative to locust).

Use case: this is itself an asyncio pattern. N requests, at most C in flight
(Semaphore), one shared ClientSession, and latency stats at the end.

Run: uv run python -m workshop.ch15_fastapi_sync_vs_async.bench URL [-n REQUESTS] [-c CONCURRENCY]
"""

import argparse
import asyncio
import statistics
import time

import aiohttp


async def main(url: str, requests: int, concurrency: int) -> None:
    semaphore = asyncio.Semaphore(concurrency)
    latencies: list[float] = []
    errors = 0

    async def one(session: aiohttp.ClientSession) -> None:
        nonlocal errors
        async with semaphore:
            start = time.perf_counter()
            try:
                async with session.get(url) as response:
                    await response.read()
                    if response.status >= 400:
                        errors += 1
            except aiohttp.ClientError:
                errors += 1
            latencies.append(time.perf_counter() - start)

    connector = aiohttp.TCPConnector(limit=concurrency)
    async with aiohttp.ClientSession(connector=connector) as session:
        start = time.perf_counter()
        await asyncio.gather(*(one(session) for _ in range(requests)))
        total = time.perf_counter() - start

    latencies.sort()
    print(f"{requests} requests, concurrency {concurrency}, {errors} errors")
    print(f"total {total:.2f} s  ->  {requests / total:.0f} req/s")
    print(
        f"latency p50 {statistics.median(latencies) * 1000:.0f} ms, "
        f"p95 {latencies[int(len(latencies) * 0.95) - 1] * 1000:.0f} ms, "
        f"max {latencies[-1] * 1000:.0f} ms"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("-n", "--requests", type=int, default=1000)
    parser.add_argument("-c", "--concurrency", type=int, default=100)
    args = parser.parse_args()
    asyncio.run(main(args.url, args.requests, args.concurrency))
