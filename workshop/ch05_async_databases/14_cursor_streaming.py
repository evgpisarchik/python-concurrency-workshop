"""Listing 5.15: stream a large result set with a server-side cursor.

Use case: iterate over millions of rows without loading them all into memory.
Rows are fetched in batches (prefetch=50 by default) as you iterate. Cursors
must be used inside a transaction.

Run: uv run python -m workshop.ch05_async_databases.14_cursor_streaming
"""

import asyncio

import asyncpg

from workshop.common import db_config


async def main():
    connection = await asyncpg.connect(**db_config("products"))

    query = "SELECT product_id, product_name FROM product"
    async with connection.transaction():
        async for product in connection.cursor(query):
            print(product)

    await connection.close()


asyncio.run(main())
