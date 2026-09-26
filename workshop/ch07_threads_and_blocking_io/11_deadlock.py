"""Listing 7.11: a classic deadlock (two locks taken in opposite order).

Use case: learn to spot deadlocks. Thread 1 holds A and waits for B, while
thread 2 holds B and waits for A. Neither can continue. The fix is to always
acquire locks in the same global order.

Run: uv run python -m workshop.ch07_threads_and_blocking_io.11_deadlock   (it detects the hang after 3 s)
"""

import time
from threading import Lock, Thread

lock_a = Lock()
lock_b = Lock()


def a():
    with lock_a:
        print("Acquired lock a from method a!")
        time.sleep(1)  # gives thread b time to grab lock_b
        with lock_b:
            print("Acquired both locks from method a!")


def b():
    with lock_b:
        print("Acquired lock b from method b!")
        with lock_a:
            print("Acquired both locks from method b!")


thread_1 = Thread(target=a, daemon=True)
thread_2 = Thread(target=b, daemon=True)
thread_1.start()
thread_2.start()
thread_1.join(timeout=3)
thread_2.join(timeout=3)
if thread_1.is_alive() and thread_2.is_alive():
    print("Deadlock: both threads are waiting on each other forever.")
