"""Listing 10.1: the inventory service, which is deliberately slow and random.

Use case: simulate an unreliable dependency. It answers after 0 to 2 s, so
the backend-for-frontend has to handle timeouts.

Run:  uv run python -m workshop.ch10_microservices.01_inventory_service   (port 8001)
Then: curl localhost:8001/products/1/inventory
"""

import asyncio
import random

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response

routes = web.RouteTableDef()


@routes.get("/products/{id}/inventory")
async def get_inventory(request: Request) -> Response:
    delay: float = random.randint(0, 20) / 10
    await asyncio.sleep(delay)
    inventory: int = random.randint(0, 100)
    return web.json_response({"inventory": inventory})


app = web.Application()
app.add_routes(routes)
web.run_app(app, port=8001)
