"""Listing 10.4: reusable aiohttp startup/cleanup hooks for an asyncpg pool.

Each microservice owns its own database, so the database name is a parameter
(bound with functools.partial when registering the hook).
"""

import asyncpg
from aiohttp import web
from asyncpg.pool import Pool

from workshop.common import db_config

DB_KEY = web.AppKey("database", Pool)


async def create_database_pool(app: web.Application, database: str):
    app[DB_KEY] = await asyncpg.create_pool(**db_config(database), min_size=6, max_size=6)


async def destroy_database_pool(app: web.Application):
    await app[DB_KEY].close()
