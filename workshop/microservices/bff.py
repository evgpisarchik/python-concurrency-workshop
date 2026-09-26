"""Backend-for-frontend: one endpoint that calls 4 services concurrently and degrades gracefully.

* products is REQUIRED: on timeout return 504, on error return 500
* cart / favorites are OPTIONAL: on error or timeout their value is null
* inventory is fetched per product with a 1 s budget, and slow ones get null
"""

import asyncio
import logging
from asyncio import Task

import aiohttp
from aiohttp import ClientSession, web

from workshop.microservices import BFF_PORT, CART_PORT, FAVORITES_PORT, INVENTORY_PORT, PRODUCT_PORT

routes = web.RouteTableDef()

PRODUCT_BASE = f"http://127.0.0.1:{PRODUCT_PORT}"
INVENTORY_BASE = f"http://127.0.0.1:{INVENTORY_PORT}"
FAVORITE_BASE = f"http://127.0.0.1:{FAVORITES_PORT}"
CART_BASE = f"http://127.0.0.1:{CART_PORT}"


async def get_json(session: ClientSession, url: str):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.json()


@routes.get("/products/all")
async def all_products(request: web.Request) -> web.Response:
    async with aiohttp.ClientSession() as session:
        products = asyncio.create_task(get_json(session, f"{PRODUCT_BASE}/products"))
        favorites = asyncio.create_task(get_json(session, f"{FAVORITE_BASE}/users/3/favorites"))
        cart = asyncio.create_task(get_json(session, f"{CART_BASE}/users/3/cart"))

        requests = [products, favorites, cart]
        done, pending = await asyncio.wait(requests, timeout=1.0)

        if products in pending:
            [r.cancel() for r in requests]
            return web.json_response({"error": "Could not reach products service."}, status=504)
        if products.exception() is not None:
            [r.cancel() for r in requests]
            logging.error("Server error reaching product service.", exc_info=products.exception())
            return web.json_response({"error": "Server error reaching products service."}, status=500)

        product_results = await get_products_with_inventory(session, products.result())
        return web.json_response(
            {
                "cart_items": item_count(cart, done, "Error getting user cart."),
                "favorite_items": item_count(favorites, done, "Error getting user favorites."),
                "products": product_results,
            }
        )


async def get_products_with_inventory(session: ClientSession, product_response) -> list[dict]:
    tasks_to_id = {
        asyncio.create_task(get_json(session, f"{INVENTORY_BASE}/products/{p['product_id']}/inventory")): p[
            "product_id"
        ]
        for p in product_response
    }
    done, pending = await asyncio.wait(tasks_to_id, timeout=1.0)

    results = []
    for task in done:
        inventory = task.result()["inventory"] if task.exception() is None else None
        results.append({"product_id": tasks_to_id[task], "inventory": inventory})
    for task in pending:
        task.cancel()
        results.append({"product_id": tasks_to_id[task], "inventory": None})
    return results


def item_count(task: Task, done: set[Task], error_msg: str) -> int | None:
    if task in done and task.exception() is None:
        return len(task.result())
    if task not in done:
        task.cancel()
    else:
        logging.error(error_msg, exc_info=task.exception())
    return None


app = web.Application()
app.add_routes(routes)

if __name__ == "__main__":
    web.run_app(app, port=BFF_PORT, print=None)
