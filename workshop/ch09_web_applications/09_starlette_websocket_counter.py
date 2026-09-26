"""Listing 9.9: a WebSocket endpoint that broadcasts the online user count.

Use case: push real-time updates to browsers (counters, notifications, live
dashboards) over long-lived connections. This is something only ASGI can do.
Sends to all sockets happen concurrently, and sockets that fail are dropped.

Note: the class-level `sockets` list is per process. With --workers N each
worker only sees its own users (you'd need Redis pub/sub or similar to share).

Run:  uv run uvicorn workshop.ch09_web_applications.09_starlette_websocket_counter:app
Then: open workshop/ch09_web_applications/websocket_counter.html in several tabs (listing 9.10)
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

    async def on_receive(self, websocket, data):
        pass

    async def _send_count(self):
        if len(UserCounter.sockets) > 0:
            count_str = str(len(UserCounter.sockets))
            task_to_socket = {
                asyncio.create_task(websocket.send_text(count_str)): websocket for websocket in UserCounter.sockets
            }

            done, pending = await asyncio.wait(task_to_socket)

            for task in done:
                if task.exception() is not None:
                    if task_to_socket[task] in UserCounter.sockets:
                        UserCounter.sockets.remove(task_to_socket[task])


app = Starlette(routes=[WebSocketRoute("/counter", UserCounter)])
