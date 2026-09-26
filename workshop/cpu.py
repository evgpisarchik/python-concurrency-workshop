"""CPU-bound functions used with threads and process pools.

They live in a module (not in a notebook cell) because process pools pickle a
function by its module and name, and the child process must be able to import it.
"""

import hashlib
import os
import time


def fib(n: int) -> int:
    """Deliberately slow recursive Fibonacci."""
    if n <= 2:
        return n - 1
    return fib(n - 1) + fib(n - 2)


def count(count_to: int) -> int:
    counter = 0
    while counter < count_to:
        counter = counter + 1
    return counter


def timed_count(count_to: int) -> tuple[int, int, float]:
    """Count and report (pid, count_to, seconds), so the parent can show what each process did."""
    start = time.perf_counter()
    count(count_to)
    return os.getpid(), count_to, time.perf_counter() - start


def say_hello(name: str) -> str:
    return f"Hi there, {name} (from pid {os.getpid()})"


def hash_password(password: bytes) -> bytes:
    """scrypt is CPU-heavy, but hashlib releases the GIL while it runs."""
    return hashlib.scrypt(password, salt=os.urandom(16), n=2048, p=1, r=8)
