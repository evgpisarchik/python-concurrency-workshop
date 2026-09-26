"""Product service: lists products from the `products` database."""

from aiohttp import web

from workshop.microservices import PRODUCT_PORT
from workshop.microservices.db_pool import DB_KEY, with_database

routes = web.RouteTableDef()


@routes.get("/products")
async def products(request: web.Request) -> web.Response:
    rows = await request.app[DB_KEY].fetch("SELECT product_id, product_name FROM product LIMIT 20")
    return web.json_response([dict(row) for row in rows])


app = with_database(web.Application(), "products")
app.add_routes(routes)

if __name__ == "__main__":
    web.run_app(app, port=PRODUCT_PORT, print=None)
