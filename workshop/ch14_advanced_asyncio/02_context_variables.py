"""Listing 14.2: contextvars give per-task "thread-local" state.

Use case: request-scoped data (request id, user, trace id, DB transaction)
visible anywhere in the call chain without passing it as an argument. Each
task gets a copy of the context at the moment it is created.

Run:  uv run python -m workshop.ch14_advanced_asyncio.02_context_variables
Then: in two terminals:  nc 127.0.0.1 9000   and type messages
"""

import asyncio
from asyncio import StreamReader, StreamWriter
from contextvars import ContextVar


class Server:
    user_address = ContextVar("user_address")

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    async def start_server(self):
        server = await asyncio.start_server(self._client_connected, self.host, self.port)
        await server.serve_forever()

    def _client_connected(self, reader: StreamReader, writer: StreamWriter):
        self.user_address.set(writer.get_extra_info("peername"))
        asyncio.create_task(self.listen_for_messages(reader))  # the task copies the current context

    async def listen_for_messages(self, reader: StreamReader):
        while data := await reader.readline():
            print(f"Got message {data} from {self.user_address.get()}")


async def main():
    server = Server("127.0.0.1", 9000)
    await server.start_server()


asyncio.run(main())
