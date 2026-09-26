"""Listing 11.1: single-threaded asyncio has no race here.

Use case: understand WHEN asyncio code can race. `counter = counter + 1` has
no `await` in the middle, so no other task can run halfway through it and the
assertion always holds. Code between two awaits is effectively atomic.

Run: uv run python -m workshop.ch11_synchronization.01_no_race_without_await
"""

import asyncio

counter: int = 0


async def increment():
    global counter
    await asyncio.sleep(0.01)
    counter = counter + 1


async def main():
    global counter
    for _ in range(1000):
        tasks = [asyncio.create_task(increment()) for _ in range(100)]
        await asyncio.gather(*tasks)
        assert counter == 100
        counter = 0
    print("No race: every run counted to 100")


asyncio.run(main())
