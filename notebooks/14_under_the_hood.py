import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium", app_title="14 · Under the hood")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 14 · Under the hood: contextvars, uvloop, and building an event loop
    """)
    return


@app.cell
def _():
    import asyncio
    import contextvars
    import functools
    import inspect
    import selectors
    import socket
    import threading
    import time
    import types

    import marimo as mo
    import uvloop

    from workshop.common import delay
    from workshop.nb import Timeline

    return (
        Timeline,
        asyncio,
        contextvars,
        delay,
        functools,
        inspect,
        mo,
        selectors,
        socket,
        threading,
        time,
        types,
        uvloop,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Accepting both sync and async callables

    *Listing 14.1.* Libraries often let users register hooks that may be plain functions, coroutine functions or coroutine
    objects. Detect which one you got and run it the right way.
    """)
    return


@app.cell
async def _(asyncio, inspect):
    async def run_all(callables: list) -> None:
        awaitables = []
        for item in callables:
            if inspect.iscoroutinefunction(item):  # async def function: call it, then schedule it
                awaitables.append(asyncio.create_task(item()))
            elif inspect.iscoroutine(item):  # already a coroutine object: schedule it
                awaitables.append(asyncio.create_task(item))
            else:  # plain function: run it as a loop callback
                asyncio.get_running_loop().call_soon(item)
        await asyncio.gather(*awaitables)

    async def async_hook():
        await asyncio.sleep(0.5)
        print("async hook finished")

    await run_all([async_hook, async_hook(), lambda: print("sync hook ran")])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## contextvars: per-task "globals"

    *Listing 14.2.* A `ContextVar` holds request-scoped data (request id, user, trace id) that any function in the call chain
    can read **without passing it as an argument**. Each task gets a **copy** of the context at the moment it's created, so
    concurrent requests don't overwrite each other. It's the async-safe replacement for `threading.local`.
    """)
    return


@app.cell
async def _(asyncio, contextvars):
    request_id: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")

    def log(message: str):
        print(f"[request {request_id.get()}] {message}")  # no request id parameter anywhere

    async def query_database():
        await asyncio.sleep(0.1)
        log("query finished")

    async def handle_request(rid: str):
        request_id.set(rid)
        log("handling")
        await query_database()
        log("done")

    await asyncio.gather(*(handle_request(r) for r in ("A", "B", "C")))
    log("outside any request: still the default")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## `await asyncio.sleep(0)` yields to the loop

    *Listing 14.3.* `sleep(0)` suspends for exactly one loop iteration. New tasks get to start right away, and a long
    loop can yield so that other tasks get a turn (cooperative multitasking).
    """)
    return


@app.cell
async def _(asyncio, delay):
    print("--- without sleep(0): the tasks start only when we reach gather")
    _t1 = asyncio.create_task(delay(0.1))
    _t2 = asyncio.create_task(delay(0.2))
    print("about to gather")
    await asyncio.gather(_t1, _t2)

    print("--- with sleep(0): each task starts immediately")
    _t1 = asyncio.create_task(delay(0.1))
    await asyncio.sleep(0)
    _t2 = asyncio.create_task(delay(0.2))
    await asyncio.sleep(0)
    print("about to gather")
    await asyncio.gather(_t1, _t2)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## uvloop: a faster event loop

    *Listing 14.4.* uvloop reimplements the event loop on libuv (the loop behind Node.js). It's a drop-in change:
    `uvloop.run(main())` instead of `asyncio.run(main())`, and uvicorn uses it automatically when it's installed. Below, the same
    TCP echo workload (100 clients × 300 round-trips) runs on each loop in a background thread, since marimo's own loop is already running.
    """)
    return


@app.cell
def _(asyncio, mo, threading, time, uvloop):
    async def echo_workload(clients: int = 100, messages: int = 300) -> float:
        async def handle(reader, writer):
            while line := await reader.readline():
                writer.write(line)
                await writer.drain()
            writer.close()

        server = await asyncio.start_server(handle, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]

        async def client():
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            for _ in range(messages):
                writer.write(b"ping\n")
                await writer.drain()
                await reader.readline()
            writer.close()

        start = time.perf_counter()
        await asyncio.gather(*(client() for _ in range(clients)))
        elapsed = time.perf_counter() - start
        server.close()
        return elapsed

    def run_in_thread(runner) -> float:
        result = {}
        thread = threading.Thread(target=lambda: result.update(t=runner(echo_workload())))
        thread.start()
        thread.join()
        return result["t"]

    _asyncio_time = run_in_thread(asyncio.run)
    _uvloop_time = run_in_thread(uvloop.run)
    mo.md(f"""
    | 30,000 echo round-trips | seconds |
    |---|---|
    | asyncio (default loop) | {_asyncio_time:.2f} |
    | uvloop | {_uvloop_time:.2f} |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Coroutines are generators underneath

    *Listings 14.5–14.7.* Before `async`/`await`, coroutines were generators that used `yield from`
    (`@asyncio.coroutine` was removed in Python 3.11; `@types.coroutine` is its low-level successor). A generator pauses at
    `yield`, and a loop that resumes several generators in turn **is** concurrency on one thread:
    """)
    return


@app.cell
async def _(asyncio, types):
    def counter(name: str, start: int, end: int):
        for i in range(start, end):
            yield f"{name}: {i}"

    _generators = [counter("A", 1, 4), counter("B", 10, 13)]
    while _generators:  # a round-robin "scheduler"
        for _gen in list(_generators):
            try:
                print(next(_gen))
            except StopIteration:
                _generators.remove(_gen)

    async def say_hello():
        print("Hello!")

    async def meet_and_greet():
        await say_hello()
        print("Goodbye!")

    _coro = meet_and_greet()
    try:
        _coro.send(None)  # drive a coroutine by hand, with no event loop
    except StopIteration:
        print("the coroutine finished: it raised StopIteration, just like a generator")

    @types.coroutine
    def legacy_style():
        yield from asyncio.sleep(0.1).__await__()  # the pre-async/await way
        return "legacy coroutine done"

    print(await legacy_style())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Build a Future

    *Listings 14.8, 14.9.* `__await__` **yields the future itself** while it isn't done, and that's how a coroutine
    suspends. Whoever drives the coroutine gets the future back and knows what it's waiting for.
    """)
    return


@app.cell
def _():
    class CustomFuture:
        def __init__(self):
            self._result = None
            self._is_finished = False
            self._done_callback = None

        def result(self):
            return self._result

        def is_finished(self):
            return self._is_finished

        def set_result(self, result):
            self._result = result
            self._is_finished = True
            if self._done_callback:
                self._done_callback(result)

        def add_done_callback(self, fn):
            self._done_callback = fn

        def __await__(self):
            if not self._is_finished:
                yield self  # suspend: hand ourselves to the driver
            return self.result()

    _future = CustomFuture()
    for _step in range(3):
        try:
            _future.__await__().send(None)
            print(f"step {_step}: the future isn't done, so awaiting it yields")
            if _step == 1:
                _future.set_result("Finished!")
        except StopIteration as si:
            print(f"step {_step}: done, and the await returned {si.value!r}")
    return (CustomFuture,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Resume a coroutine when a socket is ready

    *Listing 14.10.* Connect the future to OS I/O: register a selector callback that resolves the future, and resume the
    coroutine when the selector fires. It runs in a background thread so this notebook can act as the client.
    """)
    return


@app.cell
def _(CustomFuture, Timeline, selectors, socket, threading, time):
    def selector_driven_accept(port: int, timeline: Timeline):
        selector = selectors.DefaultSelector()

        async def sock_accept(sock):
            future = CustomFuture()
            selector.register(sock, selectors.EVENT_READ, lambda s: future.set_result(s.accept()))
            timeline.log("coroutine suspended until the socket is readable")
            connection, address = await future
            return address

        async def main():
            server = socket.create_server(("127.0.0.1", port))
            server.setblocking(False)
            address = await sock_accept(server)
            timeline.log(f"coroutine resumed: connection from port {address[1]}")
            server.close()

        coro = main()
        try:
            while True:
                coro.send(None)  # run until the coroutine yields a future
                for key, _ in selector.select():  # sleep until the OS says a socket is ready
                    timeline.log("selector event: firing callback")
                    key.data(key.fileobj)  # resolves the future
        except StopIteration:
            timeline.log("coroutine finished")

    _timeline = Timeline()
    _thread = threading.Thread(target=selector_driven_accept, args=(8141, _timeline), name="mini-loop")
    _thread.start()
    time.sleep(0.2)
    socket.create_connection(("127.0.0.1", 8141)).close()
    _thread.join()
    _timeline.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Build a Task and an event loop, then run a server on them

    *Listings 14.11–14.13.* A **Task** is a Future that drives a coroutine: when the coroutine yields a future, the task
    subscribes to it and resumes the coroutine with the result. The **event loop** drives the main coroutine, steps the
    tasks, waits on the selector and fires the callbacks, over and over. It's about 60 lines, with the same design as asyncio.
    """)
    return


@app.cell
def _(CustomFuture, functools, selectors):
    class CustomTask(CustomFuture):
        def __init__(self, coro, loop):
            super().__init__()
            self._coro, self._loop, self._task_state = coro, loop, None
            loop.register_task(self)

        def step(self):
            try:
                if self._task_state is None:
                    self._task_state = self._coro.send(None)
                if isinstance(self._task_state, CustomFuture):
                    self._task_state.add_done_callback(self._future_done)
            except StopIteration as si:
                self.set_result(si.value)

        def _future_done(self, result):
            try:
                self._task_state = self._coro.send(result)
                if isinstance(self._task_state, CustomFuture):
                    self._task_state.add_done_callback(self._future_done)
            except StopIteration as si:
                self.set_result(si.value)

    class EventLoop:
        def __init__(self):
            self.selector = selectors.DefaultSelector()
            self._tasks_to_run = []

        def _register_socket_to_read(self, sock, callback):
            future = CustomFuture()
            handler = functools.partial(callback, future)
            try:
                self.selector.get_key(sock)
                self.selector.modify(sock, selectors.EVENT_READ, handler)
            except KeyError:
                sock.setblocking(False)
                self.selector.register(sock, selectors.EVENT_READ, handler)
            return future

        async def sock_recv(self, sock):
            return await self._register_socket_to_read(sock, lambda future, s: future.set_result(s.recv(1024)))

        async def sock_accept(self, sock):
            return await self._register_socket_to_read(sock, lambda future, s: future.set_result(s.accept()))

        def sock_close(self, sock):
            self.selector.unregister(sock)
            sock.close()

        def register_task(self, task):
            self._tasks_to_run.append(task)

        def run(self, coro):
            main = CustomTask(coro, self)
            while True:
                for task in self._tasks_to_run:
                    task.step()
                self._tasks_to_run = [t for t in self._tasks_to_run if not t.is_finished()]
                if main.is_finished() and not self._tasks_to_run:
                    return main.result()
                for key, _ in self.selector.select():
                    key.data(key.fileobj)

    return CustomTask, EventLoop


@app.cell
def _(CustomTask, EventLoop, Timeline, socket, threading, time):
    def custom_loop_server(port: int, clients: int, timeline: Timeline):
        async def read_from_client(conn, loop: EventLoop):
            try:
                while data := await loop.sock_recv(conn):
                    timeline.log(f"got {data!r}")
            finally:
                loop.sock_close(conn)

        async def main(loop: EventLoop):
            server = socket.create_server(("127.0.0.1", port))
            for _ in range(clients):
                conn, address = await loop.sock_accept(server)
                timeline.log(f"accepted client {address[1]}, spawning a task")
                CustomTask(read_from_client(conn, loop), loop)
            loop.sock_close(server)

        loop = EventLoop()
        loop.run(main(loop))
        timeline.log("all client tasks finished: event loop exits")

    _timeline = Timeline()
    _thread = threading.Thread(target=custom_loop_server, args=(8142, 3, _timeline), name="custom-event-loop")
    _thread.start()
    time.sleep(0.2)
    _clients = [socket.create_connection(("127.0.0.1", 8142)) for _ in range(3)]
    for _round in range(2):
        for _i, _c in enumerate(_clients):
            _c.sendall(f"client {_i}, message {_round}".encode())
            time.sleep(0.05)
    for _c in _clients:
        _c.close()
    _thread.join(timeout=5)
    _timeline.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Modern: eager tasks (3.12+)

    With `asyncio.eager_task_factory`, a new task runs **synchronously inside `create_task()`** up to its first real suspension.
    Tasks that finish without ever suspending (cache hits, memoized results) skip the scheduling round-trip entirely.
    """)
    return


@app.cell
async def _(asyncio):
    _CACHE = {"a": 1}

    async def cached_lookup(key: str) -> int:
        if key in _CACHE:
            return _CACHE[key]  # completes without suspending
        await asyncio.sleep(0.1)
        return 0

    _loop = asyncio.get_running_loop()
    _previous = _loop.get_task_factory()
    for _name, _factory in [("default", None), ("eager", asyncio.eager_task_factory)]:
        _loop.set_task_factory(_factory)
        _task = asyncio.create_task(cached_lookup("a"))
        print(f"{_name:>7} task factory: done right after create_task()? {_task.done()}")
        await _task
    _loop.set_task_factory(_previous)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Takeaways

    * A coroutine is a generator underneath. `await` passes futures **up** to whoever is driving the coroutine.
    * An event loop does four things: run ready tasks, `select()` on sockets, fire callbacks that resolve futures, repeat.
    * `contextvars` carry per-request state across awaits. uvloop is a drop-in speedup.
    """)
    return


if __name__ == "__main__":
    app.run()
