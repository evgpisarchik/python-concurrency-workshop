"""Listing 5.7: run queries concurrently through a connection pool.

Use case: ONE connection can run only one query at a time. To run queries
concurrently you need several connections, and a pool keeps them open and
lends them out with `async with pool.acquire()`.

Run: uv run python -m workshop.ch05_async_databases.06_connection_pool_queries
"""

import asyncio

import asyncpg

from workshop.common import PRODUCT_QUERY, db_config


async def query_product(pool):
    async with pool.acquire() as connection:
        return await connection.fetchrow(PRODUCT_QUERY)


async def main():
    async with asyncpg.create_pool(**db_config("products"), min_size=6, max_size=6) as pool:
        results = await asyncio.gather(query_product(pool), query_product(pool))
        print(results)


asyncio.run(main())
