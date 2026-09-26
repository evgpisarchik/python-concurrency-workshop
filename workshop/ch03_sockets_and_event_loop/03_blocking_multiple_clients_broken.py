"""Listing 3.3: PITFALL. Blocking sockets cannot serve two clients at once.

Use case: see why blocking I/O does not scale. Connect two clients: while the
server waits in recv() for client 1, it cannot accept() or read from client 2.

Run:  uv run python -m workshop.ch03_sockets_and_event_loop.03_blocking_multiple_clients_broken
Then: open two terminals with  nc -C 127.0.0.1 8000
"""

import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_address = ("127.0.0.1", 8000)
server_socket.bind(server_address)
server_socket.listen()

connections = []

try:
    while True:
        connection, client_address = server_socket.accept()  # blocks
        print(f"I got a connection from {client_address}!")
        connections.append(connection)

        for connection in connections:
            buffer = b""

            while buffer[-2:] != b"\r\n":
                data = connection.recv(2)  # blocks
                if not data:
                    break
                print(f"I got data: {data}!")
                buffer = buffer + data

            print(f"All the data is: {buffer}")
            connection.send(buffer)
finally:
    server_socket.close()
