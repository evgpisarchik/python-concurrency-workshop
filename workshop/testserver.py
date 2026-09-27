"""A local HTTP server for the notebooks, so demos don't depend on the internet.

Endpoints:
    GET /delay?seconds=0.5   answer {"slept": 0.5} after that delay (a stand-in for a slow API)
    GET /page/{n}            HTML page linking to 3 child pages (a small site to crawl)

In an async notebook cell:
    base_url = await start()          # runs for the rest of the notebook
As a separate process (for demos that use blocking clients):
    python -m workshop.testserver --port 8111
"""

import argparse
import asyncio

from aiohttp import web

MAX_PAGES = 40


async def delay(request: web.Request) -> web.Response:
    seconds = float(request.query.get("seconds", 0))
    await asyncio.sleep(seconds)
    return web.json_response({"slept": seconds})


async def page(request: web.Request) -> web.Response:
    n = int(request.match_info["n"])
    children = [child for child in (3 * n + 1, 3 * n + 2, 3 * n + 3) if child < MAX_PAGES]
    links = " ".join(f'<a href="/page/{child}">page {child}</a>' for child in children)
    await asyncio.sleep(0.05)
    return web.Response(text=f"<html><body><h1>Page {n}</h1>{links}</body></html>", content_type="text/html")


def make_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/delay", delay)
    app.router.add_get("/page/{n}", page)
    return app


async def start(port: int = 0) -> str:
    """Start the test server on the running event loop and return its base URL. It runs until the loop stops."""
    runner = web.AppRunner(make_app(), access_log=None)
    await runner.setup()
    await web.TCPSite(runner, "127.0.0.1", port).start()
    return f"http://127.0.0.1:{runner.addresses[0][1]}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8111)
    web.run_app(make_app(), host="127.0.0.1", port=parser.parse_args().port, print=None, access_log=None)
