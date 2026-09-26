"""Listing 2.4: `await` runs a coroutine and waits for its result.

Use case: call one coroutine from another, the async version of a normal
function call.

Run: uv run python -m workshop.ch02_asyncio_basics.04_await_coroutines
"""

import asyncio


async def add_one(number: int) -> int:
    return number + 1


async def main() -> None:
    one_plus_one = await add_one(1)
    two_plus_one = await add_one(2)
    print(one_plus_one)
    print(two_plus_one)


asyncio.run(main())
