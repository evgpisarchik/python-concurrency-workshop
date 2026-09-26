"""Listing 8.14: the chat client.

Use case: a client that listens and sends at the same time. Two tasks run
concurrently: one prints messages from the server, and one sends what you type.
asyncio.wait(FIRST_COMPLETED) exits when either side finishes.

Run: uv run python -m workshop.ch08_streams.09_chat_client   (start 08_chat_server first)
"""

import asyncio
import logging
import os
import sys
import tty
from asyncio import StreamReader, StreamWriter

from workshop.ch08_streams.terminal import (
    MessageStore,
    create_stdin_reader,
    make_redraw,
    move_to_bottom_of_screen,
    read_line,
)


async def send_message(message: str, writer: StreamWriter):
    writer.write((message + "\n").encode())
    await writer.drain()


async def listen_for_messages(reader: StreamReader, message_store: MessageStore):
    while (message := await reader.readline()) != b"":
        await message_store.append(message.decode())
    await message_store.append("Server closed connection.")


async def read_and_send(stdin_reader: StreamReader, writer: StreamWriter):
    while True:
        message = await read_line(stdin_reader)
        await send_message(message, writer)


async def main():
    tty.setcbreak(sys.stdin)
    os.system("clear")
    rows = move_to_bottom_of_screen()

    messages = MessageStore(make_redraw(sys.stdout.write), rows - 1)

    stdin_reader = await create_stdin_reader()
    sys.stdout.write("Enter username: ")
    sys.stdout.flush()
    username = await read_line(stdin_reader)

    reader, writer = await asyncio.open_connection("127.0.0.1", 8000)

    writer.write(f"CONNECT {username}\n".encode())
    await writer.drain()

    message_listener = asyncio.create_task(listen_for_messages(reader, messages))
    input_listener = asyncio.create_task(read_and_send(stdin_reader, writer))

    try:
        await asyncio.wait([message_listener, input_listener], return_when=asyncio.FIRST_COMPLETED)
    except Exception as e:
        logging.exception(e)
    finally:
        writer.close()
        await writer.wait_closed()


asyncio.run(main())
