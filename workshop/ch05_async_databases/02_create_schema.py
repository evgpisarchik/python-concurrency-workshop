"""Listing 5.3: create the products schema by running DDL statements.

Use case: run migrations and setup scripts with connection.execute().
Running this is required before the other chapter 5, 9 and 10 examples.

Run: uv run python -m workshop.ch05_async_databases.02_create_schema
"""

import asyncio

import asyncpg

from workshop.ch05_async_databases.products_db import (
    COLOR_INSERT,
    CREATE_BRAND_TABLE,
    CREATE_PRODUCT_COLOR_TABLE,
    CREATE_PRODUCT_SIZE_TABLE,
    CREATE_PRODUCT_TABLE,
    CREATE_SKU_TABLE,
    SIZE_INSERT,
)
from workshop.common import db_config


async def main():
    connection = await asyncpg.connect(**db_config("products"))
    statements = [
        CREATE_BRAND_TABLE,
        CREATE_PRODUCT_TABLE,
        CREATE_PRODUCT_COLOR_TABLE,
        CREATE_PRODUCT_SIZE_TABLE,
        CREATE_SKU_TABLE,
        SIZE_INSERT,
        COLOR_INSERT,
    ]

    print("Creating the product database...")
    for statement in statements:
        status = await connection.execute(statement)
        print(status)
    print("Finished creating the product database!")
    await connection.close()


asyncio.run(main())
