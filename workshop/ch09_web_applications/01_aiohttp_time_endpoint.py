"""Listing 9.1: a minimal aiohttp web server.

Use case: an async HTTP API. Every handler is a coroutine, so one process can
serve thousands of concurrent requests that are waiting on I/O. Try swapping
the asyncio.sleep for time.sleep and load-test both (see locust/).

Run:  uv run python -m workshop.ch09_web_applications.01_aiohttp_time_endpoint
Then: curl localhost:8080/time
"""

import asyncio
from datetime import datetime

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response

routes = web.RouteTableDef()


@routes.get("/time")
async def time(request: Request) -> Response:
    await asyncio.sleep(0.1)  # pretend we're calling a slow dependency; time.sleep() would block everyone
    today = datetime.today()

    result = {
        "month": today.month,
        "day": today.day,
        "time": str(today.time()),
    }

    return web.json_response(result)


app = web.Application()
app.add_routes(routes)
web.run_app(app)
