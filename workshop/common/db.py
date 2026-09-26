"""Postgres connection settings shared by all database examples.

Defaults match docker-compose.yml. Override with the standard PG* environment
variables (PGHOST, PGPORT, PGUSER, PGPASSWORD).
"""

import os
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

PG_HOST = os.getenv("PGHOST", "127.0.0.1")
PG_PORT = int(os.getenv("PGPORT", "55432"))
PG_USER = os.getenv("PGUSER", "postgres")
PG_PASSWORD = os.getenv("PGPASSWORD", "password")


def db_config(database: str = "products") -> dict:
    """Keyword arguments for asyncpg.connect() / asyncpg.create_pool()."""
    return {
        "host": PG_HOST,
        "port": PG_PORT,
        "user": PG_USER,
        "password": PG_PASSWORD,
        "database": database,
    }


def dsn(database: str = "products") -> str:
    """libpq connection string for psycopg (sync driver)."""
    return f"host={PG_HOST} port={PG_PORT} user={PG_USER} password={PG_PASSWORD} dbname={database}"


# Listing 5.7 / 5.8 / 6.15 / 8.11: a join-heavy query used for benchmarks.
PRODUCT_QUERY = """
SELECT
    p.product_id,
    p.product_name,
    p.brand_id,
    s.sku_id,
    pc.product_color_name,
    ps.product_size_name
FROM product AS p
JOIN sku AS s ON s.product_id = p.product_id
JOIN product_color AS pc ON pc.product_color_id = s.product_color_id
JOIN product_size AS ps ON ps.product_size_id = s.product_size_id
WHERE p.product_id = 100
"""
