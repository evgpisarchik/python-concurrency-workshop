"""Listing 2.1: defining a coroutine with `async def`.

Use case: the building block of asyncio. A coroutine is a function that can
pause (at `await`) and let other work run while it waits.

Run: uv run python -m workshop.ch02_asyncio_basics.01_first_coroutine   (prints nothing; see 02)
"""


async def my_coroutine() -> None:
    print("Hello world!")
