"""Listing 2.14: a Future is a placeholder for a value that arrives later.

Use case: understand the low-level object under Tasks. A Future starts
"not done". Someone calls set_result() later, and anyone awaiting it wakes up.
(Task is a subclass of Future.)

Run: uv run python -m workshop.ch02_asyncio_basics.13_futures_basics
"""

import asyncio


async def main():
    my_future = asyncio.get_running_loop().create_future()

    print(f"Is my_future done? {my_future.done()}")

    my_future.set_result(42)

    print(f"Is my_future done? {my_future.done()}")
    print(f"What is the result of my_future? {my_future.result()}")


asyncio.run(main())
