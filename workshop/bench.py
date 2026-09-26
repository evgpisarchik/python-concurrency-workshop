"""A tiny asyncio HTTP load generator (an alternative to Locust).

It's an asyncio pattern in itself: N requests, at most C in flight (Semaphore),
one shared ClientSession, and latency percentiles at the end.

    uv run python -m workshop.bench URL [-n REQUESTS] [-c CONCURRENCY]
"""

import argparse
import asyncio
import statistics
import time

import aiohttp


async def bench(url: str, requests: int = 1000, concurrency: int = 100) -> dict:
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
                    errors += response.status >= 400
            except aiohttp.ClientError:
                errors += 1
            latencies.append(time.perf_counter() - start)

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=concurrency)) as session:
        start = time.perf_counter()
        await asyncio.gather(*(one(session) for _ in range(requests)))
        total = time.perf_counter() - start

    latencies.sort()
    return {
        "url": url,
        "requests": requests,
        "concurrency": concurrency,
        "errors": errors,
        "total_s": round(total, 2),
        "req_per_s": round(requests / total),
        "p50_ms": round(statistics.median(latencies) * 1000),
        "p95_ms": round(latencies[int(len(latencies) * 0.95) - 1] * 1000),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("-n", "--requests", type=int, default=1000)
    parser.add_argument("-c", "--concurrency", type=int, default=100)
    args = parser.parse_args()
    print(asyncio.run(bench(args.url, args.requests, args.concurrency)))
