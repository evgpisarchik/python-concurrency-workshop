"""Listing 8.13: a chat server.

Use case: a real-time broadcast server. The protocol is:
  * the first line must be  CONNECT <username>
  * every later line is broadcast as  <username>: <message>
  * a user idle for 60 s is disconnected (wait_for on readline)

Run:  uv run python -m workshop.ch08_streams.08_chat_server
Then: uv run python -m workshop.ch08_streams.09_chat_client   (in 2+ terminals)
      or:  nc 127.0.0.1 8000  and type  CONNECT alice
"""

import asyncio
import logging
from asyncio import StreamReader, StreamWriter


class ChatServer:
    def __init__(self):
        self._username_to_writer: dict[str, StreamWriter] = {}

    async def start_chat_server(self, host: str, port: int):
        server = await asyncio.start_server(self.client_connected, host, port)

        async with server:
            await server.serve_forever()

    async def client_connected(self, reader: StreamReader, writer: StreamWriter):
        command = await reader.readline()
        print(f"CONNECTED {writer.get_extra_info('peername')}")
        command, _, args = command.partition(b" ")
        if command == b"CONNECT" and args.strip():
            username = args.strip().decode()
            self._add_user(username, reader, writer)
            await self._on_connect(username, writer)
        else:
            logging.error("Got invalid command from client, disconnecting.")
            writer.close()
            await writer.wait_closed()

    def _add_user(self, username: str, reader: StreamReader, writer: StreamWriter):
        self._username_to_writer[username] = writer
        asyncio.create_task(self._listen_for_messages(username, reader))

    async def _on_connect(self, username: str, writer: StreamWriter):
        writer.write(f"Welcome! {len(self._username_to_writer)} user(s) are online!\n".encode())
        await writer.drain()
        await self._notify_all(f"{username} connected!\n")

    async def _remove_user(self, username: str):
        writer = self._username_to_writer.pop(username, None)
        if writer is None:
            return
        try:
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            logging.exception("Error closing client writer, ignoring.", exc_info=e)

    async def _listen_for_messages(self, username: str, reader: StreamReader):
        try:
            while (data := await asyncio.wait_for(reader.readline(), 60)) != b"":
                await self._notify_all(f"{username}: {data.decode()}")
            await self._notify_all(f"{username} has left the chat\n")
        except Exception as e:
            logging.exception("Error reading from client.", exc_info=e)
        finally:
            await self._remove_user(username)

    async def _notify_all(self, message: str):
        inactive_users = []
        for username, writer in self._username_to_writer.items():
            try:
                writer.write(message.encode())
                await writer.drain()
            except ConnectionError as e:
                logging.exception("Could not write to client.", exc_info=e)
                inactive_users.append(username)

        for username in inactive_users:
            await self._remove_user(username)


async def main():
    chat_server = ChatServer()
    await chat_server.start_chat_server("127.0.0.1", 8000)


asyncio.run(main())
