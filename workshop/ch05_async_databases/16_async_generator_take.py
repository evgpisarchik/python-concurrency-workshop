"""Listing 5.17: take the first N items from any async generator.

Use case: combine async generators like itertools.islice. Here we stop
reading the cursor after 5 rows.

Run: uv run python -m workshop.ch05_async_databases.16_async_generator_take
"""

import asyncio

import asyncpg

from workshop.common import db_config


async def take(generator, to_take: int):
    item_count = 0
    async for item in generator:
        if item_count > to_take - 1:
            return
        item_count = item_count + 1
        yield item


async def main():
    connection = await asyncpg.connect(**db_config("products"))
    async with connection.transaction():
        query = "SELECT product_id, product_name FROM product"
        product_generator = connection.cursor(query)

        async for product in take(product_generator, 5):
            print(product)

        print("Got the first five products!")

    await connection.close()


asyncio.run(main())
