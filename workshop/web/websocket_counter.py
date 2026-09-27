"""Starlette WebSocket endpoint that pushes the number of connected users to everyone.

    uv run uvicorn workshop.web.websocket_counter:app --port 8102

The `sockets` list lives in one process: with --workers N each worker would only
count its own users (sharing would need Redis pub/sub or similar).
"""

import asyncio

from starlette.applications import Starlette
from starlette.endpoints import WebSocketEndpoint
from starlette.routing import WebSocketRoute


class UserCounter(WebSocketEndpoint):
    encoding = "text"
    sockets = []

    async def on_connect(self, websocket):
        await websocket.accept()
        UserCounter.sockets.append(websocket)
        await self._send_count()

    async def on_disconnect(self, websocket, close_code):
        UserCounter.sockets.remove(websocket)
        await self._send_count()

    async def _send_count(self):
        count = str(len(UserCounter.sockets))
        # Send to every client concurrently: one slow or dead client doesn't delay the others
        await asyncio.gather(*(ws.send_text(count) for ws in UserCounter.sockets), return_exceptions=True)


app = Starlette(routes=[WebSocketRoute("/counter", UserCounter)])
