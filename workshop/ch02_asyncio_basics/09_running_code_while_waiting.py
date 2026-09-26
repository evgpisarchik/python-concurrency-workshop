"""Listing 2.10: run other code while tasks are waiting.

Use case: keep doing useful work (for example, reporting progress) while
long-running tasks wait in the background. Total time is about 3 s, not 8 s.

Run: uv run python -m workshop.ch02_asyncio_basics.09_running_code_while_waiting
"""

import asyncio

from workshop.common import delay


async def hello_every_second():
    for _ in range(2):
        await asyncio.sleep(1)
        print("I'm running other code while I'm waiting!")


async def main():
    first_delay = asyncio.create_task(delay(3))
    second_delay = asyncio.create_task(delay(3))
    await hello_every_second()
    await first_delay
    await second_delay


asyncio.run(main())
