"""Process-pool worker that runs its own event loop and connection pool (one loop per process)."""

import asyncio

import asyncpg

from workshop.common import PRODUCT_QUERY, db_config


def query_products_in_new_loop(num_queries: int) -> int:
    async def run_queries():
        async with asyncpg.create_pool(**db_config("products"), min_size=6, max_size=6) as pool:

            async def query():
                async with pool.acquire() as connection:
                    return await connection.fetchrow(PRODUCT_QUERY)

            return await asyncio.gather(*(query() for _ in range(num_queries)))

    return len(asyncio.run(run_queries()))  # return a count: asyncpg Records can't be pickled
