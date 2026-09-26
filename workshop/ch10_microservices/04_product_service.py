"""Listing 10.7: the product service, which lists products from the `products` DB.

Run:  uv run python -m workshop.ch10_microservices.04_product_service   (port 8000)
Then: curl localhost:8000/products
"""

import functools

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response

from workshop.ch10_microservices.db_pool import DB_KEY, create_database_pool, destroy_database_pool

routes = web.RouteTableDef()


@routes.get("/products")
async def products(request: Request) -> Response:
    db = request.app[DB_KEY]
    product_query = "SELECT product_id, product_name FROM product LIMIT 50"
    result = await db.fetch(product_query)
    return web.json_response([dict(record) for record in result])


app = web.Application()
app.on_startup.append(functools.partial(create_database_pool, database="products"))
app.on_cleanup.append(destroy_database_pool)

app.add_routes(routes)
web.run_app(app, port=8000)
