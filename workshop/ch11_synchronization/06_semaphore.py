"""Listing 11.6: a Semaphore lets at most N coroutines in at once.

Use case: limit concurrency (N parallel downloads, N DB connections, N GPU
jobs). Here 4 operations run at most 2 at a time, so they finish in 2 waves.

Run: uv run python -m workshop.ch11_synchronization.06_semaphore
"""

import asyncio
from asyncio import Semaphore


async def operation(semaphore: Semaphore):
    print("Waiting to acquire semaphore...")
    async with semaphore:
        print("Semaphore acquired!")
        await asyncio.sleep(2)
    print("Semaphore released!")


async def main():
    semaphore = Semaphore(2)
    await asyncio.gather(*[operation(semaphore) for _ in range(4)])


asyncio.run(main())
