"""Listing 1.2: every Python program is one process with at least one thread.

Use case: inspect which process / thread your code runs on (useful when debugging
web servers that use worker processes or thread pools).

    * A process has its own memory space; processes do not share objects.
    * Threads live inside a process and share its memory.

Run: uv run python -m workshop.ch01_concurrency_basics.02_processes_and_threads
"""

import os
import threading

print(f"Python process running with process id: {os.getpid()}")

total_threads = threading.active_count()
thread_name = threading.current_thread().name

print(f"Python is currently running {total_threads} thread(s)")
print(f"The current thread is {thread_name}")
