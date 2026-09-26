"""Listing 2.12: add a timeout with asyncio.wait_for().

Use case: never wait forever on a slow dependency. When the timeout expires,
wait_for cancels the task and raises TimeoutError.

The modern form (Python 3.11+) is also shown: `async with asyncio.timeout(...)`.

Run: uv run python -m workshop.ch02_asyncio_basics.11_timeout_with_wait_for
"""

import asyncio

from workshop.common import delay


async def main():
    delay_task = asyncio.create_task(delay(2))
    try:
        result = await asyncio.wait_for(delay_task, timeout=1)
        print(result)
    except TimeoutError:
        print("Got a timeout!")
        print(f"Was the task cancelled? {delay_task.cancelled()}")

    # Python 3.11+: timeout as a context manager, which can wrap several awaits
    try:
        async with asyncio.timeout(1):
            await delay(2)
    except TimeoutError:
        print("Got a timeout from asyncio.timeout() too!")


asyncio.run(main())
