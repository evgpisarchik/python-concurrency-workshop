"""Favorites and cart services: same code, different database and URL.

python -m workshop.microservices.user_lists favorites
python -m workshop.microservices.user_lists cart
"""

import sys

from aiohttp import web

from workshop.microservices import CART_PORT, FAVORITES_PORT
from workshop.microservices.db_pool import DB_KEY, with_database

SERVICES = {
    "favorites": ("user_favorite", FAVORITES_PORT),
    "cart": ("user_cart", CART_PORT),
}


def make_app(name: str) -> web.Application:
    table, _ = SERVICES[name]

    async def handler(request: web.Request) -> web.Response:
        try:
            user_id = int(request.match_info["id"])
        except ValueError:
            raise web.HTTPBadRequest() from None
        rows = await request.app[DB_KEY].fetch(f"SELECT product_id FROM {table} WHERE user_id = $1", user_id)
        return web.json_response([dict(row) for row in rows])

    app = with_database(web.Application(), name)
    app.router.add_get(f"/users/{{id}}/{name}", handler)
    return app


if __name__ == "__main__":
    service = sys.argv[1]
    web.run_app(make_app(service), port=SERVICES[service][1], print=None)
