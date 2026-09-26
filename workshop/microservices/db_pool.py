"""aiohttp startup/cleanup hooks that own an asyncpg pool (one database per service)."""

import asyncpg
from aiohttp import web
from asyncpg.pool import Pool

from workshop.common import db_config

DB_KEY = web.AppKey("database", Pool)


def with_database(app: web.Application, database: str) -> web.Application:
    async def create_pool(app: web.Application):
        app[DB_KEY] = await asyncpg.create_pool(**db_config(database), min_size=6, max_size=6)

    async def close_pool(app: web.Application):
        await app[DB_KEY].close()

    app.on_startup.append(create_pool)
    app.on_cleanup.append(close_pool)
    return app
