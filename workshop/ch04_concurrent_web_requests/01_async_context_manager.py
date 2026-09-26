"""Listing 4.1: write an asynchronous context manager (__aenter__/__aexit__).

Use case: acquire and release resources that need I/O (connections, sessions,
locks, transactions) with `async with`. aiohttp's ClientSession, asyncpg
transactions and pools all work this way.

Run:  uv run python -m workshop.ch04_concurrent_web_requests.01_async_context_manager
Then: echo hello | nc 127.0.0.1 8000
"""

import asyncio
import socket
from types import TracebackType


class ConnectedSocket:
    def __init__(self, server_socket: socket.socket):
        self._connection: socket.socket | None = None
        self._server_socket = server_socket

    async def __aenter__(self) -> socket.socket:
        print("Entering context manager, waiting for connection")
        loop = asyncio.get_running_loop()
        connection, _address = await loop.sock_accept(self._server_socket)
        self._connection = connection
        print("Accepted a connection")
        return self._connection

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ):
        print("Exiting context manager")
        self._connection.close()
        print("Closed connection")


async def main():
    loop = asyncio.get_running_loop()

    server_socket = socket.socket()
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.setblocking(False)
    server_socket.bind(("127.0.0.1", 8000))
    server_socket.listen()

    async with ConnectedSocket(server_socket) as connection:
        data = await loop.sock_recv(connection, 1024)
        print(data)


asyncio.run(main())
