"""Listing 14.5: the legacy generator-based coroutine style.

Use case: read old asyncio code (Python 3.4 to 3.10). The book uses
@asyncio.coroutine, which was removed in Python 3.11. Its closest remaining
equivalent is @types.coroutine, which shows that under the hood async/await is
still built on generators and `yield from`.

Run: uv run python -m workshop.ch14_advanced_asyncio.05_generator_based_coroutines_legacy
"""

import asyncio
import types


@types.coroutine
def coroutine():
    print("Sleeping!")
    yield from asyncio.sleep(1).__await__()
    print("Finished!")


async def main():
    await coroutine()


asyncio.run(main())
