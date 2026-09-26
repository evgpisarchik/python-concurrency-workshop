"""Listing 11.9: BoundedSemaphore raises on an extra release().

Use case: turn the silent bug from 11.8 into a loud ValueError. Prefer
BoundedSemaphore unless you really need to raise the limit on purpose.

Run: uv run python -m workshop.ch11_synchronization.09_bounded_semaphore   (raises ValueError, as intended)
"""

import asyncio
from asyncio import BoundedSemaphore


async def main():
    semaphore = BoundedSemaphore(1)

    await semaphore.acquire()
    semaphore.release()
    semaphore.release()  # ValueError: BoundedSemaphore released too many times


asyncio.run(main())
