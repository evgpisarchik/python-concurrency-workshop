"""Listing 3.9: handle SIGINT (Ctrl+C) inside the event loop.

Use case: react to OS signals (Ctrl+C, `kill`, Docker/Kubernetes stop) by
cancelling running tasks. loop.add_signal_handler works on Unix only. On
Windows, use signal.signal().

Run: uv run python -m workshop.ch03_sockets_and_event_loop.09_signal_handler   then press Ctrl+C
"""

import asyncio
import signal

from workshop.common import delay


def cancel_tasks():
    print("Got a SIGINT!")
    tasks: set[asyncio.Task] = asyncio.all_tasks()
    print(f"Cancelling {len(tasks)} task(s).")
    for task in tasks:
        task.cancel()


async def main():
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, cancel_tasks)
    try:
        await delay(10)
    except asyncio.CancelledError:
        print("main() was cancelled, exiting cleanly")


asyncio.run(main())
