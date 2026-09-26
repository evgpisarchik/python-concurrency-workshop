"""Listing 7.1: an echo server with one thread per client.

Use case: add concurrency to blocking code without rewriting it. Each blocking
recv() only blocks its own thread. Downside: you can't stop it cleanly (Ctrl+C
won't stop the client threads). 02 fixes that.

Run:  uv run python -m workshop.ch07_threads_and_blocking_io.01_threaded_echo_server
Then: several  nc 127.0.0.1 8000
"""

import socket
from threading import Thread


def echo(client: socket.socket):
    while data := client.recv(2048):
        print(f"Received {data}, sending!")
        client.sendall(data)


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 8000))
    server.listen()
    while True:
        connection, _ = server.accept()  # blocks the main thread only
        thread = Thread(target=echo, args=(connection,))
        thread.start()
