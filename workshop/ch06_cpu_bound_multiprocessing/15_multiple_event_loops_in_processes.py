"""Listing 6.15: one event loop per process to scale I/O beyond one core.

Use case: when a single event loop becomes CPU-bound (for example, parsing
lots of DB rows), run N processes that each run their own asyncio loop and
connection pool. This is what `uvicorn --workers N` / gunicorn do.

Prereq: products DB from chapter 5
Run:    uv run python -m workshop.ch06_cpu_bound_multiprocessing.15_multiple_event_loops_in_processes
"""

import asyncio
from concurrent.futures import ProcessPoolExecutor

import asyncpg

from workshop.common import PRODUCT_QUERY, async_timed, db_config


async def query_product(pool):
    async with pool.acquire() as connection:
        return await connection.fetchrow(PRODUCT_QUERY)


@async_timed()
async def query_products_concurrently(pool, queries):
    queries = [query_product(pool) for _ in range(queries)]
    return await asyncio.gather(*queries)


def run_in_new_loop(num_queries: int) -> list[dict]:
    async def run_queries():
        async with asyncpg.create_pool(**db_config("products"), min_size=6, max_size=6) as pool:
            return await query_products_concurrently(pool, num_queries)

    # asyncpg Records can't be pickled back to the parent process, so convert them to dicts
    return [dict(result) for result in asyncio.run(run_queries())]


@async_timed()
async def main():
    loop = asyncio.get_running_loop()
    with ProcessPoolExecutor() as pool:
        tasks = [loop.run_in_executor(pool, run_in_new_loop, 10_000) for _ in range(5)]
        all_results = await asyncio.gather(*tasks)
        total_queries = sum(len(result) for result in all_results)
        print(f"Retrieved {total_queries} products the product database.")


if __name__ == "__main__":
    asyncio.run(main())
