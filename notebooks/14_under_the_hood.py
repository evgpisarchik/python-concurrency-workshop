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
    import inspect
    import selectors
    import socket
    import threading
    import time

    import marimo as mo
    import uvloop

    return (
        asyncio,
        contextvars,
        inspect,
        mo,
        selectors,
        socket,
        threading,
        time,
        uvloop,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Accepting both sync and async callables

    *Listing 14.1.* Libraries often let users register hooks that may be plain functions or coroutine functions.
    Detect which one you got and run it the right way.
    """)
    return


@app.cell
async def _(inspect):
    async def run_hook(hook):
        if inspect.iscoroutinefunction(hook):
            await hook()
        else:
            hook()

    async def async_hook():
        print("async hook ran")

    await run_hook(async_hook)
    await run_hook(lambda: print("sync hook ran"))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## contextvars: per-task "globals"

    *Listing 14.2.* A `ContextVar` holds request-scoped data (request id, user, trace id) that any function can read
    **without passing it as an argument**. Each task gets its own **copy** of the context, so concurrent requests don't
    overwrite each other. It's the async-safe replacement for `threading.local`.
    """)
    return


@app.cell
async def _(asyncio, contextvars):
    request_id = contextvars.ContextVar("request_id")

    async def handle_request(rid: str):
        request_id.set(rid)
        await asyncio.sleep(0.1)  # the other request sets its own id meanwhile
        print("finished request", request_id.get())

    await asyncio.gather(handle_request("A"), handle_request("B"))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## `await asyncio.sleep(0)` yields to the loop

    *Listing 14.3.* A new task doesn't start until the current code gives the loop a turn. `sleep(0)` suspends for exactly
    one loop iteration, which is enough.
    """)
    return


@app.cell
async def _(asyncio):
    async def child():
        print("child task runs")

    asyncio.create_task(child())
    print("task created")
    await asyncio.sleep(0)
    print("after sleep(0)")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## uvloop: a faster event loop

    *Listing 14.4.* uvloop reimplements the event loop on libuv (the loop behind Node.js). It's a drop-in change:
    `uvloop.run(main())` instead of `asyncio.run(main())`. The runs go in a background thread, because marimo's own loop is
    already running in this one.
    """)
    return


@app.cell
def _(asyncio, threading, time, uvloop):
    async def many_tasks():
        await asyncio.gather(*(asyncio.sleep(0.01) for _ in range(100_000)))

    def seconds(run) -> float:
        start = time.perf_counter()
        thread = threading.Thread(target=run, args=(many_tasks(),))
        thread.start()
        thread.join()
        return time.perf_counter() - start

    print(f"asyncio: {seconds(asyncio.run):.2f} s")
    print(f"uvloop:  {seconds(uvloop.run):.2f} s")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Coroutines are generators underneath

    *Listings 14.5–14.7.* A generator pauses at `yield`. Resuming several generators in turn **is** concurrency on one
    thread. A coroutine works the same way: `send(None)` runs it to its next suspension, and it finishes by raising
    `StopIteration`, just like a generator.
    """)
    return


@app.cell
def _():
    def counter(name: str):
        for i in range(3):
            yield f"{name}{i}"

    print(list(zip(counter("A"), counter("B"), strict=True)))  # A and B take turns

    async def greet():
        return "hello"

    try:
        greet().send(None)  # drive a coroutine by hand, with no event loop
    except StopIteration as _e:
        print("the coroutine returned", repr(_e.value))
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
            self.done = False
            self.result = None
            self.callback = None

        def set_result(self, result):
            self.result, self.done = result, True
            if self.callback:
                self.callback()

        def __await__(self):
            if not self.done:
                yield self  # suspend: hand ourselves to the driver
            return self.result

    _future = CustomFuture()
    _awaiting = _future.__await__()
    print("not done, so awaiting yields the future:", next(_awaiting) is _future)
    _future.set_result("Finished!")
    try:
        next(_awaiting)
    except StopIteration as _e:
        print("done, so the await returns", repr(_e.value))
    return (CustomFuture,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Resume a coroutine when a socket is ready

    *Listing 14.10.* Connect the future to OS I/O: register a selector callback that resolves the future, and resume the
    coroutine when the selector fires. `socket.socketpair()` gives two connected sockets, so no server is needed.
    """)
    return


@app.cell
def _(CustomFuture, selectors, socket):
    _selector = selectors.DefaultSelector()
    _reader, _writer = socket.socketpair()

    async def read_when_ready(sock):
        future = CustomFuture()
        _selector.register(sock, selectors.EVENT_READ, lambda: future.set_result(sock.recv(100)))
        return await future

    _coro = read_when_ready(_reader)
    _coro.send(None)  # runs until the coroutine awaits the future
    _writer.send(b"hello")
    for _key, _ in _selector.select():  # waits until the OS says a socket is ready
        _key.data()  # the callback resolves the future
    try:
        _coro.send(None)  # resume the coroutine
    except StopIteration as _e:
        print("the coroutine returned", _e.value)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Build a Task and an event loop

    *Listings 14.11–14.13.* A **Task** is a Future that drives a coroutine: when the coroutine yields a future, the task
    resumes it once that future is done. The **event loop** runs ready tasks, waits on the selector and fires the
    callbacks, over and over. Same design as asyncio, in about 30 lines.
    """)
    return


@app.cell
def _(CustomFuture, selectors):
    class CustomTask(CustomFuture):
        def __init__(self, coro, loop):
            super().__init__()
            self.coro = coro
            loop.ready.append(self)

        def step(self):
            try:
                future = self.coro.send(None)  # run to the next await
                future.callback = self.step  # continue when that future is done
            except StopIteration as e:
                self.set_result(e.value)

    class EventLoop:
        def __init__(self):
            self.selector = selectors.DefaultSelector()
            self.ready = []

        async def sock_recv(self, sock):
            future = CustomFuture()
            self.selector.register(sock, selectors.EVENT_READ, lambda: future.set_result(sock.recv(1024)))
            data = await future
            self.selector.unregister(sock)
            return data

        def run(self, coro):
            main = CustomTask(coro, self)
            while not main.done:
                while self.ready:
                    self.ready.pop(0).step()
                if not main.done:
                    for key, _ in self.selector.select():
                        key.data()
            return main.result

    return CustomTask, EventLoop


@app.cell
def _(CustomTask, EventLoop, socket):
    _loop = EventLoop()

    async def read(sock):
        data = await _loop.sock_recv(sock)
        print("got", data)
        return data

    async def main():
        reader1, writer1 = socket.socketpair()
        reader2, writer2 = socket.socketpair()
        task1 = CustomTask(read(reader1), _loop)  # both tasks wait at the same time
        task2 = CustomTask(read(reader2), _loop)
        writer1.send(b"first socket")
        writer2.send(b"second socket")
        return await task1, await task2

    print("main returned", _loop.run(main()))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Modern: eager tasks (3.12+)

    With `asyncio.eager_task_factory`, a new task runs **synchronously inside `create_task()`** up to its first real
    suspension. Tasks that finish without ever suspending (cache hits, memoized results) skip the scheduling round-trip.
    """)
    return


@app.cell
async def _(asyncio):
    async def cache_hit():
        return 1  # completes without suspending

    _task = asyncio.create_task(cache_hit())
    print("default: done right after create_task()?", _task.done())
    await _task

    asyncio.get_running_loop().set_task_factory(asyncio.eager_task_factory)
    _task = asyncio.create_task(cache_hit())
    print("eager:   done right after create_task()?", _task.done())
    asyncio.get_running_loop().set_task_factory(None)
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
