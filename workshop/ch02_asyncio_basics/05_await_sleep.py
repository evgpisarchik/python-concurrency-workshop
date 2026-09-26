"""Listing 2.5: asyncio.sleep() simulates a slow I/O operation.

Use case: stand-in for a web request or database query. While a coroutine sleeps,
the event loop is free to run other work.

Run: uv run python -m workshop.ch02_asyncio_basics.05_await_sleep
"""

import asyncio


async def hello_world_message() -> str:
    await asyncio.sleep(1)
    return "Hello World!"


async def main() -> None:
    message = await hello_world_message()
    print(message)


asyncio.run(main())
