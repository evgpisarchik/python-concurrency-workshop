"""Listing 1.8: I/O-bound work in threads. This IS faster.

Use case: blocking I/O (the socket calls inside `requests`) releases the GIL
while it waits, so other threads can run. Two requests take about as long as one.

Run: uv run python -m workshop.ch01_concurrency_basics.08_io_bound_with_threads
"""

import threading
import time

import requests


def read_example() -> None:
    response = requests.get("https://www.example.com")
    print(response.status_code)


thread_1 = threading.Thread(target=read_example)
thread_2 = threading.Thread(target=read_example)

start = time.perf_counter()

thread_1.start()
thread_2.start()

print("All threads running!")

thread_1.join()
thread_2.join()

print(f"Running with threads took {time.perf_counter() - start:.4f} seconds.")
