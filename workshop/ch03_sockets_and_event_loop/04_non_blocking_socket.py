"""Listing 3.4: switch a socket to non-blocking mode.

Use case: the first step towards an event loop. A non-blocking socket never
waits. If no data or connection is ready, it raises BlockingIOError right away.

Run: uv run python -m workshop.ch03_sockets_and_event_loop.04_non_blocking_socket
"""

import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(("127.0.0.1", 8000))
server_socket.listen()
server_socket.setblocking(False)

try:
    server_socket.accept()
except BlockingIOError as error:
    print(f"No client yet, accept() returned immediately with: {error!r}")
finally:
    server_socket.close()
