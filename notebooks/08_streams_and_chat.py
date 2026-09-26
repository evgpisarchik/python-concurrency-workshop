import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium", app_title="8 · Streams and a chat server")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 8 · Streams, protocols, and a concurrent chat server

    asyncio offers two networking layers:

    * **transports & protocols**: callback-based. asyncio calls your methods as bytes arrive. This is what libraries are built on.
    * **streams** (`StreamReader` / `StreamWriter`): the high-level, awaitable API you should normally use.
    """)
    return


@app.cell
def _():
    import asyncio
    import logging
    from urllib.parse import urlparse

    import marimo as mo

    from workshop.testserver import serve

    return asyncio, logging, mo, serve, urlparse


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Low level: a Protocol, plus a Future bridging callbacks to `await`

    *Listings 8.1, 8.2.* asyncio calls `connection_made → data_received (N times) → eof_received → connection_lost`.
    The protocol resolves a `Future` at EOF, which lets the caller simply `await` the whole response.
    """)
    return


@app.cell
async def _(asyncio, serve, urlparse):
    class HTTPGetClientProtocol(asyncio.Protocol):
        def __init__(self, host: str, path: str, loop: asyncio.AbstractEventLoop):
            self._request = f"GET {path} HTTP/1.1\r\nConnection: close\r\nHost: {host}\r\n\r\n".encode()
            self._future = loop.create_future()
            self._buffer = b""
            self.chunks = 0

        async def get_response(self) -> str:
            return await self._future

        def connection_made(self, transport):
            transport.write(self._request)

        def data_received(self, data):
            self.chunks += 1
            self._buffer += data

        def eof_received(self):
            self._future.set_result(self._buffer.decode())

        def connection_lost(self, exc):
            if exc is not None and not self._future.done():
                self._future.set_exception(exc)

    async with serve() as _base:
        _url = urlparse(_base)
        _loop = asyncio.get_running_loop()
        _, _protocol = await _loop.create_connection(
            lambda: HTTPGetClientProtocol(_url.hostname, "/delay?seconds=0.1", _loop), _url.hostname, _url.port
        )
        _response = await _protocol.get_response()
        print(f"{_protocol.chunks} data_received call(s); status line: {_response.splitlines()[0]}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## High level: streams

    *Listing 8.3.* `asyncio.open_connection()` returns a `(reader, writer)` pair. `writer.write()` only **buffers** data.
    `await writer.drain()` waits until the buffer is flushed, which is the stream's **back-pressure**. Without it, a fast
    producer can fill memory when the peer reads slowly.
    """)
    return


@app.cell
async def _(asyncio, serve, urlparse):
    async with serve() as _base:
        _url = urlparse(_base)
        _reader, _writer = await asyncio.open_connection(_url.hostname, _url.port)
        _writer.write(f"GET /delay?seconds=0.1 HTTP/1.1\r\nConnection: close\r\nHost: {_url.hostname}\r\n\r\n".encode())
        await _writer.drain()
        _lines = [_line.decode().rstrip() async for _line in _reader]  # a StreamReader is async-iterable by line
        _writer.close()
        await _writer.wait_closed()
        print("\n".join(_lines))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    > Console apps: `input()` blocks the event loop the same way `requests` does. Wrap stdin in a `StreamReader`
    > (`loop.connect_read_pipe`) to read it asynchronously. That's the book's terminal-UI chapter, left out here
    > because a notebook has no terminal.

    ## A chat server: one task per client, shared state, broadcast

    *Listings 8.12, 8.13.* `asyncio.start_server(callback, host, port)` calls `callback(reader, writer)` for every client.
    The server keeps `username → writer` as shared state and **broadcasts** each message.

    * The first line must be `CONNECT <username>`.
    * A client idle for longer than `idle_timeout` is disconnected (`wait_for` around `readline()`).
    * A client whose connection fails during a broadcast is removed. It doesn't break the broadcast for the others.
    """)
    return


@app.cell
def _(asyncio, logging):
    class ChatServer:
        def __init__(self, idle_timeout: float):
            self._username_to_writer: dict[str, asyncio.StreamWriter] = {}
            self.idle_timeout = idle_timeout

        async def client_connected(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
            command, _, username = (await reader.readline()).decode().strip().partition(" ")
            if command != "CONNECT" or not username:
                writer.close()
                return
            self._username_to_writer[username] = writer
            writer.write(f"Welcome! {len(self._username_to_writer)} user(s) online\n".encode())
            await writer.drain()
            await self._notify_all(f"{username} connected!\n")
            asyncio.create_task(self._listen_for_messages(username, reader))

        async def _listen_for_messages(self, username: str, reader: asyncio.StreamReader):
            try:
                while data := await asyncio.wait_for(reader.readline(), self.idle_timeout):
                    await self._notify_all(f"{username}: {data.decode()}")
                await self._notify_all(f"{username} has left the chat\n")
            except TimeoutError:
                await self._notify_all(f"{username} was idle too long, disconnecting\n")
            finally:
                await self._remove_user(username)

        async def _remove_user(self, username: str):
            writer = self._username_to_writer.pop(username, None)
            if writer is not None:
                writer.close()

        async def _notify_all(self, message: str):
            inactive = []
            for username, writer in list(self._username_to_writer.items()):
                try:
                    writer.write(message.encode())
                    await writer.drain()
                except ConnectionError:
                    logging.exception("could not write to %s", username)
                    inactive.append(username)
            for username in inactive:
                await self._remove_user(username)

    return (ChatServer,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *Listing 8.14.* A chat client must **listen and send at the same time**, so it runs two tasks and stops when either
    one finishes (`wait(..., FIRST_COMPLETED)`). Here the "keyboard input" is a scripted list of timed messages.
    """)
    return


@app.cell
def _(asyncio):
    async def chat_client(port: int, username: str, script: list[tuple[float, str]], transcript: dict):
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write(f"CONNECT {username}\n".encode())
        await writer.drain()
        received = transcript.setdefault(username, [])

        async def listen():
            while line := await reader.readline():
                received.append(line.decode().rstrip())

        async def send():
            for pause, message in script:
                await asyncio.sleep(pause)
                writer.write(f"{message}\n".encode())
                await writer.drain()
            writer.write_eof()  # done typing: leave the chat

        listener, sender = asyncio.create_task(listen()), asyncio.create_task(send())
        await asyncio.wait([listener, sender], return_when=asyncio.FIRST_COMPLETED)
        await asyncio.wait_for(listener, 3)  # let the last messages arrive
        writer.close()

    return (chat_client,)


@app.cell
async def _(ChatServer, asyncio, chat_client):
    _chat = ChatServer(idle_timeout=1.5)
    _server = await asyncio.start_server(_chat.client_connected, "127.0.0.1", 8801)
    _transcript = {}
    async with _server:
        await asyncio.gather(
            chat_client(8801, "alice", [(0.2, "hi all!"), (0.5, "how's asyncio going?")], _transcript),
            chat_client(8801, "bob", [(0.4, "hey alice"), (0.6, "great, no threads needed")], _transcript),
            chat_client(8801, "carol", [(3.0, "sorry, was away")], _transcript),  # idle > 1.5 s: gets kicked
        )
    for _user, _lines in _transcript.items():
        print(f"--- what {_user} saw")
        print("\n".join(f"    {_l}" for _l in _lines))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Takeaways

    * Prefer streams. Protocols plus Futures show how awaitables are built on top of callbacks.
    * `write()` buffers, and `await drain()` applies back-pressure.
    * A concurrent server is one task per client plus shared state. Handle idle and dead clients so one bad
      connection can't affect the others.
    """)
    return


if __name__ == "__main__":
    app.run()
