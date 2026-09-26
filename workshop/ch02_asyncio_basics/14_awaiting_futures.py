"""Listing 2.15: await a Future that gets resolved by another task.

Use case: connect callback-style code to async/await. A library hands you a
Future, and some other code (a callback, a protocol, a thread) fills it in later.

Run: uv run python -m workshop.ch02_asyncio_basics.14_awaiting_futures
"""

import asyncio
from asyncio import Future


def make_request() -> Future:
    future = asyncio.get_running_loop().create_future()
    asyncio.create_task(set_future_value(future))
    return future


async def set_future_value(future: Future) -> None:
    await asyncio.sleep(1)
    future.set_result(42)


async def main() -> None:
    future = make_request()
    print(f"Is the future done? {future.done()}")
    value = await future
    print(f"Is the future done? {future.done()}")
    print(value)


asyncio.run(main())
