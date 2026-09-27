"""Backend-for-frontend: one endpoint that calls 4 services concurrently and degrades gracefully.

* products is REQUIRED: on timeout return 504, on error return 500
* cart / favorites are OPTIONAL: on error or timeout their value is null
* inventory is fetched per product with a 1 s budget, and slow ones get null
"""

import asyncio

import aiohttp
from aiohttp import web

from workshop.microservices import BFF_PORT, CART_PORT, FAVORITES_PORT, INVENTORY_PORT, PRODUCT_PORT

routes = web.RouteTableDef()


async def get_json(session: aiohttp.ClientSession, port: int, path: str):
    async with session.get(f"http://127.0.0.1:{port}{path}") as response:
        response.raise_for_status()
        return await response.json()


def result_or_none(task: asyncio.Task, done: set):
    """The result of an optional call, or None if it failed or didn't finish in time."""
    return task.result() if task in done and task.exception() is None else None


@routes.get("/products/all")
async def all_products(request: web.Request) -> web.Response:
    async with aiohttp.ClientSession() as session:
        products = asyncio.create_task(get_json(session, PRODUCT_PORT, "/products"))
        favorites = asyncio.create_task(get_json(session, FAVORITES_PORT, "/users/3/favorites"))
        cart = asyncio.create_task(get_json(session, CART_PORT, "/users/3/cart"))
        done, pending = await asyncio.wait([products, favorites, cart], timeout=1.0)
        for task in pending:
            task.cancel()

        if products not in done:
            return web.json_response({"error": "Could not reach the products service."}, status=504)
        if products.exception() is not None:
            return web.json_response({"error": "Server error reaching the products service."}, status=500)

        return web.json_response(
            {
                "cart": result_or_none(cart, done),
                "favorites": result_or_none(favorites, done),
                "products": await with_inventory(session, products.result()),
            }
        )


async def with_inventory(session: aiohttp.ClientSession, products: list[dict]) -> list[dict]:
    tasks = {
        product["product_id"]: asyncio.create_task(
            get_json(session, INVENTORY_PORT, f"/products/{product['product_id']}/inventory")
        )
        for product in products
    }
    done, pending = await asyncio.wait(tasks.values(), timeout=1.0)
    for task in pending:
        task.cancel()
    return [{"product_id": product_id, "inventory": result_or_none(task, done)} for product_id, task in tasks.items()]


app = web.Application()
app.add_routes(routes)

if __name__ == "__main__":
    web.run_app(app, port=BFF_PORT, print=None)
