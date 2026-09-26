"""Create and seed the `products` database used by the notebooks.

Run once after `docker compose up -d`:
    uv run python -m workshop.db_setup
"""

import asyncio
from pathlib import Path
from random import randint, sample

import asyncpg

from workshop.common import db_config

CREATE_BRAND_TABLE = """
    CREATE TABLE IF NOT EXISTS brand(
        brand_id SERIAL PRIMARY KEY,
        brand_name TEXT NOT NULL
    );"""

CREATE_PRODUCT_TABLE = """
    CREATE TABLE IF NOT EXISTS product(
        product_id SERIAL PRIMARY KEY,
        product_name TEXT NOT NULL,
        brand_id INT NOT NULL,
        FOREIGN KEY (brand_id) REFERENCES brand(brand_id)
    );"""

CREATE_PRODUCT_COLOR_TABLE = """
    CREATE TABLE IF NOT EXISTS product_color(
        product_color_id SERIAL PRIMARY KEY,
        product_color_name TEXT NOT NULL
    );"""

CREATE_PRODUCT_SIZE_TABLE = """
    CREATE TABLE IF NOT EXISTS product_size(
        product_size_id SERIAL PRIMARY KEY,
        product_size_name TEXT NOT NULL
    );"""

CREATE_SKU_TABLE = """
    CREATE TABLE IF NOT EXISTS sku(
       sku_id SERIAL PRIMARY KEY,
       product_id INT NOT NULL,
       product_size_id INT NOT NULL,
       product_color_id INT NOT NULL,
       FOREIGN KEY (product_id) REFERENCES product(product_id),
       FOREIGN KEY (product_size_id) REFERENCES product_size(product_size_id),
       FOREIGN KEY (product_color_id) REFERENCES product_color(product_color_id)
    );"""

COLOR_INSERT = """
    INSERT INTO product_color VALUES(1, 'Blue') ON CONFLICT DO NOTHING;
    INSERT INTO product_color VALUES(2, 'Black') ON CONFLICT DO NOTHING;
    """

SIZE_INSERT = """
    INSERT INTO product_size VALUES(1, 'Small') ON CONFLICT DO NOTHING;
    INSERT INTO product_size VALUES(2, 'Medium') ON CONFLICT DO NOTHING;
    INSERT INTO product_size VALUES(3, 'Large') ON CONFLICT DO NOTHING;
    """

WORDS = (Path(__file__).parent / "common" / "common_words.txt").read_text().split()


async def main() -> None:
    connection = await asyncpg.connect(**db_config("products"))
    for statement in [
        CREATE_BRAND_TABLE,
        CREATE_PRODUCT_TABLE,
        CREATE_PRODUCT_COLOR_TABLE,
        CREATE_PRODUCT_SIZE_TABLE,
        CREATE_SKU_TABLE,
        SIZE_INSERT,
        COLOR_INSERT,
    ]:
        await connection.execute(statement)

    if await connection.fetchval("SELECT count(*) FROM product") > 0:
        print("products database already seeded")
        await connection.close()
        return

    # executemany + $1 parameters: fast, injection-safe bulk inserts
    await connection.executemany("INSERT INTO brand VALUES(DEFAULT, $1)", [(w,) for w in sample(WORDS, 100)])
    brand_ids = [r["brand_id"] for r in await connection.fetch("SELECT brand_id FROM brand")]
    products = [(" ".join(sample(WORDS, 10)), brand_ids[randint(0, len(brand_ids) - 1)]) for _ in range(1000)]
    await connection.executemany("INSERT INTO product VALUES(DEFAULT, $1, $2)", products)
    low, high = await connection.fetchrow("SELECT min(product_id), max(product_id) FROM product")
    skus = [(randint(low, high), randint(1, 3), randint(1, 2)) for _ in range(100_000)]
    await connection.executemany("INSERT INTO sku VALUES(DEFAULT, $1, $2, $3)", skus)
    print("Seeded 100 brands, 1,000 products, 100,000 SKUs")
    await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
