"""Listing 5.12: manage a transaction by hand with start/commit/rollback.

Use case: when commit or rollback depends on logic that doesn't fit a
single `async with` block (for example, commit only if validation passes).

Run: uv run python -m workshop.ch05_async_databases.11_manual_transaction
"""

import asyncio

import asyncpg
from asyncpg.transaction import Transaction

from workshop.common import db_config


async def main():
    connection = await asyncpg.connect(**db_config("products"))
    transaction: Transaction = connection.transaction()
    await transaction.start()
    try:
        await connection.execute("INSERT INTO brand VALUES(DEFAULT, 'brand_1')")
        await connection.execute("INSERT INTO brand VALUES(DEFAULT, 'brand_2')")
    except asyncpg.PostgresError:
        print("Errors, rolling back transaction!")
        await transaction.rollback()
    else:
        print("No errors, committing transaction!")
        await transaction.commit()

    query = "SELECT brand_name FROM brand WHERE brand_name LIKE 'brand%'"
    brands = await connection.fetch(query)
    print(brands)

    await connection.close()


asyncio.run(main())
