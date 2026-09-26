"""Listing 8.3: the same HTTP request with high-level streams.

Use case: talk any line- or byte-based TCP protocol (HTTP, Redis, SMTP, custom)
with asyncio.open_connection(), which returns a (StreamReader, StreamWriter) pair.
write() buffers data, and `await drain()` applies back-pressure.

Run: uv run python -m workshop.ch08_streams.02_stream_reader_http_client
"""

import asyncio
from asyncio import StreamReader
from collections.abc import AsyncGenerator


async def read_until_empty(stream_reader: StreamReader) -> AsyncGenerator[str, None]:
    while response := await stream_reader.readline():
        yield response.decode()


async def main():
    host: str = "www.example.com"
    request: str = f"GET / HTTP/1.1\r\nConnection: close\r\nHost: {host}\r\n\r\n"

    stream_reader, stream_writer = await asyncio.open_connection(host, 80)

    try:
        stream_writer.write(request.encode())
        await stream_writer.drain()

        responses = [response async for response in read_until_empty(stream_reader)]

        print("".join(responses))
    finally:
        stream_writer.close()
        await stream_writer.wait_closed()


asyncio.run(main())
