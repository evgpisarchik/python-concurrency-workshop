"""Listing 1.4: starting a child process.

Use case: run code in a separate interpreter with its own GIL, which gives true
parallelism for CPU-bound work. The `if __name__ == "__main__"` guard is
required: child processes re-import this module and must not start processes
themselves.

Run: uv run python -m workshop.ch01_concurrency_basics.04_multiprocessing
"""

import multiprocessing
import os


def hello_from_process():
    print(f"Hello from child process {os.getpid()}!")


if __name__ == "__main__":
    hello_process = multiprocessing.Process(target=hello_from_process)
    hello_process.start()

    print(f"Hello from parent process {os.getpid()}")

    hello_process.join()
