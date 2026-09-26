"""A thread computing and a thread waiting, for the sampling profiler in notebook 17."""

import threading
import time

from workshop.cpu import fib


def crunch():
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        fib(25)


def wait():
    time.sleep(2)


if __name__ == "__main__":
    threads = [threading.Thread(target=crunch, name="cruncher"), threading.Thread(target=wait, name="waiter")]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
