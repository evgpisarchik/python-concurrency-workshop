"""Listing 4.5: create ALL tasks first, then await them.

Use case: the fix for listing 4.4. Three 3 s delays take about 3 s.

Run: uv run python -m workshop.ch04_concurrent_web_requests.05_create_tasks_then_await
"""

import asyncio

from workshop.common import async_timed, delay


@async_timed()
async def main() -> None:
    delay_times = [3, 3, 3]
    tasks = [asyncio.create_task(delay(seconds)) for seconds in delay_times]
    [await task for task in tasks]


asyncio.run(main())
