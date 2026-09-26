"""Listing 4.4: PITFALL. `await` inside the comprehension runs tasks one by one.

Use case: spot a subtle bug. Each task is created AND awaited before the next
one is created, so three 3 s delays take 9 s.

Run: uv run python -m workshop.ch04_concurrent_web_requests.04_create_task_in_comprehension_pitfall
"""

import asyncio

from workshop.common import async_timed, delay


@async_timed()
async def main() -> None:
    delay_times = [3, 3, 3]
    [await asyncio.create_task(delay(seconds)) for seconds in delay_times]


asyncio.run(main())
