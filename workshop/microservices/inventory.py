"""Inventory service: slow and random (0-2 s), to force the BFF to handle timeouts."""

import asyncio
import random

from aiohttp import web

from workshop.microservices import INVENTORY_PORT

routes = web.RouteTableDef()


@routes.get("/products/{id}/inventory")
async def get_inventory(request: web.Request) -> web.Response:
    await asyncio.sleep(random.randint(0, 20) / 10)
    return web.json_response({"inventory": random.randint(0, 100)})


app = web.Application()
app.add_routes(routes)

if __name__ == "__main__":
    web.run_app(app, port=INVENTORY_PORT, print=None)
