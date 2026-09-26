"""Listing 8.2: use the Protocol with loop.create_connection().

Use case: the low-level transport/protocol API, which is what libraries like
aiohttp and asyncpg are built on. You rarely need it directly, but it shows how
streams work under the hood.

Run: uv run python -m workshop.ch08_streams.01_protocol_http_client
"""

import asyncio
from asyncio import AbstractEventLoop

from workshop.ch08_streams.http_client_protocol import HTTPGetClientProtocol


async def make_request(host: str, port: int, loop: AbstractEventLoop) -> str:
    def protocol_factory():
        return HTTPGetClientProtocol(host, loop)

    _, protocol = await loop.create_connection(protocol_factory, host=host, port=port)

    return await protocol.get_response()


async def main():
    loop = asyncio.get_running_loop()
    result = await make_request("www.example.com", 80, loop)
    print(result)


asyncio.run(main())
