import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium", app_title="3 · Sockets and the event loop")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 3 · From blocking sockets to an event loop

    This notebook builds, step by step, the machinery that asyncio uses underneath:
    **blocking sockets → non-blocking sockets → a busy loop → `selectors` → asyncio**.
    Every server runs inside its demo cell on a free port (port 0 = "OS, pick one"), and the notebook plays the clients.
    """)
    return


@app.cell
def _():
    import asyncio
    import selectors
    import socket
    import threading
    import time

    import marimo as mo

    from workshop.common import timed

    return asyncio, mo, selectors, socket, threading, time, timed


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Blocking sockets serve one client at a time

    *Listings 3.1–3.3.* A server has **one listening socket** (`accept()` hands out connections) plus **one socket per client**.
    With blocking calls, `recv()` stops the whole thread. While the server waits for the slow client (who sends after
    1 second), the fast client gets no answer, even though it already sent its data.
    """)
    return


@app.cell
def _(socket, threading, timed):
    def serve_one_at_a_time(server: socket.socket, clients: int):
        for _ in range(clients):
            connection, _ = server.accept()  # blocks until a client connects
            with connection:
                connection.sendall(connection.recv(1024))  # blocks until this client sends

    _server = socket.create_server(("127.0.0.1", 0))
    threading.Thread(target=serve_one_at_a_time, args=(_server, 2)).start()

    _slow = socket.create_connection(_server.getsockname())  # connects first, sends after 1 s
    _fast = socket.create_connection(_server.getsockname())
    threading.Timer(1, _slow.sendall, args=(b"slow",)).start()

    with timed("the fast client waited for its echo"):
        _fast.sendall(b"fast")
        _fast.recv(1024)

    _slow.close()
    _fast.close()
    _server.close()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Non-blocking sockets never wait

    *Listings 3.4, 3.5.* With `setblocking(False)`, `accept()` and `recv()` return right away. When nothing is
    ready they raise `BlockingIOError` instead of waiting.
    """)
    return


@app.cell
def _(socket):
    _server = socket.create_server(("127.0.0.1", 0))
    _server.setblocking(False)
    try:
        _server.accept()
    except BlockingIOError as _error:
        print("accept() returned immediately:", repr(_error))
    _server.close()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Busy polling burns a CPU core; a selector sleeps

    *Listings 3.6, 3.7.* One way to serve many sockets on one thread is to try every non-blocking socket in a loop and
    ignore `BlockingIOError`. It works, but it spins at 100% CPU even when nobody is talking.
    `selectors` (epoll / kqueue / IOCP) asks the **OS** which sockets are ready and sleeps until one is.

    Both wait 1 second for a client that never comes. Compare the CPU time each one used:
    """)
    return


@app.cell
def _(selectors, socket, time):
    _server = socket.create_server(("127.0.0.1", 0))
    _server.setblocking(False)

    def busy_poll(server: socket.socket, seconds: float):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            try:
                server.accept()
            except BlockingIOError:
                pass  # nobody there: try again immediately

    def wait_with_selector(server: socket.socket, seconds: float):
        selector = selectors.DefaultSelector()
        selector.register(server, selectors.EVENT_READ)
        selector.select(timeout=seconds)  # the OS wakes us when a client arrives

    _cpu = time.thread_time()
    busy_poll(_server, 1)
    print(f"busy polling: {time.thread_time() - _cpu:.2f} s of CPU")

    _cpu = time.thread_time()
    wait_with_selector(_server, 1)
    print(f"selector:     {time.thread_time() - _cpu:.2f} s of CPU")
    _server.close()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## A selector serves many clients from one thread

    Registering sockets and reacting to "ready" events in a loop **is** an event loop. Three clients connect and send;
    one thread echoes all of them:
    """)
    return


@app.cell
def _(selectors, socket):
    class SelectorEchoServer:
        def __init__(self):
            self.socket = socket.create_server(("127.0.0.1", 0))
            self.socket.setblocking(False)
            self.address = self.socket.getsockname()
            self.selector = selectors.DefaultSelector()
            self.selector.register(self.socket, selectors.EVENT_READ)

        def serve(self, messages: int):
            """The event loop: wait for ready sockets and react, until `messages` messages were echoed."""
            echoed = 0
            while echoed < messages:
                for key, _ in self.selector.select():
                    if key.fileobj is self.socket:  # a new client
                        self._accept()
                    else:  # a client sent data
                        self._echo(key.fileobj)
                        echoed += 1

        def _accept(self):
            connection, _ = self.socket.accept()
            self.selector.register(connection, selectors.EVENT_READ)

        def _echo(self, connection: socket.socket):
            connection.sendall(connection.recv(1024))

    _server = SelectorEchoServer()
    _clients = [socket.create_connection(_server.address) for _ in range(3)]
    for _i, _client in enumerate(_clients):
        _client.sendall(f"hi from {_i}".encode())

    _server.serve(messages=3)
    print([_client.recv(1024) for _client in _clients])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## The same server on asyncio

    *Listing 3.8.* `loop.sock_accept` / `sock_recv` / `sock_sendall` are coroutines built on a selector. With one task per
    client the code reads sequentially, but clients are served concurrently. An exception in one client's task
    (send `boom`) doesn't affect the others.
    """)
    return


@app.cell
async def _(asyncio, socket):
    class AsyncEchoServer:
        def __init__(self):
            self.socket = socket.create_server(("127.0.0.1", 0))
            self.socket.setblocking(False)
            self.address = self.socket.getsockname()

        async def serve(self):
            loop = asyncio.get_running_loop()
            while True:
                connection, _ = await loop.sock_accept(self.socket)
                connection.setblocking(False)
                asyncio.create_task(self._echo(connection))  # one task per client

        async def _echo(self, connection: socket.socket):
            loop = asyncio.get_running_loop()
            try:
                data = await loop.sock_recv(connection, 1024)
                if data == b"boom":
                    raise RuntimeError("unexpected network error")
                await loop.sock_sendall(connection, data)
            except RuntimeError as error:
                print("one echo task failed:", repr(error))
            finally:
                connection.close()

    async def client(address, message: bytes) -> bytes:
        reader, writer = await asyncio.open_connection(*address)
        writer.write(message)
        reply = await reader.read(1024)
        writer.close()
        return reply

    _server = AsyncEchoServer()
    _serving = asyncio.create_task(_server.serve())
    _address = _server.address
    print(await asyncio.gather(client(_address, b"one"), client(_address, b"boom"), client(_address, b"three")))
    _serving.cancel()
    _server.socket.close()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Graceful shutdown

    *Listings 3.9, 3.10.* On shutdown: stop accepting, give connected clients a deadline to finish, then close whatever is
    left. `asyncio.start_server` does the bookkeeping: `close()` stops accepting, `wait_closed()` waits for connected
    clients, and `close_clients()` (3.13+) closes the rest. In a script the trigger is a signal handler
    (`loop.add_signal_handler(signal.SIGTERM, ...)`). Here client A leaves after 0.5 s, and client B would stay forever.
    """)
    return


@app.cell
async def _(asyncio, timed):
    async def handle(reader, writer):
        await reader.read()  # until the client disconnects
        writer.close()

    _server = await asyncio.start_server(handle, "127.0.0.1", 0)
    _address = _server.sockets[0].getsockname()
    _, _client_a = await asyncio.open_connection(*_address)
    _, _client_b = await asyncio.open_connection(*_address)
    asyncio.get_running_loop().call_later(0.5, _client_a.close)

    with timed("shutdown"):
        _server.close()  # 1. stop accepting
        try:
            async with asyncio.timeout(2):  # 2. a deadline for connected clients
                await _server.wait_closed()
        except TimeoutError:
            print("client B still connected after 2 s: closing it")
            _server.close_clients()  # 3. close whatever is left
            await _server.wait_closed()
    _client_b.close()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Takeaways

    * Blocking I/O stalls the thread. Non-blocking I/O needs something that knows **when** to retry.
    * Polling wastes CPU. `selectors` let the OS wake you up when a socket is ready, and that's the core of every event loop.
    * asyncio wraps the selector in coroutines: one task per client, and errors stay isolated to that client.
    * Handle shutdown on purpose: stop accepting, drain within a deadline, then close.
    """)
    return


if __name__ == "__main__":
    app.run()
