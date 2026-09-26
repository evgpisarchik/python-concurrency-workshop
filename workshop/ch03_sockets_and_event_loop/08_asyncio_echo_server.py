"""Listing 3.8: the same echo server on asyncio, one task per client.

Use case: a concurrent TCP server written like sequential code. loop.sock_accept /
sock_recv / sock_sendall are coroutines that use a selector underneath. Each
client gets its own task, and an error in one client does not affect the others.

Run:  uv run python -m workshop.ch03_sockets_and_event_loop.08_asyncio_echo_server
Then: several  nc 127.0.0.1 8000   (type "boom" to trigger an error in one client)
"""

import asyncio
import logging
import socket
from asyncio import AbstractEventLoop


async def echo(connection: socket.socket, loop: AbstractEventLoop) -> None:
    try:
        while data := await loop.sock_recv(connection, 1024):
            if data.strip() == b"boom":
                raise Exception("Unexpected network error")
            await loop.sock_sendall(connection, data)
    except Exception as ex:
        logging.exception(ex)  # only this client's task fails
    finally:
        connection.close()


async def listen_for_connection(server_socket: socket.socket, loop: AbstractEventLoop):
    while True:
        connection, address = await loop.sock_accept(server_socket)
        connection.setblocking(False)
        print(f"Got a connection from {address}")
        asyncio.create_task(echo(connection, loop))


async def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_address = ("127.0.0.1", 8000)
    server_socket.setblocking(False)
    server_socket.bind(server_address)
    server_socket.listen()

    await listen_for_connection(server_socket, asyncio.get_running_loop())


asyncio.run(main())
