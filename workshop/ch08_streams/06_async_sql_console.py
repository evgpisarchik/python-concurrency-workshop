"""Listing 8.11: a console that runs SQL queries concurrently.

Use case: an interactive tool that fires off long queries without waiting for
each one. Results show up at the top as each query completes.

Prereq: products DB from chapter 5
Run:    uv run python -m workshop.ch08_streams.06_async_sql_console
        then type e.g.  SELECT * FROM product  or  SELECT pg_sleep(5)
"""

import asyncio
import os
import sys
import tty

import asyncpg
from asyncpg.pool import Pool

from workshop.ch08_streams.terminal import (
    MessageStore,
    create_stdin_reader,
    make_redraw,
    move_to_bottom_of_screen,
    read_line,
)
from workshop.common import db_config


async def run_query(query: str, pool: Pool, message_store: MessageStore):
    async with pool.acquire() as connection:
        try:
            result = await connection.fetch(query)
            await message_store.append(f"Fetched {len(result)} rows from: {query}")
        except Exception as e:
            await message_store.append(f"Got exception {e} from: {query}")


async def main():
    tty.setcbreak(sys.stdin)
    os.system("clear")
    rows = move_to_bottom_of_screen()

    messages = MessageStore(make_redraw(), rows - 1)

    stdin_reader = await create_stdin_reader()

    async with asyncpg.create_pool(**db_config("products"), min_size=6, max_size=6) as pool:
        while True:
            query = await read_line(stdin_reader)
            asyncio.create_task(run_query(query, pool, messages))


asyncio.run(main())
