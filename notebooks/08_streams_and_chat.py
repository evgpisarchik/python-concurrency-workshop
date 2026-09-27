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

    Both demos send a raw HTTP request to the local test server.
    """)
    return


@app.cell
async def _():
    import asyncio
    import contextlib
    from urllib.parse import urlparse

    import marimo as mo

    from workshop.testserver import start

    _url = urlparse(await start())
    host, port = _url.hostname, _url.port
    request = f"GET /delay?seconds=0.1 HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n".encode()
    return asyncio, contextlib, host, mo, port, request


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Low level: a Protocol, plus a Future bridging callbacks to `await`

    *Listings 8.1, 8.2.* asyncio calls `connection_made → data_received (N times) → eof_received → connection_lost`.
    The protocol resolves a `Future` at EOF, which lets the caller simply `await` the whole response.
    """)
    return


@app.cell
async def _(asyncio, host, port, request):
    class HttpGetProtocol(asyncio.Protocol):
        def __init__(self):
            self.response = asyncio.get_running_loop().create_future()
            self.buffer = b""

        def connection_made(self, transport):
            transport.write(request)

        def data_received(self, data):
            self.buffer += data

        def eof_received(self):
            self.response.set_result(self.buffer)

    _, _protocol = await asyncio.get_running_loop().create_connection(HttpGetProtocol, host, port)
    print((await _protocol.response).decode())
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
async def _(asyncio, host, port, request):
    _reader, _writer = await asyncio.open_connection(host, port)
    _writer.write(request)
    await _writer.drain()
    print((await _reader.read()).decode())  # read until EOF
    _writer.close()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    > Console apps: `input()` blocks the event loop the same way `requests` does. Wrap stdin in a `StreamReader`
    > (`loop.connect_read_pipe`) to read it asynchronously. That's the book's terminal-UI chapter, left out here
    > because a notebook has no terminal.

    ## A chat server: one task per client, shared state, broadcast

    *Listings 8.12, 8.13.* `asyncio.start_server(callback, host, port)` runs `callback(reader, writer)` as a new task for every
    client. The server keeps `username → writer` as shared state and **broadcasts** each message.

    * The first line a client sends is its username.
    * A client idle for longer than `idle_timeout` is disconnected (`wait_for` around `readline()`).
    * A client whose connection breaks during a broadcast is skipped, so it can't break the broadcast for the others.
    """)
    return


@app.cell
def _(asyncio, contextlib):
    class ChatServer:
        def __init__(self, idle_timeout: float):
            self.idle_timeout = idle_timeout
            self.writers: dict[str, asyncio.StreamWriter] = {}

        async def client_connected(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
            username = (await reader.readline()).decode().strip()
            self.writers[username] = writer
            await self.broadcast(f"{username} joined")
            try:
                while line := await asyncio.wait_for(reader.readline(), self.idle_timeout):
                    await self.broadcast(f"{username}: {line.decode().strip()}")
            except TimeoutError:
                await self.broadcast(f"{username} was idle too long and is disconnected")
            finally:
                del self.writers[username]
                writer.close()

        async def broadcast(self, message: str):
            for writer in list(self.writers.values()):
                with contextlib.suppress(ConnectionError):  # a dead client doesn't stop the broadcast
                    writer.write(f"{message}\n".encode())
                    await writer.drain()

    return (ChatServer,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    *Listing 8.14.* A chat client must **type and listen at the same time**, so sending runs as a separate task while the
    client reads lines. Here the "keyboard input" is a scripted list of `(pause, message)` pairs. Every client goes quiet
    at the end, so the server disconnects it after the idle timeout. Carol is away too long before her first message.
    """)
    return


@app.cell
def _(asyncio):
    class ChatClient:
        """Joins the chat, types scripted `(pause, message)` pairs and records everything it receives."""

        def __init__(self, username: str, messages: list[tuple[float, str]]):
            self.username = username
            self.messages = messages
            self.received = []

        async def chat(self, address) -> list[str]:
            reader, writer = await asyncio.open_connection(*address)
            writer.write(f"{self.username}\n".encode())
            typing = asyncio.create_task(self._type(writer))  # type while listening
            self.received = [line.decode().strip() async for line in reader]  # until the server disconnects us
            typing.cancel()
            writer.close()
            return self.received

        async def _type(self, writer: asyncio.StreamWriter):
            for pause, message in self.messages:
                await asyncio.sleep(pause)
                writer.write(f"{message}\n".encode())

    return (ChatClient,)


@app.cell
async def _(ChatClient, ChatServer, asyncio):
    _alice = ChatClient("alice", [(0.2, "hi all!"), (0.5, "how's asyncio going?")])
    _bob = ChatClient("bob", [(0.4, "hey alice"), (0.6, "great, no threads needed")])
    _carol = ChatClient("carol", [(3.0, "sorry, was away")])  # idle too long before her first message

    _chat = ChatServer(idle_timeout=1.5)
    async with await asyncio.start_server(_chat.client_connected, "127.0.0.1", 0) as _server:
        _address = _server.sockets[0].getsockname()
        await asyncio.gather(_alice.chat(_address), _bob.chat(_address), _carol.chat(_address))

    print("what alice saw:", *_alice.received, sep="\n    ")
    print("what carol saw:", *_carol.received, sep="\n    ")
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
