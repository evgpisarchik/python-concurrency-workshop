"""Listing 1.3: starting a second thread.

Use case: run a function in the background while the main thread keeps going.
start() launches the thread, join() blocks until it finishes.

Run: uv run python -m workshop.ch01_concurrency_basics.03_multithreading
"""

import threading


def hello_from_thread():
    print(f"Hello from thread {threading.current_thread()}!")


hello_thread = threading.Thread(target=hello_from_thread)
hello_thread.start()

total_threads = threading.active_count()
thread_name = threading.current_thread().name

print(f"Python is currently running {total_threads} thread(s)")
print(f"The current thread is {thread_name}")

hello_thread.join()  # wait for the worker thread to finish
print(f"After join() only {threading.active_count()} thread is left")
