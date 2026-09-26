"""Listing 4.7: gather returns results in the order you passed the awaitables.

Use case: map results back to inputs without extra bookkeeping. The 3 s
delay finishes last but its result comes first: [3, 1].

Run: uv run python -m workshop.ch04_concurrent_web_requests.07_gather_preserves_order
"""

import asyncio

from workshop.common import delay


async def main():
    results = await asyncio.gather(delay(3), delay(1))
    print(results)


asyncio.run(main())
