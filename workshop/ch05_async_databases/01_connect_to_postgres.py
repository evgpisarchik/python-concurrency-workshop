"""Listing 5.1: connect to Postgres with asyncpg.

Use case: a non-blocking database driver. While a query waits on the
network, the event loop serves other requests. (psycopg2 would block it.)

Prereq: docker compose up -d
Run:    uv run python -m workshop.ch05_async_databases.01_connect_to_postgres
"""

import asyncio

import asyncpg

from workshop.common import db_config


async def main():
    connection = await asyncpg.connect(**db_config("postgres"))
    version = connection.get_server_version()
    print(f"Connected! Postgres version is {version}")
    await connection.close()


asyncio.run(main())
