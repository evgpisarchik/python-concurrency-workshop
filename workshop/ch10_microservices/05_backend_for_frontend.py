"""Listing 10.8: backend-for-frontend (BFF) that aggregates 4 services.

Use case: one endpoint for the UI that calls several services CONCURRENTLY
and degrades gracefully:
  * products is REQUIRED: if it times out, return 504; if it errors, return 500
  * cart and favorites are OPTIONAL: on error or timeout, return null for them
  * inventory is fetched per product with a 1 s budget, and slow ones get null

Run: uv run python -m workshop.ch10_microservices.run_services     (starts 01-04)
     uv run python -m workshop.ch10_microservices.05_backend_for_frontend   (port 9000)
Then: curl localhost:9000/products/all
"""

import asyncio
import logging
from asyncio import Task

import aiohttp
from aiohttp import ClientSession, web
from aiohttp.web_request import Request
from aiohttp.web_response import Response

routes = web.RouteTableDef()

PRODUCT_BASE = "http://127.0.0.1:8000"
INVENTORY_BASE = "http://127.0.0.1:8001"
FAVORITE_BASE = "http://127.0.0.1:8002"
CART_BASE = "http://127.0.0.1:8003"


async def get_json(session: ClientSession, url: str):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.json()


@routes.get("/products/all")
async def all_products(request: Request) -> Response:
    async with aiohttp.ClientSession() as session:
        products = asyncio.create_task(get_json(session, f"{PRODUCT_BASE}/products"))
        favorites = asyncio.create_task(get_json(session, f"{FAVORITE_BASE}/users/3/favorites"))
        cart = asyncio.create_task(get_json(session, f"{CART_BASE}/users/3/cart"))

        requests = [products, favorites, cart]
        done, pending = await asyncio.wait(requests, timeout=1.0)

        if products in pending:
            [request.cancel() for request in requests]
            return web.json_response({"error": "Could not reach products service."}, status=504)
        elif products in done and products.exception() is not None:
            [request.cancel() for request in requests]
            logging.error("Server error reaching product service.", exc_info=products.exception())
            return web.json_response({"error": "Server error reaching products service."}, status=500)
        else:
            product_results = await get_products_with_inventory(session, products.result())

            cart_item_count = get_response_item_count(cart, done, "Error getting user cart.")
            favorite_item_count = get_response_item_count(favorites, done, "Error getting user favorites.")

            return web.json_response(
                {
                    "cart_items": cart_item_count,
                    "favorite_items": favorite_item_count,
                    "products": product_results,
                }
            )


async def get_products_with_inventory(session: ClientSession, product_response) -> list[dict]:
    def get_inventory(product_id: int) -> Task:
        url = f"{INVENTORY_BASE}/products/{product_id}/inventory"
        return asyncio.create_task(get_json(session, url))

    def create_product_record(product_id: int, inventory: int | None) -> dict:
        return {"product_id": product_id, "inventory": inventory}

    inventory_tasks_to_product_id = {
        get_inventory(product["product_id"]): product["product_id"] for product in product_response
    }

    inventory_done, inventory_pending = await asyncio.wait(inventory_tasks_to_product_id.keys(), timeout=1.0)

    product_results = []

    for done_task in inventory_done:
        product_id = inventory_tasks_to_product_id[done_task]
        if done_task.exception() is None:
            product_results.append(create_product_record(product_id, done_task.result()["inventory"]))
        else:
            product_results.append(create_product_record(product_id, None))
            logging.error(f"Error getting inventory for id {product_id}", exc_info=done_task.exception())

    for pending_task in inventory_pending:
        pending_task.cancel()
        product_id = inventory_tasks_to_product_id[pending_task]
        product_results.append(create_product_record(product_id, None))

    return product_results


def get_response_item_count(task: Task, done: set[Task], error_msg: str) -> int | None:
    if task in done and task.exception() is None:
        return len(task.result())
    elif task not in done:
        task.cancel()
    else:
        logging.error(error_msg, exc_info=task.exception())
    return None


app = web.Application()
app.add_routes(routes)
web.run_app(app, port=9000)
