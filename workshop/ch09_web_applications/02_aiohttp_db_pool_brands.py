"""Listing 9.2: an aiohttp endpoint backed by an asyncpg connection pool.

Use case: a REST endpoint that reads from Postgres. The pool's lifecycle is
tied to the app through on_startup / on_cleanup hooks.

Prereq: products DB from chapter 5
Run:    uv run python -m workshop.ch09_web_applications.02_aiohttp_db_pool_brands
Then:   curl localhost:8080/brands
"""

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from asyncpg import Record

from workshop.ch09_web_applications.aiohttp_db import DB_KEY, create_database_pool, destroy_database_pool

routes = web.RouteTableDef()


@routes.get("/brands")
async def brands(request: Request) -> Response:
    connection = request.app[DB_KEY]
    brand_query = "SELECT brand_id, brand_name FROM brand"
    results: list[Record] = await connection.fetch(brand_query)
    result_as_dict: list[dict] = [dict(brand) for brand in results]
    return web.json_response(result_as_dict)


app = web.Application()
app.on_startup.append(create_database_pool)
app.on_cleanup.append(destroy_database_pool)

app.add_routes(routes)
web.run_app(app)
