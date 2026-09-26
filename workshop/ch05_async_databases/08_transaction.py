"""Listing 5.9: a transaction with `async with connection.transaction()`.

Use case: several writes that must succeed or fail together. The block
commits when it exits normally and rolls back when it raises.

Run: uv run python -m workshop.ch05_async_databases.08_transaction
"""

import asyncio

import asyncpg

from workshop.common import db_config


async def main():
    connection = await asyncpg.connect(**db_config("products"))
    async with connection.transaction():
        await connection.execute("INSERT INTO brand VALUES(DEFAULT, 'brand_1')")
        await connection.execute("INSERT INTO brand VALUES(DEFAULT, 'brand_2')")

    query = "SELECT brand_name FROM brand WHERE brand_name LIKE 'brand%'"
    brands = await connection.fetch(query)
    print(brands)

    await connection.close()


asyncio.run(main())
