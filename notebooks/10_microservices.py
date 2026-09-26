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
    import random
    import time
    from datetime import datetime, timedelta

    import aiohttp
    import marimo as mo

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
        datetime,
        gate,
        mo,
        random,
        start_server,
        stop_server,
        time,
        timedelta,
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
    time,
):
    gate(services_button)
    _services = {
        "products": start_server(["-m", "workshop.microservices.products"], PRODUCT_PORT),
        "inventory": start_server(["-m", "workshop.microservices.inventory"], INVENTORY_PORT),
        "favorites": start_server(["-m", "workshop.microservices.user_lists", "favorites"], FAVORITES_PORT),
        "cart": start_server(["-m", "workshop.microservices.user_lists", "cart"], CART_PORT),
        "bff": start_server(["-m", "workshop.microservices.bff"], BFF_PORT),
    }

    async def call_bff(label: str):
        async with aiohttp.ClientSession() as session:
            start = time.perf_counter()
            async with session.get(f"http://127.0.0.1:{BFF_PORT}/products/all") as response:
                body = await response.json()
            elapsed = time.perf_counter() - start
        if response.status != 200:
            print(f"{label:<28} HTTP {response.status} in {elapsed:.2f} s: {body['error']}")
            return
        known = sum(p["inventory"] is not None for p in body["products"])
        print(
            f"{label:<28} HTTP 200 in {elapsed:.2f} s: cart={body['cart_items']}, favorites={body['favorite_items']}, "
            f"inventory known for {known}/{len(body['products'])} products"
        )

    try:
        for _i in range(3):
            await call_bff(f"all services up (call {_i + 1})")

        stop_server(_services.pop("cart"))
        await call_bff("cart service down")

        stop_server(_services.pop("products"))
        _ = await call_bff("products service down")
    finally:
        for _proc in _services.values():
            stop_server(_proc)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    What you should see:

    * every call takes ~1 s at most, however slow inventory gets, because of the time budget
    * products whose inventory didn't arrive in time get `null` instead of failing the whole page
    * optional data (cart) that's missing becomes `null`
    * required data (products) that's missing produces an error response, **fast**

    The core of `bff.py`:

    ```python
    products = asyncio.create_task(get_json(session, f"{PRODUCT_BASE}/products"))
    favorites = asyncio.create_task(get_json(session, f"{FAVORITE_BASE}/users/3/favorites"))
    cart = asyncio.create_task(get_json(session, f"{CART_BASE}/users/3/cart"))
    done, pending = await asyncio.wait([products, favorites, cart], timeout=1.0)
    if products in pending: ...                   # 504
    if products.exception() is not None: ...      # 500
    # optional results: use them if done without error, otherwise None (and cancel if still pending)
    ```

    ## Retries

    *Listings 10.9, 10.10.* Retry transient failures with a **per-attempt timeout** and a pause between attempts, then give up.
    Pass a *factory* (a function returning a new coroutine), because a coroutine object can be awaited only once.
    """)
    return


@app.cell
async def _(asyncio, random):
    class TooManyRetries(Exception):
        pass

    async def retry(coro_factory, max_retries: int, timeout: float, retry_interval: float):
        for attempt in range(1, max_retries + 1):
            try:
                return await asyncio.wait_for(coro_factory(), timeout=timeout)
            except Exception as error:
                print(f"  attempt {attempt} failed: {error!r}")
                await asyncio.sleep(retry_interval)
        raise TooManyRetries()

    async def flaky():
        if random.random() < 0.6:
            raise ConnectionError("blip")
        return "ok"

    async def always_timeout():
        await asyncio.sleep(1)

    random.seed(3)
    print("flaky service:", await retry(flaky, max_retries=5, timeout=0.1, retry_interval=0.1))
    try:
        _ = await retry(always_timeout, max_retries=3, timeout=0.1, retry_interval=0.1)
    except TooManyRetries:
        print("always-timeout service: retried too many times")
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
def _(asyncio, datetime, timedelta):
    class CircuitOpenException(Exception):
        pass

    class CircuitBreaker:
        def __init__(self, callback, timeout: float, time_window: float, max_failures: int, reset_interval: float):
            self.callback, self.timeout, self.time_window = callback, timeout, time_window
            self.max_failures, self.reset_interval = max_failures, reset_interval
            self.last_request_time = None
            self.last_failure_time = None
            self.current_failures = 0

        async def request(self, *args, **kwargs):
            if self.current_failures >= self.max_failures:
                if datetime.now() > self.last_request_time + timedelta(seconds=self.reset_interval):
                    self._reset("circuit half-open: trying one request")
                    return await self._do_request(*args, **kwargs)
                raise CircuitOpenException("circuit open: failing fast")
            if self.last_failure_time and datetime.now() > self.last_failure_time + timedelta(seconds=self.time_window):
                self._reset("failure window elapsed: resetting count")
            return await self._do_request(*args, **kwargs)

        def _reset(self, message: str):
            print(f"  {message}")
            self.last_failure_time = None
            self.current_failures = 0

        async def _do_request(self, *args, **kwargs):
            try:
                self.last_request_time = datetime.now()
                return await asyncio.wait_for(self.callback(*args, **kwargs), timeout=self.timeout)
            except Exception:
                self.current_failures += 1
                self.last_failure_time = self.last_failure_time or datetime.now()
                raise

    return CircuitBreaker, CircuitOpenException


@app.cell
async def _(CircuitBreaker, CircuitOpenException, asyncio, time):
    async def slow_service():
        await asyncio.sleep(1)

    async def attempt(breaker: CircuitBreaker, n: int):
        start = time.perf_counter()
        try:
            await breaker.request()
            outcome = "ok"
        except CircuitOpenException as error:
            outcome = str(error)
        except TimeoutError:
            outcome = "timed out"
        print(f"request {n}: {outcome:<27} ({time.perf_counter() - start:.2f} s)")

    _breaker = CircuitBreaker(slow_service, timeout=0.5, time_window=5, max_failures=2, reset_interval=2)
    for _n in range(1, 5):
        await attempt(_breaker, _n)
    print("waiting 2 s for the breaker to allow a trial request...")
    await asyncio.sleep(2)
    await attempt(_breaker, 5)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Takeaways

    * Fan out to independent services **concurrently**, with a time budget (`wait(..., timeout=)`).
    * Decide per dependency: **required** (fail fast with 5xx) or **optional** (degrade to `null`).
    * Retries absorb short blips. Circuit breakers stop you from hammering, and waiting on, a service that's down.
    """)
    return


if __name__ == "__main__":
    app.run()
