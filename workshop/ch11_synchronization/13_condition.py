"""Listing 11.14: asyncio.Condition = Lock + Event.

Use case: wait for a notification AND hold a lock while reacting to it.
wait() releases the lock while waiting and re-acquires it on notify.

Run: uv run python -m workshop.ch11_synchronization.13_condition   (stops after 12 s)
"""

import asyncio
from asyncio import Condition
from contextlib import suppress


async def do_work(condition: Condition):
    while True:
        print("Waiting for condition lock...")
        async with condition:
            print("Acquired lock, releasing and waiting for condition...")
            await condition.wait()
            print("Condition event fired, re-acquiring lock and doing work...")
            await asyncio.sleep(1)
        print("Work finished, lock released.")


async def fire_event(condition: Condition):
    while True:
        await asyncio.sleep(5)
        print("About to notify, acquiring condition lock...")
        async with condition:
            print("Lock acquired, notifying all workers.")
            condition.notify_all()
        print("Notification finished, releasing lock.")


async def main():
    condition = Condition()

    with suppress(TimeoutError):
        async with asyncio.timeout(12):
            asyncio.create_task(fire_event(condition))
            await asyncio.gather(do_work(condition), do_work(condition))


asyncio.run(main())
