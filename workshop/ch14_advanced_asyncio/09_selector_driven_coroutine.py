"""Listing 14.10: a coroutine suspended on a socket and resumed by a selector.

Use case: connect futures with OS I/O readiness. sock_accept registers a
callback with the selector that resolves a future, and the loop at the bottom
resumes the coroutine when the selector fires.

Run:  uv run python -m workshop.ch14_advanced_asyncio.09_selector_driven_coroutine
Then: nc 127.0.0.1 8000
"""

import functools
import selectors
import socket
from selectors import BaseSelector

from workshop.ch14_advanced_asyncio.custom_future import CustomFuture


def accept_connection(future: CustomFuture, connection: socket.socket):
    print(f"We got a connection from {connection}!")
    future.set_result(connection)


async def sock_accept(sel: BaseSelector, sock) -> socket.socket:
    print("Registering socket to listen for connections")
    future = CustomFuture()
    sel.register(sock, selectors.EVENT_READ, functools.partial(accept_connection, future))
    print("Pausing to listen for connections...")
    connection: socket.socket = await future
    return connection


async def main(sel: BaseSelector):
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    sock.bind(("127.0.0.1", 8000))
    sock.listen()
    sock.setblocking(False)

    print("Waiting for socket connection!")
    connection = await sock_accept(sel, sock)
    print(f"Got a connection {connection}!")


selector = selectors.DefaultSelector()

coro = main(selector)

while True:
    try:
        state = coro.send(None)

        events = selector.select()

        for key, mask in events:
            print("Processing selector events...")
            callback = key.data
            callback(key.fileobj)
    except StopIteration:
        print("Application finished!")
        break
