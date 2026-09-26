"""Shared aiohttp startup/cleanup hooks that own an asyncpg pool (from listing 9.2).

Create the pool ONCE on startup, store it on the app, and close it on cleanup.
Every request borrows a connection from it. web.AppKey gives type-safe
app[...] storage (a plain string key triggers a warning in aiohttp 3.9+).
"""

import asyncpg
from aiohttp import web
from asyncpg.pool import Pool

from workshop.common import db_config

DB_KEY = web.AppKey("database", Pool)


async def create_database_pool(app: web.Application):
    print("Creating database pool.")
    app[DB_KEY] = await asyncpg.create_pool(**db_config("products"), min_size=6, max_size=6)


async def destroy_database_pool(app: web.Application):
    print("Destroying database pool.")
    await app[DB_KEY].close()
