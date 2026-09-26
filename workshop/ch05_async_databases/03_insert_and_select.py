"""Listing 5.4: insert rows and read them back as Records.

Use case: basic CRUD. execute() for statements, fetch() for many rows,
fetchrow() for one. A Record behaves like a tuple and a dict at the same time.

Run: uv run python -m workshop.ch05_async_databases.03_insert_and_select
"""

import asyncio

import asyncpg
from asyncpg import Record

from workshop.common import db_config


async def main():
    connection = await asyncpg.connect(**db_config("products"))
    await connection.execute("INSERT INTO brand VALUES(DEFAULT, 'Levis')")
    await connection.execute("INSERT INTO brand VALUES(DEFAULT, 'Seven')")

    brand_query = "SELECT brand_id, brand_name FROM brand"
    results: list[Record] = await connection.fetch(brand_query)

    for brand in results:
        print(f"id: {brand['brand_id']}, name: {brand['brand_name']}")

    await connection.close()


asyncio.run(main())
