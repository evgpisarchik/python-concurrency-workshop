"""A local HTTP server for the notebooks, so demos don't depend on the internet.

Endpoints:
    GET  /delay?seconds=0.5   answer after a delay (a stand-in for a slow API)
    GET  /status/{code}       answer with that HTTP status
    GET  /page/{n}            HTML page linking to 3 child pages (a small site to crawl)
    GET  /stats               {"in_flight", "max_in_flight", "total"}: see how much concurrency arrived
    POST /stats/reset

In an async notebook cell:
    async with serve() as base_url: ...
As a separate process (for demos that use blocking clients from threads):
    python -m workshop.testserver --port 8111
"""

import argparse
import asyncio
from contextlib import asynccontextmanager

from aiohttp import web

MAX_PAGES = 40


def make_app() -> web.Application:
    stats = {"in_flight": 0, "max_in_flight": 0, "total": 0}

    @web.middleware
    async def track(request, handler):
        if request.path.startswith("/stats"):
            return await handler(request)
        stats["in_flight"] += 1
        stats["total"] += 1
        stats["max_in_flight"] = max(stats["max_in_flight"], stats["in_flight"])
        try:
            return await handler(request)
        finally:
            stats["in_flight"] -= 1

    async def delay(request):
        seconds = float(request.query.get("seconds", 0))
        await asyncio.sleep(seconds)
        return web.json_response({"slept": seconds})

    async def status(request):
        code = int(request.match_info["code"])
        return web.json_response({"status": code}, status=code)

    async def page(request):
        n = int(request.match_info["n"])
        children = [c for c in (3 * n + 1, 3 * n + 2, 3 * n + 3) if c < MAX_PAGES]
        links = "".join(f'<a href="/page/{c}">page {c}</a> ' for c in children)
        await asyncio.sleep(0.05)
        return web.Response(text=f"<html><body><h1>Page {n}</h1>{links}</body></html>", content_type="text/html")

    async def get_stats(request):
        return web.json_response(stats)

    async def reset_stats(request):
        stats.update(in_flight=0, max_in_flight=0, total=0)
        return web.json_response(stats)

    app = web.Application(middlewares=[track])
    app.router.add_get("/delay", delay)
    app.router.add_get("/status/{code}", status)
    app.router.add_get("/page/{n}", page)
    app.router.add_get("/stats", get_stats)
    app.router.add_post("/stats/reset", reset_stats)
    return app


@asynccontextmanager
async def serve(port: int = 0):
    """Run the test server on the current event loop; yields its base URL."""
    runner = web.AppRunner(make_app(), access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", port)
    await site.start()
    actual_port = runner.addresses[0][1]
    try:
        yield f"http://127.0.0.1:{actual_port}"
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8111)
    web.run_app(make_app(), host="127.0.0.1", port=parser.parse_args().port, print=None, access_log=None)
