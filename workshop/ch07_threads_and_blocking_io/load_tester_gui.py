"""Listing 7.14: the Tkinter UI for the load tester.

The asyncio thread must never touch Tk widgets (Tk is not thread-safe). It puts
progress into a thread-safe queue.Queue, and the GUI polls that queue with
self.after(), so every widget update happens on the GUI thread.
"""

from queue import Queue
from tkinter import Entry, Label, Tk, ttk

from workshop.ch07_threads_and_blocking_io.stress_test import StressTest


class LoadTester(Tk):
    def __init__(self, loop, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)
        self._queue = Queue()
        self._refresh_ms = 25

        self._loop = loop
        self._load_test: StressTest | None = None
        self.title("URL Requester")

        self._url_label = Label(self, text="URL:")
        self._url_label.grid(column=0, row=0)

        self._url_field = Entry(self, width=10)
        self._url_field.grid(column=1, row=0)

        self._request_label = Label(self, text="Number of requests:")
        self._request_label.grid(column=0, row=1)

        self._request_field = Entry(self, width=10)
        self._request_field.grid(column=1, row=1)

        self._submit = ttk.Button(self, text="Submit", command=self._start)
        self._submit.grid(column=2, row=1)

        self._pb_label = Label(self, text="Progress:")
        self._pb_label.grid(column=0, row=3)

        self._pb = ttk.Progressbar(self, orient="horizontal", length=200, mode="determinate")
        self._pb.grid(column=1, row=3, columnspan=2)

    def _update_bar(self, pct: int):
        if pct == 100:
            self._load_test = None
            self._submit["text"] = "Submit"
        else:
            self._pb["value"] = pct
            self.after(self._refresh_ms, self._poll_queue)

    def _queue_update(self, completed_requests: int, total_requests: int):
        # called from the asyncio thread
        self._queue.put(int(completed_requests / total_requests * 100))

    def _poll_queue(self):
        # called on the GUI thread
        if not self._queue.empty():
            percent_complete = self._queue.get()
            self._update_bar(percent_complete)
        elif self._load_test:
            self.after(self._refresh_ms, self._poll_queue)

    def _start(self):
        if self._load_test is None:
            self._submit["text"] = "Cancel"
            test = StressTest(
                self._loop,
                self._url_field.get(),
                int(self._request_field.get()),
                self._queue_update,
            )
            self.after(self._refresh_ms, self._poll_queue)
            test.start()
            self._load_test = test
        else:
            self._load_test.cancel()
            self._load_test = None
            self._submit["text"] = "Submit"
