"""Listing 11.10: asyncio.Event, where many coroutines wait for one signal.

Use case: "wait until ready" (config loaded, connection established,
shutdown requested). Every waiter wakes up when the event is set().

Run: uv run python -m workshop.ch11_synchronization.10_event
"""

import asyncio
import functools
from asyncio import Event


def trigger_event(event: Event):
    event.set()


async def do_work_on_event(event: Event):
    print("Waiting for event...")
    await event.wait()
    print("Performing work!")
    await asyncio.sleep(1)
    print("Finished work!")
    event.clear()


async def main():
    event = asyncio.Event()
    asyncio.get_running_loop().call_later(5.0, functools.partial(trigger_event, event))
    await asyncio.gather(do_work_on_event(event), do_work_on_event(event))


asyncio.run(main())
