"""Listing 7.15: run asyncio in a background thread next to a GUI.

Use case: combine asyncio with a framework that owns the main thread
(Tkinter, Qt, a game loop, a sync web framework). Run the asyncio loop forever
in a daemon thread and send work to it with run_coroutine_threadsafe.

Run: uv run python -m workshop.ch07_threads_and_blocking_io.13_load_tester_app   (needs a display)
     enter e.g.  https://www.example.com  and  200
"""

import asyncio
from asyncio import AbstractEventLoop
from threading import Thread

from workshop.ch07_threads_and_blocking_io.load_tester_gui import LoadTester


class ThreadedEventLoop(Thread):
    def __init__(self, loop: AbstractEventLoop):
        super().__init__(daemon=True)
        self._loop = loop

    def run(self):
        self._loop.run_forever()


loop = asyncio.new_event_loop()

asyncio_thread = ThreadedEventLoop(loop)
asyncio_thread.start()

app = LoadTester(loop)
app.mainloop()
