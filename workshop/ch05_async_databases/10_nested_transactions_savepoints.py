"""Listing 5.11: nested transactions (savepoints).

Use case: let an optional part of a unit of work fail without losing the
rest. The inner block becomes a SAVEPOINT. Its failure rolls back only the
inner insert, and the brand insert still commits.

Run: uv run python -m workshop.ch05_async_databases.10_nested_transactions_savepoints
"""

import asyncio
import logging

import asyncpg

from workshop.common import db_config


async def main():
    connection = await asyncpg.connect(**db_config("products"))
    async with connection.transaction():
        await connection.execute("INSERT INTO brand VALUES(DEFAULT, 'my_new_brand')")

        try:
            async with connection.transaction():
                # color id 1 already exists: fails, but only this savepoint rolls back
                await connection.execute("INSERT INTO product_color VALUES(1, 'black')")
        except Exception as ex:
            logging.warning("Ignoring error inserting product color", exc_info=ex)

    print(await connection.fetch("SELECT * FROM brand WHERE brand_name = 'my_new_brand'"))
    await connection.close()


asyncio.run(main())
