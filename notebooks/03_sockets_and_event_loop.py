import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium", app_title="3 · Sockets and the event loop")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 3 · From blocking sockets to an event loop

    This notebook builds, step by step, the machinery that asyncio uses underneath:
    **blocking sockets → non-blocking sockets → a busy loop → `selectors` → asyncio**.
    Every server runs inside its demo cell, and the notebook plays the clients.
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

    from workshop.nb import Timeline

    return Timeline, asyncio, mo, selectors, socket, threading, time


@app.cell
def _(Timeline, socket, time):
    def make_server_socket(port: int, blocking: bool = True) -> socket.socket:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # IPv4 + TCP
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # allow quick restarts
        server.bind(("127.0.0.1", port))
        server.listen()
        server.setblocking(blocking)
        return server

    def blocking_client(port: int, message: bytes, timeline: Timeline, wait_before_send: float = 0) -> None:
        with socket.create_connection(("127.0.0.1", port)) as client:
            timeline.log("connected")
            time.sleep(wait_before_send)
            client.sendall(message + b"\n")
            timeline.log(f"sent {message!r}, waiting for echo")
            timeline.log(f"got echo {client.recv(1024)!r}")

    return blocking_client, make_server_socket


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Blocking sockets serve one client at a time

    *Listings 3.1–3.3.* A server has **one listening socket** (`accept()` hands out connections) plus **one socket per client**.
    With blocking calls, `recv()` stops the whole thread. While the server waits for client 1 (who thinks for
    1 second), client 2 gets no answer, even though it already sent its data.
    """)
    return


@app.cell
def _(Timeline, blocking_client, make_server_socket, socket, threading, time):
    def sequential_echo_server(server: socket.socket, clients: int, timeline: Timeline) -> None:
        for _ in range(clients):
            connection, address = server.accept()  # blocks until a client connects
            timeline.log(f"accepted {address[1]}")
            buffer = b""
            while not buffer.endswith(b"\n"):
                buffer += connection.recv(2)  # blocks until bytes arrive
            connection.sendall(buffer)
            connection.close()
        server.close()

    _timeline = Timeline()
    _server = make_server_socket(8301)
    _threads = [
        threading.Thread(target=sequential_echo_server, args=(_server, 2, _timeline), name="server"),
        threading.Thread(target=blocking_client, args=(8301, b"slow", _timeline, 1.0), name="client-1 (slow)"),
        threading.Thread(target=blocking_client, args=(8301, b"fast", _timeline), name="client-2 (fast)"),
    ]
    for _t in _threads:
        _t.start()
        time.sleep(0.05)
    for _t in _threads:
        _t.join()
    _timeline.show()
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
def _(make_server_socket):
    _server = make_server_socket(8302, blocking=False)
    try:
        _server.accept()
    except BlockingIOError as error:
        print(f"accept() returned immediately: {error!r}")
    finally:
        _server.close()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Busy polling burns a CPU core; a selector sleeps

    *Listings 3.6, 3.7.* One way to serve many clients on one thread is to call every non-blocking socket in a loop and
    ignore `BlockingIOError`. It works, but it spins at 100% CPU even when nobody is talking.
    `selectors` (epoll / kqueue / IOCP) asks the **OS** which sockets are ready and sleeps until one is.

    Each server below runs for 1 second **with no clients**. Compare the CPU time each one used.
    """)
    return


@app.cell
def _(make_server_socket, selectors, socket, threading, time):
    def busy_poll_server(server: socket.socket, stop: threading.Event, result: dict) -> None:
        connections = []
        while not stop.is_set():
            try:
                connection, _ = server.accept()
                connection.setblocking(False)
                connections.append(connection)
            except BlockingIOError:
                pass  # nobody connecting: try again immediately
            for connection in connections:
                try:
                    connection.send(connection.recv(1024))
                except BlockingIOError:
                    pass
        result["cpu"] = time.thread_time()

    def selector_server(server: socket.socket, stop: threading.Event, result: dict) -> None:
        selector = selectors.DefaultSelector()
        selector.register(server, selectors.EVENT_READ)
        while not stop.is_set():
            for key, _ in selector.select(timeout=0.1):  # sleeps until a socket is ready
                if key.fileobj is server:
                    connection, _ = server.accept()
                    connection.setblocking(False)
                    selector.register(connection, selectors.EVENT_READ)
                elif data := key.fileobj.recv(1024):
                    key.fileobj.send(data)
                else:  # empty read: the client disconnected
                    selector.unregister(key.fileobj)
                    key.fileobj.close()
        result["cpu"] = time.thread_time()

    def measure_idle_cpu(target, port: int) -> float:
        server, stop, result = make_server_socket(port, blocking=False), threading.Event(), {}
        thread = threading.Thread(target=target, args=(server, stop, result))
        thread.start()
        time.sleep(1)
        stop.set()
        thread.join()
        server.close()
        return result["cpu"]

    print(f"CPU used in 1 s of idling, busy polling: {measure_idle_cpu(busy_poll_server, 8303):.2f} s")
    print(f"CPU used in 1 s of idling, selector:     {measure_idle_cpu(selector_server, 8304):.3f} s")
    return (selector_server,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    A selector serves many clients at once from one thread. Registering sockets and reacting to "ready" events in a
    loop **is** an event loop:
    """)
    return


@app.cell
def _(
    Timeline,
    blocking_client,
    make_server_socket,
    selector_server,
    threading,
):
    _timeline = Timeline()
    _server, _stop, _result = make_server_socket(8305, blocking=False), threading.Event(), {}
    _server_thread = threading.Thread(target=selector_server, args=(_server, _stop, _result), name="selector-server")
    _server_thread.start()
    _clients = [
        threading.Thread(
            target=blocking_client, args=(8305, f"hi from {i}".encode(), _timeline, 0.5), name=f"client-{i}"
        )
        for i in range(3)
    ]
    for _t in _clients:
        _t.start()
    for _t in _clients:
        _t.join()
    _stop.set()
    _server_thread.join()
    _server.close()
    _timeline.show()
    print("All three clients were served in ~0.5 s by ONE thread")
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
async def _(asyncio, make_server_socket, socket):
    async def echo(connection: socket.socket) -> None:
        loop = asyncio.get_running_loop()
        try:
            while data := await loop.sock_recv(connection, 1024):
                if data.strip() == b"boom":
                    raise Exception("Unexpected network error")
                await loop.sock_sendall(connection, data)
        except Exception as error:
            print(f"echo task failed: {error!r} (the other clients are fine)")
        finally:
            connection.close()

    async def listen_for_connections(server: socket.socket, echo_tasks: list) -> None:
        loop = asyncio.get_running_loop()
        while True:
            connection, _ = await loop.sock_accept(server)
            connection.setblocking(False)
            echo_tasks.append(asyncio.create_task(echo(connection)))

    async def async_client(port: int, message: bytes) -> bytes:
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write(message + b"\n")
        await writer.drain()
        reply = await reader.read(1024)
        writer.close()
        return reply

    _server = make_server_socket(8306, blocking=False)
    _echo_tasks = []
    _listener = asyncio.create_task(listen_for_connections(_server, _echo_tasks))
    print(await asyncio.gather(*(async_client(8306, m) for m in [b"one", b"boom", b"three"])))
    _listener.cancel()
    _server.close()
    return (listen_for_connections,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Graceful shutdown

    *Listings 3.9, 3.10.* On shutdown: stop accepting, give connected clients a deadline to finish, then close whatever is
    left. In a script the trigger is a signal handler (`loop.add_signal_handler(signal.SIGTERM, ...)` on Unix, or
    `signal.signal` on Windows). Here we trigger it by hand. Client A finishes within the deadline, and client B
    keeps its connection open and is closed after 2 s.
    """)
    return


@app.cell
async def _(asyncio, listen_for_connections, make_server_socket, time):
    async def idle_client(port: int, name: str, stay_connected: float) -> None:
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write(f"hello from {name}\n".encode())
        await asyncio.sleep(stay_connected)
        writer.close()

    async def close_echo_tasks(tasks: list, timeout: float) -> None:
        for task in tasks:
            try:
                await asyncio.wait_for(task, timeout)  # wait_for cancels the task on timeout
            except TimeoutError:
                print("client still connected after the deadline, closed it")

    _server = make_server_socket(8307, blocking=False)
    _echo_tasks = []
    _listener = asyncio.create_task(listen_for_connections(_server, _echo_tasks))
    _clients = [asyncio.create_task(idle_client(8307, "A", 0.5)), asyncio.create_task(idle_client(8307, "B", 10))]
    await asyncio.sleep(0.2)

    _start = time.perf_counter()
    print(f"shutting down with {len(_echo_tasks)} connected client(s)")
    _listener.cancel()  # 1. stop accepting
    _server.close()
    await close_echo_tasks(_echo_tasks, timeout=2)  # 2. deadline for the connected clients
    print(f"shutdown finished in {time.perf_counter() - _start:.1f} s")
    for _c in _clients:
        _c.cancel()
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
