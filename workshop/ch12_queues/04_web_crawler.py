"""Listing 12.4: a concurrent web crawler that uses a queue.

Use case: work that creates more work. Each page's links go back into the
queue, and N workers crawl concurrently. queue.join() tells us when the whole
crawl (up to max_depth) is finished.

Run: uv run python -m workshop.ch12_queues.04_web_crawler
"""

import asyncio
import logging
from asyncio import Queue
from dataclasses import dataclass
from urllib.parse import urljoin

import aiohttp
from aiohttp import ClientSession
from bs4 import BeautifulSoup


@dataclass
class WorkItem:
    item_depth: int
    url: str


async def worker(worker_id: int, queue: Queue, session: ClientSession, max_depth: int):
    while True:
        work_item: WorkItem = await queue.get()
        print(f"Worker {worker_id}: Processing {work_item.url}")
        await process_page(work_item, queue, session, max_depth)
        print(f"Worker {worker_id}: Finished {work_item.url}")
        queue.task_done()


async def process_page(work_item: WorkItem, queue: Queue, session: ClientSession, max_depth: int):
    try:
        async with asyncio.timeout(3):
            async with session.get(work_item.url) as response:
                if work_item.item_depth == max_depth:
                    print(f"Max depth reached, not processing more for {work_item.url}")
                    return
                body = await response.text()
        soup = BeautifulSoup(body, "html.parser")
        for link in soup.find_all("a", href=True):
            url = urljoin(work_item.url, link["href"])
            if url.startswith("http"):
                queue.put_nowait(WorkItem(work_item.item_depth + 1, url))
    except Exception:
        logging.exception(f"Error processing url {work_item.url}")


async def main():
    start_url = "https://example.com"
    url_queue = Queue()
    url_queue.put_nowait(WorkItem(0, start_url))
    async with aiohttp.ClientSession() as session:
        workers = [asyncio.create_task(worker(i, url_queue, session, 2)) for i in range(100)]
        await url_queue.join()
        [w.cancel() for w in workers]


asyncio.run(main())
