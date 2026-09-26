"""Listing 5.14: an async generator consumed with `async for`.

Use case: produce a stream of values where getting each value needs I/O
(paginated APIs, database cursors, message streams).

Run: uv run python -m workshop.ch05_async_databases.13_async_generator
"""

import asyncio

from workshop.common import async_timed, delay


async def positive_integers_async(until: int):
    for integer in range(1, until):
        await delay(integer)
        yield integer


@async_timed()
async def main():
    async_generator = positive_integers_async(3)
    print(type(async_generator))
    async for number in async_generator:
        print(f"Got number {number}")


asyncio.run(main())
