"""Listing 10.6: the cart service, backed by its own `cart` database.

Use case: a small service with its own database (database-per-service pattern).
The tables are created by docker/initdb/01_databases.sql.

Run:  uv run python -m workshop.ch10_microservices.03_cart_service   (port 8003)
Then: curl localhost:8003/users/1/cart
"""

import functools

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response

from workshop.ch10_microservices.db_pool import DB_KEY, create_database_pool, destroy_database_pool

routes = web.RouteTableDef()


@routes.get("/users/{id}/cart")
async def cart(request: Request) -> Response:
    try:
        user_id = int(request.match_info["id"])
        db = request.app[DB_KEY]
        query = "SELECT product_id FROM user_cart WHERE user_id = $1"
        result = await db.fetch(query, user_id)
        return web.json_response([dict(record) for record in result])
    except ValueError:
        raise web.HTTPBadRequest() from None


app = web.Application()
app.on_startup.append(functools.partial(create_database_pool, database="cart"))
app.on_cleanup.append(destroy_database_pool)

app.add_routes(routes)
web.run_app(app, port=8003)
