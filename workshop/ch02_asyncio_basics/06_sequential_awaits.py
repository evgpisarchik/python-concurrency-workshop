"""Listing 2.7: awaiting coroutines one by one is still sequential.

Use case: see why `await` alone gives no concurrency. `add_one` has to wait for
`hello_world_message` to finish its 1 s delay. You need tasks (07, 08) to
overlap the waits.

(Listing 2.6, the `delay` helper, is in workshop/common/delay.py.)

Run: uv run python -m workshop.ch02_asyncio_basics.06_sequential_awaits
"""

import asyncio

from workshop.common import delay


async def add_one(number: int) -> int:
    return number + 1


async def hello_world_message() -> str:
    await delay(1)
    return "Hello World!"


async def main() -> None:
    message = await hello_world_message()  # pauses main() for 1 second
    one_plus_one = await add_one(1)  # only starts after the line above completes
    print(one_plus_one)
    print(message)


asyncio.run(main())
