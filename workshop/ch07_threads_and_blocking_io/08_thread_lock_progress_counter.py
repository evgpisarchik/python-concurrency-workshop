"""Listing 7.8: a thread-safe progress counter with threading.Lock.

Use case: many threads update shared state (counters, caches). `counter += 1`
is not atomic, so guard it with a lock. An asyncio task reads the counter to
report progress.

Run: uv run python -m workshop.ch07_threads_and_blocking_io.08_thread_lock_progress_counter
"""

import asyncio
import functools
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

import requests

from workshop.common import async_timed

counter_lock = Lock()
counter: int = 0


def get_status_code(url: str) -> int:
    global counter
    response = requests.get(url)
    with counter_lock:
        counter = counter + 1
    return response.status_code


async def reporter(request_count: int):
    while counter < request_count:
        print(f"Finished {counter}/{request_count} requests")
        await asyncio.sleep(0.5)


@async_timed()
async def main():
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        request_count = 200
        urls = ["https://www.example.com" for _ in range(request_count)]
        reporter_task = asyncio.create_task(reporter(request_count))
        tasks = [loop.run_in_executor(pool, functools.partial(get_status_code, url)) for url in urls]
        results = await asyncio.gather(*tasks)
        await reporter_task
        print(results)


asyncio.run(main())
