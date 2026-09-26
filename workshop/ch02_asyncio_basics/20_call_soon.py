"""Listing 2.22: schedule a plain function on the running loop.

Use case: run a normal (non-async) callback on the next loop iteration.
get_running_loop() raises if no loop is running, which is safer than the
older get_event_loop().

Run: uv run python -m workshop.ch02_asyncio_basics.20_call_soon
"""

import asyncio

from workshop.common import delay


def call_later():
    print("I'm being called in the future!")


async def main():
    loop = asyncio.get_running_loop()
    loop.call_soon(call_later)
    await delay(1)


asyncio.run(main())
