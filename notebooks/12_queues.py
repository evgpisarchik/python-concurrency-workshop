import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium", app_title="12 · Queues")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 12 · Queues: producer/consumer, background jobs, crawling, priorities

    `asyncio.Queue` connects producers and consumers (workers) running as tasks:

    * `await queue.put(item)` waits if the queue is full (**back-pressure**), and `await queue.get()` waits if it's empty
    * `queue.task_done()` + `await queue.join()` tell you when every item has been processed
    * workers usually loop forever, so cancel them when you're done, or call `queue.shutdown()` (3.13+, notebook 18)
    """)
    return


@app.cell
def _():
    import asyncio
    import random
    import time
    from dataclasses import dataclass, field
    from enum import IntEnum
    from urllib.parse import urljoin

    import aiohttp
    import marimo as mo
    from aiohttp import web
    from bs4 import BeautifulSoup

    from workshop.testserver import serve

    return (
        BeautifulSoup,
        IntEnum,
        aiohttp,
        asyncio,
        dataclass,
        field,
        mo,
        random,
        serve,
        time,
        urljoin,
        web,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Workers sharing a fixed batch

    *Listing 12.1.* 10 customers, 3 cashiers. Each cashier takes the next customer from the line.
    """)
    return


@app.cell
async def _(asyncio, dataclass, random, time):
    @dataclass
    class Customer:
        customer_id: int
        items: int

    async def cashier(number: int, line: asyncio.Queue, served: dict):
        while True:
            customer = await line.get()
            await asyncio.sleep(customer.items * 0.05)  # scanning items
            served.setdefault(number, []).append(customer.customer_id)
            line.task_done()

    _line = asyncio.Queue()
    for _i in range(10):
        _line.put_nowait(Customer(_i, random.randint(1, 10)))

    _served = {}
    _start = time.perf_counter()
    _cashiers = [asyncio.create_task(cashier(n, _line, _served)) for n in range(3)]
    await _line.join()  # every customer checked out
    for _c in _cashiers:
        _c.cancel()
    print(f"all customers served in {time.perf_counter() - _start:.2f} s")
    for _n, _ids in sorted(_served.items()):
        print(f"  cashier {_n} served customers {_ids}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Back-pressure with a bounded queue

    *Listing 12.2.* The producer creates work faster than 2 consumers can handle it. With `Queue(maxsize=5)`, `await put()`
    **waits** once the line is full, so the producer slows to the consumers' pace and memory stays bounded.
    An unbounded queue would grow without limit.
    """)
    return


@app.cell
async def _(asyncio, time):
    async def producer(queue: asyncio.Queue, items: int, waited: list, sizes: list):
        for i in range(items):
            start = time.perf_counter()
            await queue.put(i)
            waited.append(time.perf_counter() - start)
            sizes.append(queue.qsize())

    async def consumer(queue: asyncio.Queue):
        while True:
            await queue.get()
            await asyncio.sleep(0.1)
            queue.task_done()

    async def run(maxsize: int):
        queue, waited, sizes = asyncio.Queue(maxsize=maxsize), [], []
        consumers = [asyncio.create_task(consumer(queue)) for _ in range(2)]
        await producer(queue, 40, waited, sizes)
        await queue.join()
        for c in consumers:
            c.cancel()
        print(f"maxsize={maxsize}: peak queue length {max(sizes)}, producer waited {sum(waited):.2f} s on put()")

    await run(0)  # 0 means unbounded
    await run(5)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Background jobs behind a web endpoint

    *Listings 12.3, 12.7.* The endpoint puts the order on a queue and answers **immediately**. Worker tasks do the slow part
    later. On shutdown the app gives queued work up to 10 s to finish before cancelling the workers.
    With a `PriorityQueue`, power users' orders would jump the line (see priorities below).
    """)
    return


@app.cell
async def _(aiohttp, asyncio, time, web):
    QUEUE_KEY = web.AppKey("order_queue", asyncio.Queue)
    TASKS_KEY = web.AppKey("order_workers", list)

    async def process_orders(queue: asyncio.Queue, processed: list):
        while True:
            order = await queue.get()
            await asyncio.sleep(order["seconds"])  # the slow part: payment, email, ...
            processed.append(order["id"])
            queue.task_done()

    def make_order_app(processed: list) -> web.Application:
        async def place_order(request: web.Request) -> web.Response:
            order = await request.json()
            await request.app[QUEUE_KEY].put(order)
            return web.json_response({"status": "accepted", "id": order["id"]}, status=202)

        async def start_workers(app):
            app[QUEUE_KEY] = asyncio.Queue(maxsize=50)
            app[TASKS_KEY] = [asyncio.create_task(process_orders(app[QUEUE_KEY], processed)) for _ in range(5)]

        async def drain_and_stop(app):
            try:
                await asyncio.wait_for(app[QUEUE_KEY].join(), timeout=10)
            finally:
                for task in app[TASKS_KEY]:
                    task.cancel()

        app = web.Application()
        app.router.add_post("/order", place_order)
        app.on_startup.append(start_workers)
        app.on_shutdown.append(drain_and_stop)
        return app

    _processed = []
    _runner = web.AppRunner(make_order_app(_processed))
    await _runner.setup()
    await web.TCPSite(_runner, "127.0.0.1", 8121).start()

    async with aiohttp.ClientSession() as _session:
        _start = time.perf_counter()
        _responses = await asyncio.gather(
            *(_session.post("http://127.0.0.1:8121/order", json={"id": i, "seconds": 0.5}) for i in range(20))
        )
        print(f"20 orders accepted in {time.perf_counter() - _start:.3f} s (HTTP {_responses[0].status})")
    print(f"processed so far: {len(_processed)}")
    _start = time.perf_counter()
    await _runner.cleanup()  # graceful shutdown drains the queue
    print(f"shutdown drained the queue in {time.perf_counter() - _start:.2f} s; processed {len(_processed)} orders")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Work that creates work: a web crawler

    *Listing 12.4.* Every page's links go back into the queue, and N workers crawl concurrently until `queue.join()` says the
    whole site (up to `max_depth`) is done. The test server serves a small site of 40 linked pages (`/page/0` → `/page/1..3` → …).
    """)
    return


@app.cell
async def _(BeautifulSoup, aiohttp, asyncio, dataclass, serve, time, urljoin):
    @dataclass
    class WorkItem:
        depth: int
        url: str

    async def crawl_worker(queue: asyncio.Queue, session: aiohttp.ClientSession, max_depth: int, seen: set):
        while True:
            item = await queue.get()
            try:
                async with session.get(item.url, timeout=aiohttp.ClientTimeout(total=3)) as response:
                    body = await response.text()
                if item.depth < max_depth:
                    for link in BeautifulSoup(body, "html.parser").find_all("a", href=True):
                        url = urljoin(item.url, link["href"])
                        if url not in seen:
                            seen.add(url)
                            queue.put_nowait(WorkItem(item.depth + 1, url))
            except Exception as error:
                print(f"error crawling {item.url}: {error!r}")
            finally:
                queue.task_done()

    async def crawl(start_url: str, workers: int, max_depth: int) -> int:
        queue, seen = asyncio.Queue(), {start_url}
        queue.put_nowait(WorkItem(0, start_url))
        async with aiohttp.ClientSession() as session:
            tasks = [asyncio.create_task(crawl_worker(queue, session, max_depth, seen)) for _ in range(workers)]
            await queue.join()
            for task in tasks:
                task.cancel()
        return len(seen)

    async with serve() as _base:
        for _workers in (1, 10):
            _start = time.perf_counter()
            _pages = await crawl(f"{_base}/page/0", workers=_workers, max_depth=3)
            print(f"{_workers:>2} worker(s): crawled {_pages} pages in {time.perf_counter() - _start:.2f} s")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Priority and LIFO queues

    *Listings 12.5–12.10.*

    * `PriorityQueue` hands out the **lowest** value first. Use an ordered dataclass where only the priority is compared (`field(compare=False)`).
    * **Pitfall:** items with equal priority come out in no particular order (a heap isn't stable). Add an insertion
      counter as a tie-breaker to get FIFO order within each priority.
    * `LifoQueue` is a stack: newest first.
    """)
    return


@app.cell
def _(IntEnum, asyncio, dataclass, field):
    class UserType(IntEnum):
        POWER_USER = 1
        NORMAL_USER = 2

    @dataclass(order=True)
    class Job:
        priority: int
        data: str = field(compare=False)

    @dataclass(order=True)
    class FairJob:
        priority: int
        order: int  # tie-breaker: insertion sequence
        data: str = field(compare=False)

    def drain(queue: asyncio.Queue) -> list[str]:
        return [queue.get_nowait().data for _ in range(queue.qsize())]

    _jobs = [
        (UserType.NORMAL_USER, "normal #1"),
        (UserType.NORMAL_USER, "normal #2"),
        (UserType.NORMAL_USER, "normal #3"),
        (UserType.POWER_USER, "power #1"),
        (UserType.NORMAL_USER, "normal #4"),
    ]

    _pq = asyncio.PriorityQueue()
    for _p, _d in _jobs:
        _pq.put_nowait(Job(_p, _d))
    print("PriorityQueue:           ", drain(_pq))

    _fair = asyncio.PriorityQueue()
    for _i, (_p, _d) in enumerate(_jobs):
        _fair.put_nowait(FairJob(_p, _i, _d))
    print("PriorityQueue + counter: ", drain(_fair))

    _lifo = asyncio.LifoQueue()
    for _i, (_p, _d) in enumerate(_jobs):
        _lifo.put_nowait(FairJob(_p, _i, _d))
    print("LifoQueue:               ", drain(_lifo))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Takeaways

    * A queue decouples **how fast work arrives** from **how fast it's processed**, and N worker tasks set the concurrency.
    * Bound the queue for back-pressure. `task_done()` + `join()` tell you when all the work is finished.
    * asyncio queues live in one process and memory. For durability or multiple machines, use Redis, RabbitMQ, SQS, Celery, etc.
    """)
    return


if __name__ == "__main__":
    app.run()
