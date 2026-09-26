"""Listing 11.2: PITFALL. A race condition because of an `await` in a read-modify-write.

Use case: the classic asyncio bug. Read shared state, `await` something,
then write it back. Other tasks updated it in the meantime, so their updates are
lost. The assertion fails on the first run (counter is 1, not 100).

Run: uv run python -m workshop.ch11_synchronization.02_race_condition_across_await
"""

import asyncio

counter: int = 0


async def increment():
    global counter
    temp_counter = counter
    temp_counter = temp_counter + 1
    await asyncio.sleep(0.01)  # other tasks run here and read the same old value
    counter = temp_counter


async def main():
    global counter
    for _ in range(1000):
        tasks = [asyncio.create_task(increment()) for _ in range(100)]
        await asyncio.gather(*tasks)
        print(f"Counter is {counter}")
        assert counter == 100
        counter = 0


asyncio.run(main())
