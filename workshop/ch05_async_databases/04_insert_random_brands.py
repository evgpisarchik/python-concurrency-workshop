"""Listing 5.5: bulk insert with executemany and query parameters ($1).

Use case: load seed or test data quickly and safely. Parameters are sent
separately from the SQL, which prevents SQL injection.

Run: uv run python -m workshop.ch05_async_databases.04_insert_random_brands
"""

import asyncio
from random import sample

import asyncpg

from workshop.ch05_async_databases.products_db import load_common_words
from workshop.common import db_config


def generate_brand_names(words: list[str]) -> list[tuple[str]]:
    return [(words[index],) for index in sample(range(100), 100)]


async def insert_brands(common_words: list[str], connection) -> None:
    brands = generate_brand_names(common_words)
    insert_brands_sql = "INSERT INTO brand VALUES(DEFAULT, $1)"
    return await connection.executemany(insert_brands_sql, brands)


async def main():
    common_words = load_common_words()
    connection = await asyncpg.connect(**db_config("products"))
    await insert_brands(common_words, connection)
    print("Inserted 100 brands")
    await connection.close()


asyncio.run(main())
