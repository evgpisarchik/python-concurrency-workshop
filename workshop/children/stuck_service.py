"""An asyncio "service" that looks hung: every request waits on a backend that never answers.

Notebook 17 inspects it from outside with `python -m asyncio pstree <pid>` and `sys.remote_exec()`.
It exits by itself after 2 minutes, so a forgotten demo doesn't keep running.
"""

import asyncio

stats = {"handled": 0}  # remote_exec() scripts can read this: they run inside this process


async def query_backend():
    await asyncio.sleep(3600)  # the backend never answers


async def handle_request():
    await query_backend()  # no timeout: the request hangs forever
    stats["handled"] += 1


async def heartbeat():
    # Keeps the loop waking up. sys.remote_exec() scripts run only when the process executes Python code.
    while True:
        await asyncio.sleep(0.2)


async def serve():
    async with asyncio.TaskGroup() as tg:
        tg.create_task(heartbeat(), name="heartbeat")
        tg.create_task(handle_request(), name="request-1")
        tg.create_task(handle_request(), name="request-2")


async def main():
    print("ready", flush=True)
    async with asyncio.timeout(120):
        await serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except TimeoutError:
        pass
