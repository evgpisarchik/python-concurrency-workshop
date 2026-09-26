"""Listing 5.6: generate 1,000 products and 100,000 SKUs.

Use case: build a realistically sized dataset for benchmarks (5.8, 6.15,
ch9 load tests).

Run: uv run python -m workshop.ch05_async_databases.05_insert_random_products_and_skus
"""

import asyncio
from random import randint, sample

import asyncpg

from workshop.ch05_async_databases.products_db import load_common_words
from workshop.common import db_config


def gen_products(
    common_words: list[str], brand_id_start: int, brand_id_end: int, products_to_create: int
) -> list[tuple[str, int]]:
    products = []
    for _ in range(products_to_create):
        description = [common_words[index] for index in sample(range(1000), 10)]
        brand_id = randint(brand_id_start, brand_id_end)
        products.append((" ".join(description), brand_id))
    return products


def gen_skus(product_id_start: int, product_id_end: int, skus_to_create: int) -> list[tuple[int, int, int]]:
    skus = []
    for _ in range(skus_to_create):
        product_id = randint(product_id_start, product_id_end)
        size_id = randint(1, 3)
        color_id = randint(1, 2)
        skus.append((product_id, size_id, color_id))
    return skus


async def main():
    common_words = load_common_words()
    connection = await asyncpg.connect(**db_config("products"))

    brand_ids = [r["brand_id"] for r in await connection.fetch("SELECT brand_id FROM brand")]
    product_tuples = gen_products(
        common_words, brand_id_start=min(brand_ids), brand_id_end=max(brand_ids), products_to_create=1000
    )
    await connection.executemany("INSERT INTO product VALUES(DEFAULT, $1, $2)", product_tuples)

    product_ids = await connection.fetchrow("SELECT min(product_id), max(product_id) FROM product")
    sku_tuples = gen_skus(product_id_start=product_ids[0], product_id_end=product_ids[1], skus_to_create=100_000)
    await connection.executemany("INSERT INTO sku VALUES(DEFAULT, $1, $2, $3)", sku_tuples)

    print("Inserted 1,000 products and 100,000 SKUs")
    await connection.close()


asyncio.run(main())
