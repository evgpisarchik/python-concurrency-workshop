"""Listing 3.2: read data from a client with blocking recv().

Use case: read a framed message (here, until \\r\\n) from a TCP stream. recv(2)
returns at most 2 bytes and BLOCKS the whole thread until data arrives.

Run:  uv run python -m workshop.ch03_sockets_and_event_loop.02_read_data_blocking
Then: nc -C 127.0.0.1 8000   and type a line
"""

import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_address = ("127.0.0.1", 8000)
server_socket.bind(server_address)
server_socket.listen()

try:
    connection, client_address = server_socket.accept()
    print(f"I got a connection from {client_address}!")

    buffer = b""

    while buffer[-2:] != b"\r\n":
        data = connection.recv(2)
        if not data:  # empty bytes means the client closed the connection
            break
        print(f"I got data: {data}!")
        buffer = buffer + data

    print(f"All the data is: {buffer}")
finally:
    server_socket.close()
