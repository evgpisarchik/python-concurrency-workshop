"""Listing 2.20: PITFALL. A blocking library (requests) inside a coroutine.

Use case: see why you need asyncio-aware libraries. `requests.get` blocks the
thread, so the event loop cannot switch tasks and the three "concurrent"
requests run one by one. Fix it with aiohttp/httpx (chapter 4) or run blocking
code in threads (chapter 7).

Rule of thumb: an `async def` with no `await` in it is suspicious.

Run: uv run python -m workshop.ch02_asyncio_basics.18_blocking_library_in_coroutine
"""

import asyncio

import requests

from workshop.common import async_timed


@async_timed()
async def get_example_status() -> int:
    return requests.get("https://www.example.com").status_code


@async_timed()
async def main():
    task_1 = asyncio.create_task(get_example_status())
    task_2 = asyncio.create_task(get_example_status())
    task_3 = asyncio.create_task(get_example_status())
    await task_1
    await task_2
    await task_3


asyncio.run(main())
