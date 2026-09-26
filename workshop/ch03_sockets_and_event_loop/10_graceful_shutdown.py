"""Listing 3.10: graceful shutdown for the echo server.

Use case: on SIGINT/SIGTERM (for example, a deployment), stop accepting new
clients but give the connected ones up to 2 seconds to finish.

Run:  uv run python -m workshop.ch03_sockets_and_event_loop.10_graceful_shutdown
Then: connect with nc 127.0.0.1 8000, press Ctrl+C in the server terminal
"""

import asyncio
import logging
import signal
import socket
from asyncio import AbstractEventLoop


async def echo(connection: socket.socket, loop: AbstractEventLoop) -> None:
    try:
        while data := await loop.sock_recv(connection, 1024):
            print("got data!")
            if data == b"boom\n":
                raise Exception("Unexpected network error")
            await loop.sock_sendall(connection, data)
    except Exception as ex:
        logging.exception(ex)
    finally:
        connection.close()


echo_tasks: list[asyncio.Task] = []


async def connection_listener(server_socket: socket.socket, loop: AbstractEventLoop):
    while True:
        connection, address = await loop.sock_accept(server_socket)
        connection.setblocking(False)
        print(f"Got a connection from {address}")
        echo_tasks.append(asyncio.create_task(echo(connection, loop)))


class GracefulExit(SystemExit):
    pass


def shutdown():
    raise GracefulExit()


async def close_echo_tasks(tasks: list[asyncio.Task]):
    waiters = [asyncio.wait_for(task, 2) for task in tasks]
    print(f"Giving {len(waiters)} client(s) 2 seconds to finish...")
    for waiter in waiters:
        try:
            await waiter
        except TimeoutError:
            pass  # expected: the client was still connected


async def main():
    loop = asyncio.get_running_loop()
    server_socket = socket.socket()
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_address = ("127.0.0.1", 8000)
    server_socket.setblocking(False)
    server_socket.bind(server_address)
    server_socket.listen()

    for signame in ("SIGINT", "SIGTERM"):
        loop.add_signal_handler(getattr(signal, signame), shutdown)
    await connection_listener(server_socket, loop)


loop = asyncio.new_event_loop()

try:
    loop.run_until_complete(main())
except GracefulExit:
    loop.run_until_complete(close_echo_tasks(echo_tasks))
finally:
    loop.close()
