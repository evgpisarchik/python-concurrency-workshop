"""Listing 3.7: an echo server built on selectors (epoll/kqueue).

Use case: the core idea of an event loop. Ask the OS "tell me which sockets
are ready" and sleep until one is, instead of busy-polling. CPU use drops to
~0% while idle. asyncio's event loop is built on exactly this.

Run:  uv run python -m workshop.ch03_sockets_and_event_loop.07_selector_echo_server
Then: several  nc 127.0.0.1 8000
"""

import selectors
import socket
from selectors import SelectorKey

selector = selectors.DefaultSelector()

server_socket = socket.socket()
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_address = ("127.0.0.1", 8000)
server_socket.setblocking(False)
server_socket.bind(server_address)
server_socket.listen()

selector.register(server_socket, selectors.EVENT_READ)

while True:
    # sleep until at least one socket is ready, or 1 s passes
    events: list[tuple[SelectorKey, int]] = selector.select(timeout=1)

    if len(events) == 0:
        print("No events, waiting a bit more!")

    for event, _ in events:
        event_socket = event.fileobj

        if event_socket == server_socket:  # the listening socket is readable: a new client
            connection, address = server_socket.accept()
            connection.setblocking(False)
            print(f"I got a connection from {address}")
            selector.register(connection, selectors.EVENT_READ)
        else:  # a client socket is readable: data (or disconnect)
            data = event_socket.recv(1024)
            if not data:
                print("Client disconnected")
                selector.unregister(event_socket)
                event_socket.close()
                continue
            print(f"I got some data: {data}")
            event_socket.send(data)
