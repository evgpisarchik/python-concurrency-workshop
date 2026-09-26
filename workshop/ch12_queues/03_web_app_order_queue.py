"""Listing 12.3: a web app that queues work for background workers.

Use case: respond to the user right away ("Order placed!") and do the slow
work later in worker tasks. On shutdown, give queued work up to 10 s to
finish before cancelling the workers.

Run:  uv run python -m workshop.ch12_queues.03_web_app_order_queue
Then: for i in $(seq 20); do curl -s -X POST localhost:8080/order; echo; done
"""

import asyncio
from asyncio import Queue, Task
from random import randrange

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response

routes = web.RouteTableDef()

QUEUE_KEY = web.AppKey("order_queue", Queue)
TASKS_KEY = web.AppKey("order_tasks", list[Task])


async def process_order_worker(worker_id: int, queue: Queue):
    while True:
        print(f"Worker {worker_id}: Waiting for an order...")
        order = await queue.get()
        print(f"Worker {worker_id}: Processing order {order}")
        await asyncio.sleep(order)
        print(f"Worker {worker_id}: Processed order {order}")
        queue.task_done()


@routes.post("/order")
async def place_order(request: Request) -> Response:
    order_queue = request.app[QUEUE_KEY]
    await order_queue.put(randrange(5))
    return Response(body="Order placed!")


async def create_order_queue(app: web.Application):
    print("Creating order queue and tasks.")
    queue: Queue = asyncio.Queue(10)
    app[QUEUE_KEY] = queue
    app[TASKS_KEY] = [asyncio.create_task(process_order_worker(i, queue)) for i in range(5)]


async def destroy_queue(app: web.Application):
    order_tasks = app[TASKS_KEY]
    queue = app[QUEUE_KEY]
    print("Waiting for pending queue workers to finish....")
    try:
        await asyncio.wait_for(queue.join(), timeout=10)
    finally:
        print("Finished all pending items, canceling worker tasks...")
        [task.cancel() for task in order_tasks]


app = web.Application()
app.on_startup.append(create_order_queue)
app.on_shutdown.append(destroy_queue)

app.add_routes(routes)
web.run_app(app)
