"""Listing 14.13: a multi-client server running on OUR OWN event loop.

Use case: the final exercise. The async/await code looks just like the
asyncio version from chapter 3, but every piece underneath (futures, tasks,
selector loop) is code you can read in this folder.

Run:  uv run python -m workshop.ch14_advanced_asyncio.10_custom_event_loop_server
Then: several  nc 127.0.0.1 8000
"""

import socket

from workshop.ch14_advanced_asyncio.custom_event_loop import EventLoop
from workshop.ch14_advanced_asyncio.custom_task import CustomTask


async def read_from_client(conn, loop: EventLoop):
    print(f"Reading data from client {conn}")
    try:
        while data := await loop.sock_recv(conn):
            print(f"Got {data} from client!")
    finally:
        loop.sock_close(conn)


async def listen_for_connections(sock, loop: EventLoop):
    while True:
        print("Waiting for connection...")
        conn, addr = await loop.sock_accept(sock)
        CustomTask(read_from_client(conn, loop), loop)
        print(f"I got a new connection from {addr}!")


async def main(loop: EventLoop):
    server_socket = socket.socket()
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind(("127.0.0.1", 8000))
    server_socket.listen()
    server_socket.setblocking(False)

    await listen_for_connections(server_socket, loop)


event_loop = EventLoop()
event_loop.run(main(event_loop))
