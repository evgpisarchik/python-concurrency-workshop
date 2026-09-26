"""Listing 2.3: asyncio.run() is the entry point of every asyncio program.

Use case: run one "main" coroutine. asyncio.run creates an event loop, runs the
coroutine until it completes, cancels any tasks left over, and closes the loop.

Run: uv run python -m workshop.ch02_asyncio_basics.03_asyncio_run
"""

import asyncio


async def coroutine_add_one(number: int) -> int:
    return number + 1


result = asyncio.run(coroutine_add_one(1))
print(result)
