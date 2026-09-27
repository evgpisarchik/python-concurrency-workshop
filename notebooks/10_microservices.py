import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium", app_title="10 · Microservices")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 10 · Microservices: concurrent fan-out, graceful degradation, retries, circuit breakers

    A **backend-for-frontend (BFF)** gives the UI one endpoint and calls several services behind it **concurrently**,
    so latency is roughly the slowest call rather than the sum. It also has to decide what to do when a service is slow or down.

    ```
                          ┌─► product service   :8201  (required)
    UI ─► BFF :8200 ──────┼─► favorites service :8203  (optional)
       /products/all      ├─► cart service      :8204  (optional)
                          └─► inventory service :8202  (per product, 0-2 s, 1 s budget)
    ```

    Code: `workshop/microservices/`. Needs the database (`docker compose up -d`, `uv run python -m workshop.db_setup`);
    the `cart` and `favorites` databases are created by `docker/initdb`.
    """)
    return


@app.cell
def _():
    import asyncio
    import itertools
    import time

    import aiohttp
    import marimo as mo

    from workshop.common import timed
    from workshop.microservices import BFF_PORT, CART_PORT, FAVORITES_PORT, INVENTORY_PORT, PRODUCT_PORT
    from workshop.nb import gate, start_server, stop_server

    return (
        BFF_PORT,
        CART_PORT,
        FAVORITES_PORT,
        INVENTORY_PORT,
        PRODUCT_PORT,
        aiohttp,
        asyncio,
        gate,
        itertools,
        mo,
        start_server,
        stop_server,
        time,
        timed,
    )


@app.cell
def _(mo):
    services_button = mo.ui.run_button(label="Start the services and call the BFF")
    services_button
    return (services_button,)


@app.cell
async def _(
    BFF_PORT,
    CART_PORT,
    FAVORITES_PORT,
    INVENTORY_PORT,
    PRODUCT_PORT,
    aiohttp,
    gate,
    services_button,
    start_server,
    stop_server,
    timed,
):
    gate(services_button)
    _products = start_server(["-m", "workshop.microservices.products"], PRODUCT_PORT)
    start_server(["-m", "workshop.microservices.inventory"], INVENTORY_PORT)
    start_server(["-m", "workshop.microservices.user_lists", "favorites"], FAVORITES_PORT)
    _cart = start_server(["-m", "workshop.microservices.user_lists", "cart"], CART_PORT)
    start_server(["-m", "workshop.microservices.bff"], BFF_PORT)

    async def call_bff():
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://127.0.0.1:{BFF_PORT}/products/all") as response:
                body = await response.json()
        if response.status != 200:
            print("HTTP", response.status, body)
        else:
            inventory = [product["inventory"] for product in body["products"]]
            print("HTTP 200, cart:", body["cart"], "| inventory:", inventory)

    with timed("all services up"):
        await call_bff()

    stop_server(_cart)
    with timed("cart service down"):
        await call_bff()

    stop_server(_products)
    with timed("products service down"):
        await call_bff()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    What you should see:

    * every call takes ~1 s at most, however slow inventory gets, because of the time budget
    * products whose inventory didn't arrive in time get `None` instead of failing the whole page
    * optional data (cart) that's missing becomes `None`
    * required data (products) that's missing produces an error response, **fast**

    The core of `bff.py`:

    ```python
    products = asyncio.create_task(get_json(session, PRODUCT_PORT, "/products"))
    favorites = asyncio.create_task(get_json(session, FAVORITES_PORT, "/users/3/favorites"))
    cart = asyncio.create_task(get_json(session, CART_PORT, "/users/3/cart"))
    done, pending = await asyncio.wait([products, favorites, cart], timeout=1.0)
    if products not in done: ...                  # 504
    if products.exception() is not None: ...      # 500
    cart_items = result_or_none(cart, done)       # optional: None if it failed or was too slow
    ```

    ## Retries

    *Listings 10.9, 10.10.* Retry transient failures with a **per-attempt timeout** and a pause between attempts, then give up.
    Pass a *factory* (a function returning a new coroutine), because a coroutine object can be awaited only once.
    """)
    return


@app.cell
async def _(asyncio, itertools):
    async def retry(coro_factory, attempts: int, timeout: float, pause: float):
        for attempt in range(1, attempts + 1):
            try:
                return await asyncio.wait_for(coro_factory(), timeout)
            except Exception as error:
                print(f"  attempt {attempt} failed: {error!r}")
                await asyncio.sleep(pause)
        raise RuntimeError(f"gave up after {attempts} attempts")

    _calls = itertools.count(1)

    async def flaky_service():
        if next(_calls) < 3:  # fails twice, then works
            raise ConnectionError("blip")
        return "ok"

    async def dead_service():
        await asyncio.sleep(10)

    print("flaky service:", await retry(flaky_service, attempts=5, timeout=0.1, pause=0.1))
    try:
        await retry(dead_service, attempts=3, timeout=0.1, pause=0.1)
    except RuntimeError as _error:
        print("dead service:", _error)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Circuit breaker

    *Listings 10.11, 10.12.* Retries against a service that is **down** just add load and latency. A circuit breaker counts
    failures, and after `max_failures` it **opens**: calls fail immediately without touching the service. After
    `reset_interval` it lets a request through again to check whether the service has recovered.
    """)
    return


@app.cell
def _(asyncio, time):
    class CircuitOpenError(Exception):
        pass

    class CircuitBreaker:
        def __init__(self, callback, timeout: float, max_failures: int, reset_interval: float):
            self.callback = callback
            self.timeout = timeout
            self.max_failures = max_failures
            self.reset_interval = reset_interval
            self.failures = 0
            self.last_failure = 0.0

        async def request(self):
            if self.failures >= self.max_failures:
                if time.monotonic() - self.last_failure < self.reset_interval:
                    raise CircuitOpenError("circuit open: failing fast")
                self.failures = 0  # half-open: let one request through to test the service
            try:
                return await asyncio.wait_for(self.callback(), self.timeout)
            except Exception:
                self.failures += 1
                self.last_failure = time.monotonic()
                raise

    return CircuitBreaker, CircuitOpenError


@app.cell
async def _(CircuitBreaker, CircuitOpenError, asyncio, timed):
    async def slow_service():
        await asyncio.sleep(1)

    _breaker = CircuitBreaker(slow_service, timeout=0.5, max_failures=2, reset_interval=2)

    async def attempt(name: str):
        with timed(name):
            try:
                await _breaker.request()
            except (TimeoutError, CircuitOpenError) as error:
                print(f"{name}: {error!r}")

    await attempt("request 1")
    await attempt("request 2")
    await attempt("request 3")  # the circuit is open now
    await asyncio.sleep(2)  # wait for the reset interval
    await attempt("request 4")  # a trial request reaches the service again
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Takeaways

    * Fan out to independent services **concurrently**, with a time budget (`wait(..., timeout=)`).
    * Decide per dependency: **required** (fail fast with 5xx) or **optional** (degrade to `None`).
    * Retries absorb short blips. Circuit breakers stop you from hammering, and waiting on, a service that's down.
    """)
    return


if __name__ == "__main__":
    app.run()
