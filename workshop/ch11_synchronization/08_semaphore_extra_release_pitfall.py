"""Listing 11.8: PITFALL. Releasing a Semaphore more often than it was acquired.

Use case: see how a stray release() silently raises the limit. After the
extra release, a Semaphore(2) lets THREE coroutines in at once.

Run: uv run python -m workshop.ch11_synchronization.08_semaphore_extra_release_pitfall
"""

import asyncio
from asyncio import Semaphore


async def acquire(semaphore: Semaphore):
    print("Waiting to acquire")
    async with semaphore:
        print("Acquired")
        await asyncio.sleep(5)
    print("Releasing")


async def release(semaphore: Semaphore):
    print("Releasing as a one off!")
    semaphore.release()
    print("Released as a one off!")


async def main():
    semaphore = Semaphore(2)

    print("Acquiring twice, releasing three times...")
    await asyncio.gather(acquire(semaphore), acquire(semaphore), release(semaphore))

    print("Acquiring three times...")
    await asyncio.gather(acquire(semaphore), acquire(semaphore), acquire(semaphore))


asyncio.run(main())
