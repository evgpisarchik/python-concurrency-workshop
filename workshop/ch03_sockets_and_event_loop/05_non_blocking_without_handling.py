"""Listing 3.5: PITFALL. Non-blocking sockets without handling BlockingIOError.

Use case: see that non-blocking calls fail when nothing is ready. This
server crashes right away with BlockingIOError because no client has connected yet.

Run: uv run python -m workshop.ch03_sockets_and_event_loop.05_non_blocking_without_handling
"""

import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_address = ("127.0.0.1", 8000)
server_socket.bind(server_address)
server_socket.listen()
server_socket.setblocking(False)  # accept() will no longer wait

connections = []

try:
    while True:
        connection, client_address = server_socket.accept()  # raises BlockingIOError
        connection.setblocking(False)
        print(f"I got a connection from {client_address}!")
        connections.append(connection)

        for connection in connections:
            buffer = b""

            while buffer[-2:] != b"\r\n":
                data = connection.recv(2)
                if not data:
                    break
                print(f"I got data: {data}!")
                buffer = buffer + data

            print(f"All the data is: {buffer}")
            connection.send(buffer)
finally:
    server_socket.close()
