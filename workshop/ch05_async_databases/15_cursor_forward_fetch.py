"""Listing 5.16: move a cursor forward and fetch a page.

Use case: skip rows and read a specific page (offset 500, 100 rows) without
transferring the skipped rows to the client.

Run: uv run python -m workshop.ch05_async_databases.15_cursor_forward_fetch
"""

import asyncio

import asyncpg

from workshop.common import db_config


async def main():
    connection = await asyncpg.connect(**db_config("products"))
    async with connection.transaction():
        query = "SELECT product_id, product_name FROM product"
        cursor = await connection.cursor(query)  # awaited: a cursor object, not an iterator
        await cursor.forward(500)  # skip the first 500 rows on the server
        products = await cursor.fetch(100)
        for product in products:
            print(product)

    await connection.close()


asyncio.run(main())
