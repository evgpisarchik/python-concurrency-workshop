import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium", app_title="5 · Async databases")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 5 · Non-blocking databases with asyncpg

    A blocking driver (psycopg2, `psycopg` in sync mode) stops the event loop for the whole duration of every query.
    An async driver (asyncpg, psycopg3 async, SQLAlchemy async) awaits the database like any other socket.

    **Setup (once):**

    ```bash
    docker compose up -d                    # Postgres on localhost:55432
    uv run python -m workshop.db_setup      # create + seed the products database
    ```
    """)
    return


@app.cell
def _():
    import asyncio
    import time

    import asyncpg
    import marimo as mo

    from workshop.common import PRODUCT_QUERY, async_timed, db_config, delay
    from workshop.nb import gate

    return (
        PRODUCT_QUERY,
        async_timed,
        asyncio,
        asyncpg,
        db_config,
        delay,
        gate,
        mo,
        time,
    )


@app.cell
def _(mo):
    db_button = mo.ui.run_button(label="Run database demos")
    db_button
    return (db_button,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Connect

    *Listing 5.1.*
    """)
    return


@app.cell
async def _(asyncpg, db_button, db_config, gate):
    gate(db_button, "the database demos")
    _connection = await asyncpg.connect(**db_config("products"))
    print(f"Connected! Postgres {_connection.get_server_version().major}")
    print(f"{await _connection.fetchval('SELECT count(*) FROM sku'):,} SKUs in the database")
    await _connection.close()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## One connection runs one query at a time

    A single connection is a single conversation with the server. Trying to run two queries on it concurrently fails.
    **For concurrency, you need several connections.**
    """)
    return


@app.cell
async def _(asyncio, asyncpg, db_button, db_config, gate):
    gate(db_button, "the database demos")
    _connection = await asyncpg.connect(**db_config("products"))
    try:
        _ = await asyncio.gather(_connection.fetch("SELECT pg_sleep(0.5)"), _connection.fetch("SELECT pg_sleep(0.5)"))
    except asyncpg.InterfaceError as error:
        print(f"{type(error).__name__}: {error}")
    finally:
        _ = await _connection.close()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Connection pools

    *Listings 5.7, 5.8.* A pool keeps N connections open and lends them out with `async with pool.acquire()`.
    10,000 queries through a pool of 6: sequential vs concurrent.
    """)
    return


@app.cell
async def _(
    PRODUCT_QUERY,
    async_timed,
    asyncio,
    asyncpg,
    db_button,
    db_config,
    gate,
):
    gate(db_button, "the database demos")

    async def query_product(pool: asyncpg.Pool):
        async with pool.acquire() as connection:
            return await connection.fetchrow(PRODUCT_QUERY)

    @async_timed()
    async def query_products_sequentially(pool, queries):
        return [await query_product(pool) for _ in range(queries)]

    @async_timed()
    async def query_products_concurrently(pool, queries):
        return await asyncio.gather(*(query_product(pool) for _ in range(queries)))

    async with asyncpg.create_pool(**db_config("products"), min_size=6, max_size=6) as _pool:
        await query_products_sequentially(_pool, 10_000)
        await query_products_concurrently(_pool, 10_000)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Pool size is the concurrency limit: 10 queries that each take 0.5 s, with pools of different sizes.
    """)
    return


@app.cell
async def _(asyncio, asyncpg, db_button, db_config, gate, time):
    gate(db_button, "the database demos")
    for _size in (1, 5, 10):
        async with asyncpg.create_pool(**db_config("products"), min_size=_size, max_size=_size) as _pool:
            _start = time.perf_counter()
            await asyncio.gather(*(_pool.fetchval("SELECT pg_sleep(0.5)") for _ in range(10)))
            print(f"pool size {_size:>2}: {time.perf_counter() - _start:.2f} s")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Async generators and streaming results

    *Listings 5.13, 5.14.* An **async generator** (`async def` + `yield`) produces values that need I/O to get, and you
    consume it with `async for`. Typical uses are paginated APIs, message streams and database cursors.
    """)
    return


@app.cell
async def _(delay):
    async def positive_integers_async(until: int):
        for integer in range(1, until):
            await delay(integer)
            yield integer

    async for _number in positive_integers_async(3):
        print(f"got number {_number}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *Listings 5.15–5.17.* A server-side **cursor** streams a huge result set in batches instead of loading it into memory
    (cursors require a transaction). Async generators compose, much like `itertools`:
    """)
    return


@app.cell
async def _(asyncpg, db_button, db_config, gate):
    gate(db_button, "the database demos")

    async def take(generator, to_take: int):
        taken = 0
        async for item in generator:
            if taken >= to_take:
                return
            taken += 1
            yield item

    _connection = await asyncpg.connect(**db_config("products"))
    async with _connection.transaction():
        _rows = 0
        async for _ in _connection.cursor("SELECT * FROM sku"):  # fetched 50 rows at a time
            _rows += 1
        print(f"streamed {_rows:,} rows without holding them all in memory")

        async for _product in take(_connection.cursor("SELECT product_id, product_name FROM product"), 3):
            print(_product)
    await _connection.close()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Takeaways

    * Use an async driver inside async code, because a sync driver blocks the loop (measured in notebook 9).
    * One connection runs one query at a time. A **pool** gives concurrency, and its size is the limit.
    * Stream big results with cursors plus `async for` to keep memory flat.
    """)
    return


if __name__ == "__main__":
    app.run()
