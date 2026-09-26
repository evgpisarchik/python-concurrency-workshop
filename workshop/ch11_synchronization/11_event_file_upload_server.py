"""Listing 11.12: a file upload server built on FileUpload + Event.

Use case: separate "receive the data" from "process the data". The processor
simply awaits the upload's completion event.

Run:  uv run python -m workshop.ch11_synchronization.11_event_file_upload_server
Then: nc -N 127.0.0.1 9000 < README.md
"""

import asyncio
from asyncio import StreamReader, StreamWriter

from workshop.ch11_synchronization.file_upload import FileUpload


class FileServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    async def start_server(self):
        server = await asyncio.start_server(self._client_connected, self.host, self.port)
        await server.serve_forever()

    async def dump_contents_on_complete(self, upload: FileUpload):
        file_contents = await upload.get_contents()
        print(file_contents)

    def _client_connected(self, reader: StreamReader, writer: StreamWriter):
        upload = FileUpload(reader, writer)
        upload.listen_for_uploads()
        asyncio.create_task(self.dump_contents_on_complete(upload))


async def main():
    server = FileServer("127.0.0.1", 9000)
    await server.start_server()


asyncio.run(main())
