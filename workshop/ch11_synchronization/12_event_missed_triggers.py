"""Listing 11.13: PITFALL. Events can "miss" triggers.

Use case: know the limits of Event. The trigger fires every 1 s but the
workers are busy for 5 s, and set() on an event that is already set does nothing,
so most triggers are lost. If every trigger must be handled, use a Queue (chapter 12).

Run: uv run python -m workshop.ch11_synchronization.12_event_missed_triggers
"""

import asyncio
from asyncio import Event
from contextlib import suppress


async def trigger_event_periodically(event: Event):
    while True:
        print("Triggering event!")
        event.set()
        await asyncio.sleep(1)


async def do_work_on_event(event: Event):
    while True:
        print("Waiting for event...")
        await event.wait()
        event.clear()
        print("Performing work!")
        await asyncio.sleep(5)
        print("Finished work!")


async def main():
    event = asyncio.Event()
    trigger = asyncio.wait_for(trigger_event_periodically(event), 5.0)

    with suppress(TimeoutError):
        await asyncio.gather(do_work_on_event(event), do_work_on_event(event), trigger)


asyncio.run(main())
