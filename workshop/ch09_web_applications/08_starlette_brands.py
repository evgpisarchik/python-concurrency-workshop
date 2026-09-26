"""Listing 9.8: the /brands endpoint in Starlette (async, ASGI).

Use case: a lightweight async framework (FastAPI is built on it). The pool is
managed by a *lifespan* context manager, which replaced on_startup/on_shutdown.

Run: uv run uvicorn --workers 8 workshop.ch09_web_applications.08_starlette_brands:app
Then: curl localhost:8000/brands
"""

from contextlib import asynccontextmanager

import asyncpg
from asyncpg import Record
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from workshop.common import db_config


@asynccontextmanager
async def lifespan(app: Starlette):
    app.state.DB = await asyncpg.create_pool(**db_config("products"), min_size=6, max_size=6)
    yield
    await app.state.DB.close()


async def brands(request: Request) -> Response:
    connection = request.app.state.DB
    brand_query = "SELECT brand_id, brand_name FROM brand"
    results: list[Record] = await connection.fetch(brand_query)
    result_as_dict: list[dict] = [dict(brand) for brand in results]
    return JSONResponse(result_as_dict)


app = Starlette(routes=[Route("/brands", brands)], lifespan=lifespan)
