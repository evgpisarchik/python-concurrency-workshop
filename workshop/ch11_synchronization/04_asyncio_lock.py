"""Listing 11.4: asyncio.Lock, where only one coroutine is in the critical section.

Use case: serialize access to a shared resource across `await` points. Note
that asyncio.Lock is NOT thread-safe. Use threading.Lock for threads.

Run: uv run python -m workshop.ch11_synchronization.04_asyncio_lock
"""

import asyncio
from asyncio import Lock

from workshop.common import delay


async def a(lock: Lock):
    print("Coroutine a waiting to acquire the lock")
    async with lock:
        print("Coroutine a is in the critical section")
        await delay(2)
    print("Coroutine a released the lock")


async def b(lock: Lock):
    print("Coroutine b waiting to acquire the lock")
    async with lock:
        print("Coroutine b is in the critical section")
        await delay(2)
    print("Coroutine b released the lock")


async def main():
    lock = Lock()
    await asyncio.gather(a(lock), b(lock))


asyncio.run(main())
