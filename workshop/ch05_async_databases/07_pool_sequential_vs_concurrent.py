"""Listing 5.8: benchmark 10,000 queries, sequential vs concurrent.

Use case: measure what concurrency gives you with a database. With 6 pooled
connections the concurrent version is several times faster.

Run: uv run python -m workshop.ch05_async_databases.07_pool_sequential_vs_concurrent
"""

import asyncio

import asyncpg

from workshop.common import PRODUCT_QUERY, async_timed, db_config


async def query_product(pool):
    async with pool.acquire() as connection:
        return await connection.fetchrow(PRODUCT_QUERY)


@async_timed()
async def query_products_synchronously(pool, queries):
    return [await query_product(pool) for _ in range(queries)]


@async_timed()
async def query_products_concurrently(pool, queries):
    queries = [query_product(pool) for _ in range(queries)]
    return await asyncio.gather(*queries)


async def main():
    async with asyncpg.create_pool(**db_config("products"), min_size=6, max_size=6) as pool:
        await query_products_synchronously(pool, 10_000)
        await query_products_concurrently(pool, 10_000)


asyncio.run(main())
