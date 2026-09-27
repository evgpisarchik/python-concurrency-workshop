"""Benchmark for notebook 15. The notebook runs it on each Python build: `python -m workshop.freethreading`."""

import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from workshop.cpu import fib


def fib_in_threads(threads: int) -> float:
    """Run 4 × fib(30) on `threads` threads and return the seconds taken."""
    start = time.perf_counter()
    with ThreadPoolExecutor(threads) as pool:
        list(pool.map(fib, [30] * 4))
    return time.perf_counter() - start


class Counter:
    def __init__(self):
        self.value = 0

    def increment(self):
        self.value += 1  # read, add, write: another thread can write in between


def lost_updates(counter: Counter) -> int:
    """4 threads call `counter.increment()` 200,000 times each. Returns how many increments got lost."""

    def work():
        for _ in range(200_000):
            counter.increment()

    threads = [threading.Thread(target=work) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return 800_000 - counter.value


if __name__ == "__main__":
    print(f"GIL enabled: {sys._is_gil_enabled()}")
    print(f"1 thread:  {fib_in_threads(1):.2f} s")
    print(f"4 threads: {fib_in_threads(4):.2f} s")
    print(f"lost updates: {lost_updates(Counter()):,} of 800,000")
