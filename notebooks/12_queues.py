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
    from dataclasses import dataclass, field
    from urllib.parse import urljoin

    import aiohttp
    import marimo as mo
    from aiohttp import web
    from bs4 import BeautifulSoup

    from workshop.common import timed
    from workshop.testserver import start

    return BeautifulSoup, aiohttp, asyncio, dataclass, field, mo, start, timed, urljoin, web


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Workers sharing a fixed batch

    *Listing 12.1.* 6 customers, 3 cashiers. Each cashier takes the next customer from the line.
    """)
    return


@app.cell
async def _(asyncio, timed):
    async def cashier(name: str, line: asyncio.Queue):
        while True:
            items = await line.get()
            await asyncio.sleep(items * 0.1)  # scanning items
            print(f"{name} served a customer with {items} items")
            line.task_done()

    _line = asyncio.Queue()
    for _items in [3, 8, 1, 5, 2, 6]:
        _line.put_nowait(_items)

    _cashiers = [asyncio.create_task(cashier(f"cashier {n}", _line)) for n in range(3)]
    with timed("all customers served"):
        await _line.join()
    for _cashier in _cashiers:
        _cashier.cancel()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Back-pressure with a bounded queue

    *Listing 12.2.* The producer creates 40 items much faster than 2 consumers can handle them. With `Queue(maxsize=5)`,
    `await put()` **waits** once the queue is full, so the producer slows to the consumers' pace and memory stays
    bounded. An unbounded queue just grows.
    """)
    return


@app.cell
async def _(asyncio):
    async def consumer(queue: asyncio.Queue):
        while True:
            await queue.get()
            await asyncio.sleep(0.1)
            queue.task_done()

    async def peak_queue_length(maxsize: int) -> int:
        queue = asyncio.Queue(maxsize)
        consumers = [asyncio.create_task(consumer(queue)) for _ in range(2)]
        peak = 0
        for item in range(40):
            await queue.put(item)  # waits while the queue is full
            peak = max(peak, queue.qsize())
        await queue.join()
        for task in consumers:
            task.cancel()
        return peak

    print("unbounded queue, peak length:", await peak_queue_length(0))
    print("Queue(maxsize=5), peak length:", await peak_queue_length(5))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Background jobs behind a web endpoint

    *Listings 12.3, 12.7.* The endpoint puts the order on a queue and answers **immediately**. Worker tasks do the slow part
    later. On shutdown the app waits for queued work to finish before stopping the workers.
    With a `PriorityQueue`, power users' orders could jump the line (see priorities below).
    """)
    return


@app.cell
async def _(aiohttp, asyncio, timed, web):
    class OrderService:
        """A web endpoint that queues orders, plus worker tasks that process them later."""

        def __init__(self):
            self.orders = asyncio.Queue()
            self.processed = []
            self._workers = []
            self._runner = None

        async def start(self, workers: int) -> str:
            """Start the workers and the web server; return the order URL."""
            self._workers = [asyncio.create_task(self._process_orders()) for _ in range(workers)]
            app = web.Application()
            app.router.add_post("/order", self._place_order)
            self._runner = web.AppRunner(app)
            await self._runner.setup()
            await web.TCPSite(self._runner, "127.0.0.1", 0).start()
            return f"http://127.0.0.1:{self._runner.addresses[0][1]}/order"

        async def shutdown(self):
            await self.orders.join()  # finish the queued orders first
            for worker in self._workers:
                worker.cancel()
            await self._runner.cleanup()

        async def _place_order(self, request: web.Request) -> web.Response:
            await self.orders.put(await request.json())
            return web.json_response({"status": "accepted"}, status=202)

        async def _process_orders(self):
            while True:
                order = await self.orders.get()
                await asyncio.sleep(0.5)  # the slow part: payment, email, ...
                self.processed.append(order)
                self.orders.task_done()

    _service = OrderService()
    _url = await _service.start(workers=5)

    async with aiohttp.ClientSession() as _session:
        with timed("20 orders accepted"):
            await asyncio.gather(*(_session.post(_url, json={"id": i}) for i in range(20)))
    print("processed so far:", len(_service.processed))

    with timed("graceful shutdown"):
        await _service.shutdown()
    print("processed:", len(_service.processed))
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
async def _(BeautifulSoup, aiohttp, asyncio, start, timed, urljoin):
    class Crawler:
        def __init__(self, max_depth: int):
            self.max_depth = max_depth
            self.queue = asyncio.Queue()  # (depth, url) pairs
            self.seen = set()

        async def crawl(self, start_url: str, workers: int) -> int:
            """Crawl from `start_url` with N worker tasks; return how many pages were found."""
            self._add(start_url, depth=0)
            async with aiohttp.ClientSession() as session:
                tasks = [asyncio.create_task(self._worker(session)) for _ in range(workers)]
                await self.queue.join()  # every page, including the ones found along the way, is done
                for task in tasks:
                    task.cancel()
            return len(self.seen)

        async def _worker(self, session: aiohttp.ClientSession):
            while True:
                depth, url = await self.queue.get()
                try:
                    async with session.get(url) as response:
                        html = await response.text()
                    if depth < self.max_depth:
                        for link in BeautifulSoup(html, "html.parser").find_all("a", href=True):
                            self._add(urljoin(url, link["href"]), depth + 1)
                finally:
                    self.queue.task_done()

        def _add(self, url: str, depth: int):
            if url not in self.seen:
                self.seen.add(url)
                self.queue.put_nowait((depth, url))

    _site = f"{await start()}/page/0"
    with timed("1 worker"):
        print("pages crawled:", await Crawler(max_depth=3).crawl(_site, workers=1))
    with timed("10 workers"):
        print("pages crawled:", await Crawler(max_depth=3).crawl(_site, workers=10))
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
def _(asyncio, dataclass, field):
    @dataclass(order=True)
    class Job:
        priority: int  # 1 = power user, 2 = normal user
        name: str = field(compare=False)

    _jobs = [(2, "normal 1"), (2, "normal 2"), (2, "normal 3"), (1, "power 1"), (2, "normal 4")]

    _priority = asyncio.PriorityQueue()
    for _p, _name in _jobs:
        _priority.put_nowait(Job(_p, _name))
    print("PriorityQueue:          ", [_priority.get_nowait().name for _ in _jobs])

    _fair = asyncio.PriorityQueue()
    for _order, (_p, _name) in enumerate(_jobs):
        _fair.put_nowait((_p, _order, _name))  # the order breaks ties
    print("PriorityQueue + counter:", [_fair.get_nowait()[2] for _ in _jobs])

    _lifo = asyncio.LifoQueue()
    for _p, _name in _jobs:
        _lifo.put_nowait(_name)
    print("LifoQueue:              ", [_lifo.get_nowait() for _ in _jobs])
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
