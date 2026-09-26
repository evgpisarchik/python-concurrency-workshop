"""Listing 5.10: a failing statement rolls back the whole transaction.

Use case: keep data consistent. The second insert violates the primary key,
so the first one is rolled back too and no 'big_brand' row remains.

Run: uv run python -m workshop.ch05_async_databases.09_transaction_rollback
"""

import asyncio
import logging

import asyncpg

from workshop.common import db_config


async def main():
    connection = await asyncpg.connect(**db_config("products"))
    try:
        async with connection.transaction():
            insert_brand = "INSERT INTO brand VALUES(9999, 'big_brand')"
            await connection.execute(insert_brand)
            await connection.execute(insert_brand)  # duplicate key: raises
    except Exception:
        logging.exception("Error while running transaction")
    finally:
        query = "SELECT brand_name FROM brand WHERE brand_name LIKE 'big_%'"
        brands = await connection.fetch(query)
        print(f"Query result was: {brands}")  # [] because the transaction was rolled back

        await connection.close()


asyncio.run(main())
