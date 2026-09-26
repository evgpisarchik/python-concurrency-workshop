"""Listing 9.3: path parameters and proper HTTP errors.

Use case: GET /products/{id}. Validate input (400), handle missing rows (404),
and use a parameterized query.

Run:  uv run python -m workshop.ch09_web_applications.03_aiohttp_get_product
Then: curl -i localhost:8080/products/10 ; curl -i localhost:8080/products/abc
"""

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from asyncpg import Record

from workshop.ch09_web_applications.aiohttp_db import DB_KEY, create_database_pool, destroy_database_pool

routes = web.RouteTableDef()


@routes.get("/products/{id}")
async def get_product(request: Request) -> Response:
    try:
        str_id = request.match_info["id"]
        product_id = int(str_id)

        query = """
            SELECT product_id, product_name, brand_id
            FROM product
            WHERE product_id = $1
            """

        connection = request.app[DB_KEY]
        result: Record | None = await connection.fetchrow(query, product_id)

        if result is not None:
            return web.json_response(dict(result))
        raise web.HTTPNotFound()
    except ValueError:
        raise web.HTTPBadRequest() from None


app = web.Application()
app.on_startup.append(create_database_pool)
app.on_cleanup.append(destroy_database_pool)

app.add_routes(routes)
web.run_app(app)
