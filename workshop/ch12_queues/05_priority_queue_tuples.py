"""Listing 12.5: PriorityQueue with (priority, data) tuples.

Use case: process urgent work first. The lowest value comes out first.

Run: uv run python -m workshop.ch12_queues.05_priority_queue_tuples
"""

import asyncio
from asyncio import PriorityQueue, Queue


async def worker(queue: Queue):
    while not queue.empty():
        work_item: tuple[int, str] = await queue.get()
        print(f"Processing work item {work_item}")
        queue.task_done()


async def main():
    priority_queue = PriorityQueue()

    work_items = [(3, "Lowest priority"), (2, "Medium priority"), (1, "High priority")]

    worker_task = asyncio.create_task(worker(priority_queue))

    for work in work_items:
        priority_queue.put_nowait(work)

    await asyncio.gather(priority_queue.join(), worker_task)


asyncio.run(main())
