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

    import asyncpg
    import marimo as mo

    from workshop.common import PRODUCT_QUERY, db_config, timed
    from workshop.nb import gate

    return PRODUCT_QUERY, asyncio, asyncpg, db_config, gate, mo, timed


@app.cell
def _(mo):
    db_button = mo.ui.run_button(label="Run database demos")
    db_button
    return (db_button,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Connect

    *Listing 5.1.* The demos below share one **pool** of 6 connections (more on pools in a moment).
    """)
    return


@app.cell
async def _(asyncpg, db_button, db_config, gate):
    gate(db_button, "the database demos")
    db = db_config("products")
    pool = await asyncpg.create_pool(**db, min_size=6, max_size=6)
    print(f"{await pool.fetchval('SELECT count(*) FROM sku'):,} SKUs in the database")
    return db, pool


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## One connection runs one query at a time

    A single connection is a single conversation with the server. Trying to run two queries on it concurrently fails.
    **For concurrency, you need several connections.**
    """)
    return


@app.cell
async def _(asyncio, pool):
    async with pool.acquire() as _connection:
        _first, _second = await asyncio.gather(
            _connection.fetchval("SELECT 'first query done'"),
            _connection.fetchval("SELECT 'second query done'"),
            return_exceptions=True,
        )
    print(_first)
    print(repr(_second))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Connection pools

    *Listings 5.7, 5.8.* A pool keeps N connections open and lends them out with `async with pool.acquire()`.
    1,000 queries through the pool of 6, one by one and concurrently:
    """)
    return


@app.cell
async def _(PRODUCT_QUERY, asyncio, pool, timed):
    async def query_product():
        async with pool.acquire() as connection:
            return await connection.fetchrow(PRODUCT_QUERY)

    with timed("1,000 queries one by one"):
        [await query_product() for _ in range(1000)]

    with timed("1,000 queries concurrently"):
        await asyncio.gather(*(query_product() for _ in range(1000)))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Pool size is the concurrency limit: 10 queries that each take 0.5 s, with pools of different sizes.
    """)
    return


@app.cell
async def _(asyncio, asyncpg, db, timed):
    async def ten_slow_queries(pool_size: int):
        async with asyncpg.create_pool(**db, min_size=pool_size, max_size=pool_size) as pool:
            with timed(f"pool size {pool_size}"):
                await asyncio.gather(*(pool.fetchval("SELECT pg_sleep(0.5)") for _ in range(10)))

    await ten_slow_queries(1)
    await ten_slow_queries(5)
    await ten_slow_queries(10)
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
async def _(asyncio):
    async def countdown(start: int):
        for number in range(start, 0, -1):
            await asyncio.sleep(0.5)  # stands in for I/O
            yield number

    async for _number in countdown(3):
        print(_number)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *Listings 5.15–5.17.* A server-side **cursor** is an async generator over a query: it streams a huge result set in
    batches instead of loading it into memory. Cursors require a transaction.
    """)
    return


@app.cell
async def _(pool):
    async with pool.acquire() as _connection, _connection.transaction():
        _rows = 0
        async for _row in _connection.cursor("SELECT * FROM sku"):  # fetched 50 rows at a time
            _rows += 1
        print(f"streamed {_rows:,} rows without holding them all in memory")
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
