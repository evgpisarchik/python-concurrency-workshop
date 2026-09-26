"""Listing 3.1: a server socket that accepts one connection.

Use case: the lowest layer of every network server. A *listening* socket
accepts connections, and each accepted client gets its own *connection* socket.

Run:  uv run python -m workshop.ch03_sockets_and_event_loop.01_accept_connection
Then: nc 127.0.0.1 8000     (or: telnet 127.0.0.1 8000)
"""

import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # IPv4 + TCP
# SO_REUSEADDR lets you restart the server right away, without "address already in use"
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_address = ("127.0.0.1", 8000)
server_socket.bind(server_address)
server_socket.listen()

connection, client_address = server_socket.accept()  # blocks until a client connects
print(f"I got a connection from {client_address}!")
server_socket.close()
