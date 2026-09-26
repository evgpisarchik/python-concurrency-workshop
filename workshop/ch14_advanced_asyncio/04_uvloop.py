"""Listing 14.4: swap in uvloop, a faster event loop built on libuv.

Use case: more throughput for network-heavy services with no code changes
(uvicorn uses it automatically when installed). Load-test with and without it.

Run:  uv run python -m workshop.ch14_advanced_asyncio.04_uvloop
Then: echo hello | nc 127.0.0.1 9000
"""

import asyncio
from asyncio import StreamReader, StreamWriter

import uvloop


async def connected(reader: StreamReader, writer: StreamWriter):
    line = await reader.readline()
    writer.write(line)
    await writer.drain()
    writer.close()
    await writer.wait_closed()


async def main():
    print(f"Running on {type(asyncio.get_running_loop())}")
    server = await asyncio.start_server(connected, port=9000)
    await server.serve_forever()


uvloop.run(main())  # modern replacement for uvloop.install() + asyncio.run()
