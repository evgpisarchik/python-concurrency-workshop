"""Listing 3.6: a working multi-client server that polls in a busy loop.

Use case: serve many clients from one thread by polling every socket and
ignoring BlockingIOError. It works, but look at `top`: one CPU core sits at
100% even when nobody is talking. Listing 3.7 fixes that.

Run:  uv run python -m workshop.ch03_sockets_and_event_loop.06_non_blocking_busy_loop
Then: several  nc -C 127.0.0.1 8000
"""

import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_address = ("127.0.0.1", 8000)
server_socket.bind(server_address)
server_socket.listen()
server_socket.setblocking(False)

connections = []

try:
    while True:
        try:
            connection, client_address = server_socket.accept()
            connection.setblocking(False)
            print(f"I got a connection from {client_address}!")
            connections.append(connection)
        except BlockingIOError:
            pass  # nobody is connecting right now

        for connection in connections:
            try:
                buffer = b""

                while buffer[-2:] != b"\r\n":
                    data = connection.recv(2)
                    if not data:
                        break
                    print(f"I got data: {data}!")
                    buffer = buffer + data

                print(f"All the data is: {buffer}")
                connection.send(buffer)
            except BlockingIOError:
                pass  # this client has nothing to say right now
finally:
    server_socket.close()
